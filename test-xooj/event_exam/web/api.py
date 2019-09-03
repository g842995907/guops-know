# -*- coding: utf-8 -*-
import re

from django.utils import timezone
from rest_framework import exceptions
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from common_framework.utils.cache import CacheProduct
from event import models as event_models
from event.utils import common as event_common
from event.web import api as base_api, error
from event_exam.utils.task import TaskHandler
from event_exam.utils.exam_auth import api_auth_permission
from event_exam.models import SolvedRecord, SubmitRecord, SubmitFlags
from event.models import EventTask
from practice import api as practice_api
from practice_capability.models import TestPaperTask
from practice_theory.models import ChoiceTask
from practice_real_vuln.models import RealVulnTask
from practice_exercise.models import PracticeExerciseTask
from practice.private_api import _commit_task_answer
from x_note.models import Note
from . import serializers as mserializers
from event_exam import models as exam_models
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

import random
import collections
import json

DELIMITER = '|'
multiple = 1
judgment = 2
radio = 0
operation = 4

is_choice = 1

RealVulnType = 1
PracticeExerciseType = 2

DEFAULT_CACHE_TIME = 60 * 5

class Serializer:
    def __init__(self, raw, et):
        self.data = {
            'title': raw.title,
            'id': str(raw.id),
            'hash': str(raw.hash),
            'score': float(et.task_score),
            'content': raw.content
        }

        p_type = int(raw.hash.split('.')[-1])
        if p_type == 0:
            self.data['options'] = collections.OrderedDict(sorted(json.loads(raw.option).items(), key=lambda t: t[0]))
            # self.data['options'] = raw.option
            self.data['is_choice_question'] = 1
            self.data['is_multiple_choice'] = 1 if raw.multiple else 0
            self.data['question_type'] = raw.multiple
        else:
            if raw.file and raw.file.url:
                file_attach = {
                    'name': raw.file.name,
                    'url': raw.file.url,
                }

                self.data['file_url'] = file_attach
            self.data['url'] = raw.url
            self.data['is_dynamic_env'] = raw.is_dynamic_env
            self.data['question_type'] = operation
            self.data['solving_mode'] = raw.solving_mode
            self.data['is_choice_question'] = 0
            self.data['score_mutiple'] = raw.score_multiple


