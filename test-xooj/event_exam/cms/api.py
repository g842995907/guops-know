# -*- coding: utf-8 -*-
import json
import os
from collections import OrderedDict
from datetime import datetime

from django.db.models import F, Count, Sum, Max, ProtectedError
from django.shortcuts import get_object_or_404
from django.conf import settings
from rest_framework import viewsets, permissions, exceptions, status
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from common_auth.models import User
from common_framework.utils.models.data import get_sub_model_data
from common_framework.utils.rest import mixins as common_mixins
from common_framework.utils.rest.permission import IsStaffPermission
from common_auth.api import oj_share_teacher
from event import models as event_models
from event.cms import api as base_api
from event.models import Event
from event.utils.mixins import ProductMixin
from event.utils.task import TaskHandler
from event_exam.constant import ExamResError
from event_exam.models import SolvedRecord, SubmitRecord, SubmitFlags
from event_exam.utils.task import TaskHandler
from practice import api as practice_api
from practice_theory.models import ChoiceTask
from practice.widgets.env.handlers import EnvHandler
from practice_capability.models import TestPaper, TestPaperTask
from x_note.models import Note
from . import serializers as mserializers
from django.utils.translation import ugettext_lazy as _


class EventViewSet(base_api.EventViewSet,
                   common_mixins.AuthsMixin,
                   common_mixins.ShareTeachersMixin
                   ):
    serializer_class = mserializers.EventSerializer

    def sub_perform_create(self, serializer):
        if serializer.validated_data.has_key('name'):
            if serializer.validated_data.get('name') == u'':
                raise exceptions.ValidationError({'error_messsage': [ExamResError.WARN_MESSAGES_8]})
            elif event_models.Event.objects.filter(name=serializer.validated_data.get('name'),
                                                   type=Event.Type.EXAM).exists():
                raise exceptions.ValidationError({'error_messsage': [ExamResError.WARN_MESSAGES_9]})

        now = datetime.now()
        if serializer.validated_data.has_key('start_time') and serializer.validated_data.has_key('end_time'):
            start_time = serializer.validated_data.get('start_time')
            end_time = serializer.validated_data.get('end_time')
            if start_time >= end_time:
                raise exceptions.ValidationError({'start_time': [ExamResError.WARN_MESSAGES_1]})
            elif start_time <= now:
                raise exceptions.ValidationError({'start_time': [ExamResError.WARN_MESSAGES_4]})
            elif end_time <= now:
                raise exceptions.ValidationError({'start_time': [ExamResError.WARN_MESSAGES_5]})
        else:
            raise exceptions.ValidationError({'start_time': [ExamResError.WARN_MESSAGES_6]})
        serializer.save(
            type=self.event_type,
            integral_mode=event_models.Event.IntegralMode.CUMULATIVE,
            create_user=self.request.user,
            last_edit_user=self.request.user,
        )
        super(EventViewSet, self).sub_perform_create(serializer)
        event = serializer.instance

        extend_event_data = get_sub_model_data(self.request.data, ['extend_event'])
        if extend_event_data:
            extend_event_data['event'] = event.pk
            extend_event_serializer = mserializers.ExtendEventSerializer(data=extend_event_data)
            extend_event_serializer.is_valid(raise_exception=True)
            extend_event_serializer.save(event=event)

        if self.request.data.has_key('capabili_name') and self.request.data['capabili_name'].isdigit():
            self._handle_exam_and_capabile(self.request.data['capabili_name'], event)

        return True

    def sub_perform_update(self, serializer):
        if serializer.validated_data.has_key('name'):
            if serializer.validated_data.get('name') == u'':
                raise exceptions.ValidationError({'error_messsage': [ExamResError.WARN_MESSAGES_8]})
            elif event_models.Event.objects.filter(name=serializer.validated_data.get('name'),
                                                   type=Event.Type.EXAM).exists():
                raise exceptions.ValidationError({'error_messsage': [ExamResError.WARN_MESSAGES_9]})

        event = event_models.Event.objects.filter(id=self.kwargs.get('pk')).first()
        # super(EventViewSet, self).sub_perform_update(serializer)

        now = datetime.now()
        if now < event.start_time:
            if serializer.validated_data.has_key('start_time') and not serializer.validated_data.has_key('end_time'):
                start_time = serializer.validated_data.get('start_time')
                if start_time < now:
                    raise exceptions.ValidationError({'start_time': [ExamResError.WARN_MESSAGES_3]})
                elif start_time >= event.end_time:
                    raise exceptions.ValidationError({'start_time': [ExamResError.WARN_MESSAGES_1]})
            elif serializer.validated_data.has_key('end_time') and not serializer.validated_data.has_key('start_time'):
                end_time = serializer.validated_data.get('end_time')
                if end_time < event.start_time:
                    raise exceptions.ValidationError({'start_time': [ExamResError.WARN_MESSAGES_1]})
            elif serializer.validated_data.has_key('start_time') and serializer.validated_data.has_key('end_time'):
                start_time = serializer.validated_data.get('start_time')
                end_time = serializer.validated_data.get('end_time')
                if start_time < now:
                    raise exceptions.ValidationError({'start_time': [ExamResError.WARN_MESSAGES_3]})
                elif start_time > end_time:
                    raise exceptions.ValidationError({'start_time': [ExamResError.WARN_MESSAGES_1]})
        else:
            if serializer.validated_data.has_key('start_time') and not serializer.validated_data.has_key('end_time'):
                start_time = serializer.validated_data.get('start_time')
                if start_time >= now:
                    raise exceptions.ValidationError({'start_time': [ExamResError.WARN_MESSAGES_7]})
                elif start_time >= event.end_time:
                    raise exceptions.ValidationError({'start_time': [ExamResError.WARN_MESSAGES_1]})
            elif serializer.validated_data.has_key('end_time') and not serializer.validated_data.has_key('start_time'):
                end_time = serializer.validated_data.get('end_time')
                if end_time <= now:
                    raise exceptions.ValidationError({'start_time': [ExamResError.WARN_MESSAGES_2]})
            elif serializer.validated_data.has_key('start_time') and serializer.validated_data.has_key('end_time'):
                start_time = serializer.validated_data.get('start_time')
                end_time = serializer.validated_data.get('end_time')
                if start_time >= now:
                    raise exceptions.ValidationError({'start_time': [ExamResError.WARN_MESSAGES_7]})
                elif start_time > end_time:
                    raise exceptions.ValidationError({'start_time': [ExamResError.WARN_MESSAGES_1]})
                elif end_time <= now:
                    raise exceptions.ValidationError({'start_time': [ExamResError.WARN_MESSAGES_2]})

        extend_event_data = get_sub_model_data(self.request.data, ['extend_event'])
        if extend_event_data:
            if hasattr(event, 'extendevent'):
                # update
                extend_event_serializer = mserializers.ExtendEventSerializer(
                    event.extendevent,
                    data=extend_event_data,
                    partial=True
                )
            else:
                # create
                extend_event_data['event'] = event.pk
                extend_event_serializer = mserializers.ExtendEventSerializer(
                    data=extend_event_data,
                )
            extend_event_serializer.is_valid(raise_exception=True)
            extend_event_serializer.save(event=event)
        super(EventViewSet, self).sub_perform_update(serializer)

        if self.request.data.has_key('capabili_name') and self.request.data['capabili_name'].isdigit():
            self._handle_exam_and_capabile(self.request.data['capabili_name'], event, isUpdate=True)

        return True

    def _handle_exam_and_capabile(self, capabili_id, eventInstance, isUpdate=False):
        testPaper = get_object_or_404(TestPaper, pk=int(capabili_id))
        taskArrary = TestPaperTask.objects.filter(test_paper__id=testPaper.id)
        eventInstance.extendevent.capabili_name = testPaper.name
        eventInstance.extendevent.save()
        # 将试卷中的题目复制到考试当中去
        if isUpdate:
            event_task_list = event_models.EventTask.objects.filter(event=eventInstance)
            if event_task_list:
                # 判断原来是否存在初始数据, 批量删除
                try:
                    event_models.EventTask.objects.filter(event=eventInstance).delete()
                except ProtectedError:
                    raise exceptions.ParseError(ExamResError.CANNT_CHANGE_HAS_DONE)

        task_hashs = []
        for data in taskArrary:
            task_hashs.append(data.task_hash)
        task_copy_hashs = practice_api.copy_task_by_hash(task_hashs)

        event_task_list = []
        new_topic_list = []
        for task in taskArrary:
            task_type = TaskHandler.get_type_by_hash(task.task_hash)
            event_task = event_models.EventTask(
                event=eventInstance,
                task_hash=task_copy_hashs[task_hashs.index(task.task_hash)],
                task_score=task.score,
                type=task_type,
                seq=1,
            )
            event_task_list.append(event_task)

            new_topic_dict = {}
            if task_type == 0:
                new_topic = ChoiceTask.objects.filter(hash=task_copy_hashs[task_hashs.index(task.task_hash)]).first()
                if new_topic is None:
                    raise exceptions.ParseError(ExamResError.TESTPAPER_ABNORMAL)
                try:
                    new_topic_dict["content"] = new_topic.content
                    new_topic_dict["id"] = new_topic.id
                    new_topic_dict["option"] = new_topic.option
                    new_topic_dict["score"] = task.score
                    new_topic_dict["multiple"] = new_topic.multiple
                    new_topic_list.append(new_topic_dict)
                except ProtectedError:
                    raise exceptions.ParseError(ExamResError.TESTPAPER_ABNORMAL)
            else:
                tmp = practice_api.get_task_info(task_copy_hashs[task_hashs.index(task.task_hash)], backend=True)
                if tmp is None:
                    raise exceptions.ParseError(ExamResError.TESTPAPER_ABNORMAL)
                try:
                    new_topic_dict["title"] = tmp["title"] if tmp.get("title", None) else None
                    new_topic_dict["content"] = tmp["content"] if tmp.get("content", None) else None
                    new_topic_dict["id"] = tmp['id']
                    new_topic_dict["hash"] = tmp["hash"]
                    new_topic_dict["file_url"] = tmp["file_url"] if tmp.has_key("file_url") else None
                    new_topic_dict["attach_url"] = tmp["file_url"].get("url", None) if tmp.get("file_url", None) else None
                    new_topic_dict["url"] = tmp["url"] if tmp.get("url", None) else None
                    new_topic_dict["is_dynamic_env"] = tmp["is_dynamic_env"]
                    new_topic_dict["solving_mode"] = tmp["solving_mode"]
                    new_topic_dict["option"] = None
                    new_topic_dict["score"] = task.score
                    new_topic_dict["multiple"] = 4
                    new_topic_list.append(new_topic_dict)
                except ProtectedError:
                    raise exceptions.ParseError(ExamResError.TESTPAPER_ABNORMAL)

        event_models.EventTask.objects.bulk_create(event_task_list)

        if new_topic_list:
            datas = json.dumps(new_topic_list)

            json_name = str(eventInstance.hash + ".json")
            json_url = os.path.join(settings.BASE_DIR, 'media/event_exam/json/{}'.format(json_name))
            with open(json_url, "w", ) as  f:
                f.write(datas)
                f.close()


    def extra_handle_list_data(self, data):
        id_event = {row['id']: row for row in data}
        result = event_models.EventTask.objects.filter(event__in=id_event.keys()).values('event').annotate(
            task_count=Count('event'),
            all_score=Sum('task_score')
        )
        for task in result:
            row = id_event[task['event']]
            row.update({
                'task_count': task['task_count'],
                'all_score': float(task['all_score'])
            })
        return data

    @detail_route(methods=['get'], )
    def exam_result_detail(self, request, pk):
        submit_user_id = self.query_data.get('user', int)
        event_exam = self.get_object()
        taskArrary = event_models.EventTask.objects.filter(event=pk)
        if not taskArrary.exists():
            return Response({'error_code': 1}, status=status.HTTP_200_OK)
        user = User.objects.filter(id=submit_user_id).first()
        if user is None:
            return Response({'error_code': 1}, status=status.HTTP_200_OK)
        task_count = 0
        all_score = 0
        tasks = []
        no_writeup_score = 0
        submit_record = SubmitRecord.objects.filter(event=pk,user=user,).first()
        if submit_record is None:
            return Response({'error_code': 1}, status=status.HTTP_200_OK)
        answer_dict = json.loads(submit_record.answer) if len(submit_record.answer) != 0  else {}
        user_all_score = submit_record.score if hasattr(submit_record, "score") else 0


        for t in taskArrary:
            all_score = all_score + t.task_score
            task_count += 1
            tmp = practice_api.get_task_info(t.task_hash, backend=True)
            option_json = OrderedDict()
            if int(t.task_hash.split(".")[1]) == 0:
                for row in map(lambda x: {x: json.loads(tmp["option"])[x]}, sorted(json.loads(tmp["option"]))):
                    option_json.update(row)

                if len(answer_dict) != 0:
                    user_answer = answer_dict.get(str(tmp["id"]), None) if answer_dict.get(str(tmp["id"]), None) else ""
                else:
                    user_answer = ""

                answer = "".join(sorted(tmp["answer"].split("|"))) if tmp.get("answer", None) else ""

                diff_set = list(set(list(answer)) ^ set(list(user_answer)))


                tmp.update({
                    "score":  t.task_score,
                    "user_answer": user_answer,
                    "answer": answer,
                    "option": json.dumps(option_json),
                    "is_right": True if len(diff_set) == 0 else False
                })
                # user_all_score += t.score
                no_writeup_score += t.task_score
                tasks.append(tmp)
            else:
                if len(answer_dict) != 0:
                    if answer_dict.get(str(tmp["id"]), None) is not None:
                        user_answer = answer_dict.get(str(tmp["id"])).split(",")
                    else:
                        user_answer = []
                else:
                    user_answer = []
                get_topic_score = SubmitFlags.objects.filter(event=pk, user=user, topic_hash=tmp["hash"]).first()
                if tmp['file_url'] != None:
                    file_name = tmp['file_url']["name"]
                    file_name = os.path.split(file_name)[-1]
                    tmp['file_url']["name"] = file_name

                answer = tmp.get("answer", None) if tmp.get("answer", None) else None
                if answer is None:
                    is_dynamic_flag = tmp.get("task_env").get("is_dynamic_flag") if tmp.get("task_env", None) else False
                    answer = _("x_dynamic_answer") if is_dynamic_flag else _("x_answer_not_generated")
                else:
                    answer = json.dumps(answer)

                tmp.update({
                    "score": t.task_score,
                    "user_answer": user_answer,
                    "answer": answer if answer is not None else None,
                    "get_score": get_topic_score.score if get_topic_score is not None else 0
                })

                # user_all_score += t.score
                no_writeup_score += t.task_score
                tasks.append(tmp)

        context = {
            'name': event_exam.name,
            'number': task_count,
            'all_score': int(all_score),
            'user': {
                "first_name": user.first_name,
                "faculty": user.faculty.name if user.faculty else "",
                "major": user.major.name if user.major else "",
                "classes": user.classes.name if user.classes else "",
                "username": user.username,
            }
        }

        context["tasks"] = tasks
        context["user_all_score"] = user_all_score
        context["no_writeup_score"] = no_writeup_score
        return Response({'response_data': context, 'error_code': 0}, status=status.HTTP_200_OK)

    def get_faculty_major_objs(self, request, exam_id, faculty=None, major=None):
        if not exam_id:
            return None

        course = event_models.Event.objects.filter(id=exam_id).first()
        if not course:
            return None

        return course


