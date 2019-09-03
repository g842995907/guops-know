# -*- coding: utf-8 -*-
from rest_framework import filters, viewsets
from rest_framework.decorators import detail_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common_framework.utils.constant import Status
from common_framework.utils.rest import mixins as common_mixins
from practice import api as practice_api
from practice_capability import models as capability_modules
from practice_capability.models import TestPaperTask, TestPaper, TestPaperRecord
from practice_capability.web import serializers

import json
import collections


class Serializer:
    def __init__(self, raw, tpt):
        self.data = {
            'title': raw.title,
            'id': str(raw.id),
            'hash': str(raw.hash),
            'score': int(tpt.score),
            'content': raw.content
        }

        p_type = int(raw.hash.split('.')[-1])
        if p_type == 0:
            self.data['options'] = raw.option
            self.data['options_dsc'] = self.data['options_dsc'] = collections.OrderedDict(sorted(json.loads(raw.option).items(), key=lambda t: t[0]))
            self.data['is_choice_question'] = 1
            self.data['is_multiple_choice'] = 1 if raw.multiple else 0
        else:
            if raw.file and raw.file.url:
                file_attach = {
                    'name': raw.file.name,
                    'url': raw.file.url,
                }

                self.data['file_url'] = file_attach
            self.data['url'] = raw.url
            self.data['is_dynamic_env'] = raw.is_dynamic_env


class TestPaperViewSet(common_mixins.CacheModelMixin,
                       viewsets.ReadOnlyModelViewSet,
                       ):
    queryset = capability_modules.TestPaper.objects.filter(status=Status.NORMAL, public=True)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.TestPaperSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    ordering_fields = ('create_time',)
    ordering = ('-create_time',)
    search_fields = ('name')

    @detail_route(methods=['get'], )
    def testpaper_task(self, request, pk):
        taskArrary = TestPaperTask.objects.filter(test_paper=pk)
        rows = []
        done = False
        score = 0
        all_score = 0
        myAnswer = []
        tprs = TestPaperRecord.objects.filter(test_paper=pk, submit_user=request.user)
        if tprs.exists():
            done = True
            for tpr in tprs:
                right_answer = practice_api.get_task_answer(tpr.task_hash, request.user)
                tmp = {
                    'taskId': tpr.task_hash,
                    'answer': tpr.answer,
                    'rightAnswer': right_answer
                }
                score = score + tpr.score
                myAnswer.append(tmp)

        for t in taskArrary:
            task = practice_api.get_task_object(t.task_hash)
            rows.append(Serializer(task, t).data)

            all_score = all_score + t.score

        return Response(
            {
                'response_data':
                    {
                        'tasks': rows, 'done': done,
                        'myAnswer': myAnswer, 'score': score,
                        'all_score': all_score
                    },
                'error_code': 0
            })

    @detail_route(methods=['POST'], )
    def submit_testpaper(self, request, pk):
        testpaper = TestPaper.objects.filter(id=int(pk)).first()
        if not testpaper:
            return Response({'error_code': 1})

        if TestPaperRecord.objects.filter(submit_user=request.user, test_paper=testpaper).exists():
            return Response({'error_code': 3})

        taskArrary = TestPaperTask.objects.filter(test_paper=pk)
        task_dict = {}
        for task in taskArrary:
            task_dict[task.task_hash] = task.score

        taskhashs = str(request.data.get('taskids'))
        answers = str(request.data.get('answers').encode('utf-8'))

        task_hash = taskhashs.split(',')
        answer = answers.split(',')

        task_count = len(taskArrary)
        submit_task_count = len(taskArrary)
        if task_count != submit_task_count:
            return Response({'error_code': 2})

        get_score = 0
        for i in range(0, task_count):
            # 判断题目是否正确
            # right = practice_api.validate_answer(task_hash[i], answer[i], request.user)
            right, score, specific_score = practice_api.validate_answer(task_hash[i], answer[i], request.user)
            if right:
                score = task_dict.get(task_hash[i])
                if score:
                    get_score += score
            else:
                score = 0
            TestPaperRecord.objects.create(
                test_paper=testpaper,
                score=score,
                task_hash=task_hash[i],
                answer=answer[i],
                solved=True,
                submit_user=request.user,
            )
        self.clear_cache()
        return Response({'response_data': {'allScore': get_score}, 'error_code': 0})