class EventViewSet(base_api.EventViewSet):
    serializer_class = mserializers.EventSerializer

    @detail_route(methods=['get'], )
    @api_auth_permission
    def exam_task(self, request, pk):
        try:
            event = event_models.Event.objects.get(pk=pk)
        except Exception, e:
            raise exceptions.PermissionDenied(error.EVENT_NOT_START)

        taskArrary = event_models.EventTask.objects.filter(event=pk)
        rows = []
        done = False
        score = 0
        all_score = 0
        myAnswer = []
        eus = event_models.EventUserSubmitLog.objects.filter(event_task__event=pk, user=request.user)

        if eus.exists():
            done = True
            try:
                x_note = Note.objects.get(resource=event.hash, user=request.user)
                writeup_score = x_note.score
            except:
                writeup_score = 0
            score = score + writeup_score
            for e in eus:
                right_answer = practice_api.get_task_answer(e.event_task.task_hash, request.user)
                tmp = {
                    'taskId': e.event_task.task_hash,
                    'answer': e.answer,
                }
                if event.extendevent.ans_display_method == 0:
                    tmp['rightAnswer'] = right_answer
                if event.extendevent.ans_display_method == 1:
                    if event.end_time < timezone.now():
                        tmp['rightAnswer'] = right_answer
                score = score + e.score
                myAnswer.append(tmp)

        for t in taskArrary:
            task = practice_api.get_task_object(t.task_hash)
            rows.append(Serializer(task, t).data)

            all_score = all_score + t.task_score

        '''
        获取试卷状态：1.已经结束；2.正在进行；3.尚未开始
        '''
        now = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        if (event.start_time.strftime('%Y-%m-%d %H:%M:%S') <= now) and (
                    event.end_time.strftime('%Y-%m-%d %H:%M:%S') > now):
            process = 0
        elif (event.start_time.strftime('%Y-%m-%d %H:%M:%S') > now):
            process = 1
        else:
            process = 2

        return Response(
            {
                'response_data':
                    {
                        'tasks': rows, 'done': done,
                        'myAnswer': myAnswer, 'score': score,
                        'all_score': all_score,
                        'score_status': event.extendevent.score_status,
                        'rank_status': event.extendevent.rank_status
                    },
                'error_code': 0,
                'process': process
            })

    @detail_route(methods=['GET'], )
    @api_auth_permission
    def exam_user_ranking(self, request, pk):
        """
        获取当前用户考试排名
        """
        try:
            event = event_models.Event.objects.get(pk=pk)
        except Exception, e:
            raise exceptions.PermissionDenied(error.EVENT_NOT_START)

        from django.db.models import Sum
        eus = event_models.EventUserSubmitLog.objects.filter(event_task__event=pk).values('user').annotate(
            score=Sum('score'))
        x_note = Note.objects.filter(resource=event.hash).values('user').annotate(score=Sum('score'))
        # 添加writeup_score
        for data in eus:
            for note in x_note:
                if note['user'] == data['user']:
                    data['score'] += 2

        sorted_scores = sorted(list(eus), key=lambda a: -a.get('score'))
        ranking = ''
        for k, value in enumerate(sorted_scores):
            if value['user'] == request.user.id:
                ranking = k + 1

        return Response(data={'ranking': ranking})

    @detail_route(methods=['get'], )
    @api_auth_permission
    def get_tasks(self, request, pk):
        event = event_common.get_event_by_id(pk)

        if event.start_time > timezone.now():
            return Response({'response': {} , 'error_code': 1})
        if not event.public:
            return Response({'response': {}, 'error_code': 1})

        basic_information = {}
        grade = exam_models.SubmitRecord.objects.filter(event_id=event.id).filter(user_id=request.user).first()
        if grade is not None:
            basic_information["is_over"] = "true"
            basic_information["show_score"] = event.extendevent.score_status
            basic_information["answer"] = grade.answer

            if event.extendevent.score_status:
                basic_information["get_score"] = grade.score
                answer_dict, score_dict = self.get_correct_answer(event, pk)
                basic_information["correct_answer"] = answer_dict

        else:
            count_time = self.count_time(event)
            if count_time == 0 :
                basic_information["is_over"] = "true"
            else:
                basic_information["is_over"] = 'false'
                basic_information["count_time"] = count_time

        answer_record = SolvedRecord.objects.filter(user=request.user).filter(event=event).first()
        if answer_record is None:
            exam_models.SolvedRecord.objects.create(
                event=event,
                user=request.user,
            )
        return Response({'response': basic_information, 'error_code': 0})

    @detail_route(methods=['get'], )
    @api_auth_permission
    def review(self, request, pk):
        event = event_common.get_event_by_id(pk)

        if event.start_time > timezone.now():
            return Response({'response': {} , 'error_code': 1})
        if not event.public:
            return Response({'response': {}, 'error_code': 1})

        basic_information = {}
        grade = exam_models.SubmitRecord.objects.filter(event_id=event.id).filter(user_id=request.user).first()

        if grade is not None:
            basic_information["is_over"] = True
            basic_information["show_score"] = event.extendevent.score_status
            basic_information["rank_status"] = event.extendevent.rank_status
            basic_information["answer"] = grade.answer

            if event.extendevent.score_status:
                basic_information["get_score"] = grade.score
            if event.extendevent.rank_status:
                answer_dict, score_dict = self.get_correct_answer(event, pk)
                basic_information["correct_answer"] = answer_dict

                submit_reslut = SubmitFlags.objects.filter(event=event, user=request.user)
                is_right = {}

                if submit_reslut.exists():
                    for flag_result in submit_reslut:
                        is_right[flag_result.topic_hash] = True if flag_result.score != 0 else False
                basic_information["flag_is_right"] = is_right

        else:
            basic_information["is_over"] = False
            basic_information["answer"] = ''

        return Response({'response': basic_information, 'error_code': 0})

    def get_correct_answer(self, event, pk):
        test_list_cache = CacheProduct("test_list_cache")
        test_score_cache  = CacheProduct("test_score_cache")
        key = "%d_%d" % (int(pk), event.id)
        test_list_dateil = test_list_cache.get(key, None)
        test_score_dateil = test_score_cache.get(key, None)

        if test_list_dateil is None or test_score_dateil is None:
            task_arrary = self.get_event_task(pk)
            answer_dict = {}
            score_dict = {}
            for t in task_arrary:
                task = practice_api.get_task_object(t.task_hash)
                score_dict[int(task.id)] = t.task_score

                if task.answer is None:
                    is_dynamic_env = hasattr(task, "is_dynamic_env") if hasattr(task, "is_dynamic_env") else False
                    if is_dynamic_env:
                        task_answer = _("x_dynamic_answer")
                    else:
                        task_answer = _("x_answer_not_generated")
                else:
                    task_answer = task.answer
                answer_dict[int(task.id)] = str(task_answer)
            test_list_cache.set(key, answer_dict, DEFAULT_CACHE_TIME)
            test_score_cache.set(key, score_dict, DEFAULT_CACHE_TIME)
        else:
            answer_dict = test_list_dateil
            score_dict = test_score_dateil

        return answer_dict, score_dict

    # 时间事件
    def count_time(self, event):
        count_time = int((event.end_time - timezone.now()).total_seconds())
        if count_time < 0:
            return 0
        else:
            return count_time

    @detail_route(methods=['POST'], )
    @api_auth_permission
    def submit_testpaper(self, request, pk):
        event = event_common.get_event_by_id(pk)
        if not event:
            return Response({'error_code': 1})

        taskhash = str(request.data.get('taskhash'))
        tasktype = int(taskhash.split(".")[-1])
        task_id = request.data.get("topic_id") #该题目的id
        answers = str(request.data.get('answers').encode('utf-8')) #答案

        user = request.user

        # 没有答案
        if not answers:
            return Response({'error_code': 2})
        test_information = None
        if tasktype == RealVulnType:
            test_information = RealVulnTask.objects.filter(hash=taskhash).first()
        elif tasktype == PracticeExerciseType:
            test_information = PracticeExerciseTask.objects.filter(hash=taskhash).first()
        if not event or not test_information:
            return Response({'error_code': 1})

        _ret = _commit_task_answer(tasktype, test_information, user, answers)
        if _ret['is_solved'] and (not _ret.has_key("is_over")):
            # correct_answer, score_dict = self.get_correct_answer(event, pk)
            # topic_score = score_dict[int(task_id)]  # 获取该题目的分数

            task = EventTask.objects.filter(task_hash=taskhash).first()
            topic_score = task.task_score
            get_score = float(format(topic_score * float(_ret["score"]) / float(_ret['all_score']), '.2f'))

            submit_record = SubmitFlags.objects.filter(event=event, user=request.user, topic_hash=taskhash)
            submit_record_ob = submit_record.first()
            if submit_record_ob is not None:
                submit_record.update(
                    score = get_score
                )
            else:
                SubmitFlags.objects.create(
                    event=event,
                    user=request.user,
                    score=get_score,
                    topic_hash=taskhash
                )
        else:
            pass


        _ret['score_per'] = float(format(float(_ret["score"]) / float(_ret['all_score']), '.2f'))
        _ret["num_task"] = len(event_models.EventTask.objects.filter(event=event))
        _ret["num_done_task"] = request.data.get('topic_num')
        _ret["solving_mode"] = test_information.solving_mode
        _ret["question_type"] = test_information.multiple if (test_information.hash.split(".")[-1] == 0) else operation
        return Response({'response': _ret, 'error_code': 0})

    @detail_route(methods=['POST'], )
    @api_auth_permission
    def finish_up_job(self, request, pk):
        # 交卷
        event = event_common.get_event_by_id(pk)
        user = request.user

        count_time = self.count_time(event)
        if count_time <= 0:
            return Response({'error_code': 1})

        answers = request.data.get('answer')
        get_score = 0

        if answers != "" and answers is not None:
            answers_dict = json.loads(answers)
            correct_answer, score_dict = self.get_correct_answer(event, pk)
            for id, answer in answers_dict.items():
                topic_correct_answer = correct_answer[int(id)].split("|")
                topic_score = score_dict[int(id)]

                if re.match(r'^[A-G]*$', answer) is None:
                    pass
                else:
                   topic_user_answer = list(str(answer))

                   standard_list1 = set(topic_user_answer)
                   standard_list2 = set(topic_correct_answer)
                   if len(standard_list1.difference(standard_list2)) == 0 and len(
                           standard_list2.difference(standard_list1)) == 0:
                       get_score = get_score + topic_score

        if SubmitFlags.objects.filter(event=event, user=user).exists():
            for user_topic_score in SubmitFlags.objects.filter(event=event, user=user):
                get_score = get_score + float(user_topic_score.score)


        grade = exam_models.SubmitRecord.objects.filter(event_id=event.id).filter(user_id=request.user)

        if grade.exists():
            grade.update(
                answer=answers,
                score=get_score

            )
        else:
            exam_models.SubmitRecord.objects.create(
                event=event,
                user=user,
                answer=answers,
                score=get_score
            )

        t = SolvedRecord.objects.filter(event=event).filter(user=user)
        t.delete()

        return Response({'error_code': 0})

    def get_event_task(self, pk):
        task_cache = CacheProduct("get_event_task")
        key = pk

        event_task = task_cache.get(key, None)
        if event_task:
            return event_task

        event_task = event_models.EventTask.objects.filter(event=pk)
        if event_task:
            task_cache.set(key, event_task, DEFAULT_CACHE_TIME)

        return event_task


class EventSignupUserViewSet(base_api.EventSignupUserViewSet):
    serializer_class = mserializers.EventSignupUserSerializer


class EventSignupTeamViewSet(base_api.EventSignupTeamViewSet):
    serializer_class = mserializers.EventSignupTeamSerializer


class EventTaskViewSet(base_api.EventTaskViewSet):
    serializer_class = mserializers.EventTaskSerializer


class EventUserSubmitLogViewSet(base_api.EventUserSubmitLogViewSet):
    serializer_class = mserializers.EventUserSubmitLogSerializer
    task_handler_class = TaskHandler


class EventUserAnswerViewSet(base_api.EventUserAnswerViewSet):
    serializer_class = mserializers.EventUserAnswerSerializer


class EventNoticeViewSet(base_api.EventNoticeViewSet):
    serializer_class = mserializers.EventNoticeSerializer


class EventTaskNoticeViewSet(base_api.EventTaskNoticeViewSet):
    serializer_class = mserializers.EventTaskNoticeSerializer