class EventSignupUserViewSet(base_api.EventSignupUserViewSet):
    serializer_class = mserializers.EventSignupUserSerializer


class EventSignupTeamViewSet(base_api.EventSignupTeamViewSet):
    serializer_class = mserializers.EventSignupTeamSerializer


class EventTaskViewSet(base_api.EventTaskViewSet):
    serializer_class = mserializers.EventTaskSerializer
    task_handler_class = TaskHandler


class EventUserSubmitLogViewSet(base_api.EventUserSubmitLogViewSet):
    serializer_class = mserializers.EventUserSubmitLogSerializer
    task_handler_class = TaskHandler


class EventUserAnswerViewSet(base_api.EventUserAnswerViewSet):
    serializer_class = mserializers.EventUserAnswerSerializer


class EventNoticeViewSet(base_api.EventNoticeViewSet):
    serializer_class = mserializers.EventNoticeSerializer


class EventTaskNoticeViewSet(base_api.EventTaskNoticeViewSet):
    serializer_class = mserializers.EventTaskNoticeSerializer


class EventRankViewSet(ProductMixin,
                       common_mixins.CacheModelMixin,
                       viewsets.ReadOnlyModelViewSet):
    queryset = event_models.EventUserSubmitLog.objects.filter()
    serializer_class = mserializers.EventRankSerializer
    permission_classes = (permissions.IsAuthenticated, IsStaffPermission,)

    def get_queryset(self):
        queryset = self.queryset

        event_id = self.query_data.get('event', int)
        if event_id is None:
            raise exceptions.NotFound()
        try:
            event = event_models.Event.objects.get(pk=event_id)
        except event_models.Event.DoesNotExist as e:
            raise exceptions.NotFound()

        self.extra_attr.event = event
        queryset = queryset.filter(event_task__event=event)
        queryset = queryset.values('user__id').annotate(obj_id=F('user__id'), obj_name=F('user__first_name'), )
        self.extra_attr.group_name = 'user'

        queryset = queryset.annotate(
            sum_score=Sum('score'),
            submit_time=Max('time'),
        ).order_by('-sum_score', 'submit_time')

        return queryset

    def extra_handle_list_data(self, data):
        event = self.extra_attr.event
        resource = event.hash

        for row in data:
            row['status'] = '已提交'
            row['status_code'] = 2
            note = Note.objects.filter(resource=resource, user_id=row['obj_id']).first()

            if note:
                row['sum_score'] = row['sum_score'] + note.score
                row['writeup_score'] = note.score
        return data
