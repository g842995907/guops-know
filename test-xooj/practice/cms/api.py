# -*- coding: utf-8 -*-
import logging
import os

from django.http.response import FileResponse
from django.utils import timezone
from rest_framework import filters, viewsets, status, exceptions
from rest_framework import response
from rest_framework.decorators import api_view, list_route
from rest_framework.permissions import IsAuthenticated

from common_auth.api import oj_share_teacher
from common_framework.utils import delay_task
from common_framework.utils.constant import Status
from common_framework.utils.rest import mixins as common_mixins
from common_framework.utils.rest.filter import BootstrapOrderFilter
from common_framework.utils.rest.list_view import list_view
from common_framework.utils.rest.mixins import CacheModelMixin, DestroyModelMixin, PublicModelMixin, RequestDataMixin
from common_framework.utils.rest.permission import IsStaffPermission
from common_resource.setting import api_settings as resource_api_setting
from practice import constant
from practice.api import get_task_list, get_task_serializer, practice_config, PRACTICE_TYPE_THEORY, \
    PRACTICE_TYPE_REAL_VULN, PRACTICE_TYPE_EXCRISE
from practice.constant import TASKEVENT
from practice.models import TaskEvent
from practice.utils.task_event import dump_task_event, load_task_event, scan_task_event_resource
from practice_theory.models import ChoiceTask
from x_note.models import RecordLoads
from x_person.web.response import ResError
from . import serializers as mserializers

logger = logging.getLogger(__name__)


class TaskEventViewSet(
    common_mixins.RecordMixin,
    CacheModelMixin,
    common_mixins.AuthsMixin,
    common_mixins.ShareTeachersMixin,
    RequestDataMixin,
    DestroyModelMixin,
    PublicModelMixin,
    viewsets.ModelViewSet,
):
    queryset = TaskEvent.objects.all()
    serializer_class = mserializers.TaskEventSerializer
    permission_classes = (IsAuthenticated, IsStaffPermission,)
    filter_backends = (filters.SearchFilter, BootstrapOrderFilter)
    search_fields = ('name',)
    ordering_fields = ('id', 'weight', 'name', 'public', 'task_count')
    ordering = ('-id',)

    def get_faculty_major_objs(self, request, event_id, faculty=None, major=None):
        if not event_id:
            return []

        course = TaskEvent.objects.filter(id=event_id).first()
        if not course:
            return []

        return course

    def sub_perform_create(self, serializer):
        if serializer.validated_data.get('name') is None:
            raise exceptions.ValidationError({'name': [TASKEVENT.NAME_REQUIRED]})
        else:
            if TaskEvent.objects.filter(name=serializer.validated_data['name']).exists():
                raise exceptions.ValidationError({'name': [TASKEVENT.NMAE_HAVE_EXISTED]})
            elif serializer.validated_data.get('name').__len__() > 30:
                raise exceptions.ValidationError({'name': [TASKEVENT.FIELD_LENGTH_REQUIRED]})
        serializer.save(
            last_edit_time=timezone.now(),
            create_user=self.request.user,
            last_edit_user=self.request.user,
        )
        return True

    def sub_perform_update(self, serializer):
        if serializer.validated_data.get('name') == '':
            raise exceptions.ValidationError({'name': [TASKEVENT.NAME_REQUIRED]})
        elif serializer.validated_data.has_key('name'):
            if TaskEvent.objects.filter(name=serializer.validated_data['name']).exclude(
                    id=self.kwargs['pk']).exists():
                raise exceptions.ValidationError({'name': [TASKEVENT.NMAE_HAVE_EXISTED]})
            if serializer.validated_data.get('name').__len__() > 30:
                raise exceptions.ValidationError({'name': [TASKEVENT.FIELD_LENGTH_REQUIRED]})
        serializer.save(
            last_edit_time=timezone.now(),
            last_edit_user=self.request.user,
        )
        return True

    def sub_perform_destroy(self, instance):
        instance.status = constant.TaskEventStatus.DELETE
        instance.save()
        return True

    def perform_batch_destroy(self, queryset):
        """
        习题集删除处理,用户只可以删除自己创建的习题集，理论基础，真实漏洞，夺旗练习中没有该类别的使用，才可删除，否则不予删除
        """
        is_has_TaskEvent = False
        ids = self.request.data.getlist('ids', [])
        if not self.request.user.is_superuser:
            creater_taskevents = TaskEvent.objects.filter(create_user=self.request.user.id)  # 获取创建者的习题集
            creater_ids = [int(creater_taskevent.id) for creater_taskevent in creater_taskevents]
            for id in ids:
                if int(id) not in creater_ids:
                    raise exceptions.NotAcceptable(ResError.Other_TaskEvent_USEING)
        if practice_config.get(PRACTICE_TYPE_THEORY) is not None:  # 判断模块是否存在
            from practice_theory import models as theory_model
            if theory_model.ChoiceTask.objects.filter(event_id__in=ids, is_copy=False):  # 状态正常，且使用习题集
                is_has_TaskEvent = True
        if practice_config.get(PRACTICE_TYPE_EXCRISE) is not None:
            from practice_exercise import models as exercise_model
            if exercise_model.PracticeExerciseTask.objects.filter(event_id__in=ids, is_copy=False):
                is_has_TaskEvent = True
        if practice_config.get(PRACTICE_TYPE_REAL_VULN) is not None:
            from practice_real_vuln import models as real_vuln_model
            if real_vuln_model.RealVulnTask.objects.filter(event_id__in=ids, is_copy=False):
                is_has_TaskEvent = True
        if is_has_TaskEvent:
            raise exceptions.NotAcceptable(ResError.TaskEvent_USEING)

        if queryset.update(status=Status.DELETE) > 0:
            return True
        return False

    @list_route(methods=['get', 'post'], )
    def topic_empty(self, queryset):
        for ids in queryset.data.getlist('ids', []):
            ChoiceTask.objects.filter(event_id=ids, is_copy=0).delete()
        self.clear_cls_cache(TaskEventViewSet)
        return response.Response(status=status.HTTP_201_CREATED)

    @oj_share_teacher
    def get_queryset(self):
        queryset = self.queryset
        task_count = '''
                        CASE 
                            WHEN type = 0 THEN {theory} 
                            WHEN type = 1 THEN {real_vuln} 
                            WHEN type = 2 THEN {ctf} 
                            WHEN type = 3 THEN {man_machine}
                            WHEN type = 4 THEN {attack_defence}
                            WHEN type = 5 THEN {infiltration}
                        END
                    '''.format(
            theory='(SELECT COUNT(*) FROM practice_theory_choicetask WHERE practice_theory_choicetask.event_id = practice_taskevent.id '
                   'AND practice_theory_choicetask.status=1 AND practice_theory_choicetask.is_copy=0)',
            real_vuln='(SELECT COUNT(*) FROM practice_real_vuln_realvulntask WHERE practice_real_vuln_realvulntask.event_id = practice_taskevent.id '
                      'AND practice_real_vuln_realvulntask.status=1 AND practice_real_vuln_realvulntask.is_copy=0)',
            ctf='(SELECT COUNT(*) FROM practice_exercise_practiceexercisetask WHERE practice_exercise_practiceexercisetask.event_id = practice_taskevent.id '
                'AND practice_exercise_practiceexercisetask.status=1 AND practice_exercise_practiceexercisetask.is_copy=0)',
            man_machine='(SELECT COUNT(*) FROM practice_man_machine_manmachinetask WHERE practice_man_machine_manmachinetask.event_id = practice_taskevent.id '
                        'AND practice_man_machine_manmachinetask.status=1 AND practice_man_machine_manmachinetask.is_copy=0)',
            attack_defence='(SELECT COUNT(*) FROM practice_attack_defense_practiceattackdefensetask WHERE practice_attack_defense_practiceattackdefensetask.event_id = practice_taskevent.id '
                           'AND practice_attack_defense_practiceattackdefensetask.status=1 AND practice_attack_defense_practiceattackdefensetask.is_copy=0)',
            infiltration='(SELECT COUNT(*) FROM practice_infiltration_practiceinfiltrationtask WHERE practice_infiltration_practiceinfiltrationtask.event_id = practice_taskevent.id '
                           'AND practice_infiltration_practiceinfiltrationtask.status=1 AND practice_infiltration_practiceinfiltrationtask.is_copy=0)'
        )
        queryset = queryset.extra(
            select={'task_count': task_count}
        )
        p_type = self.query_data.get('type', int)
        if p_type is not None:
            queryset = queryset.filter(type=p_type)

        return queryset

    @list_route(methods=['get'], )
    def batch_dumps(self, request):
        downloadToken = 'downloadToken'
        ids = request.query_params.getlist('ids', [])
        download_token = request.query_params.get(downloadToken)
        if not ids:
            return response.Response(status=status.HTTP_200_OK)

        queryset = self.queryset.filter(id__in=ids)
        if not queryset:
            return response.Response(status=status.HTTP_200_OK)

        dump_path = dump_task_event(queryset)

        def file_iterator(file_name, chunk_size=512):
            with open(file_name, 'rb') as f:
                while True:
                    c = f.read(chunk_size)
                    if c:
                        yield c
                    else:
                        f.close()
                        os.remove(file_name)
                        break

        res = FileResponse(file_iterator(dump_path))
        res['Content-Length'] = os.path.getsize(dump_path)
        res['Content-Type'] = 'application/octet-stream'
        res['Content-Disposition'] = 'attachment;filename="%s"' % os.path.basename(dump_path.encode('utf8'))
        res.set_cookie(downloadToken, download_token)
        return res

    @list_route(methods=['get', 'post'], )
    def batch_loads(self, request):
        if request.method == 'GET':
            files = scan_task_event_resource()
            return response.Response({'files': files})
        elif request.method == 'POST':
            UPLOADTOKEN = 'uploadToken'
            filenames = request.data.getlist('filenames', [])
            attachment_file = request.FILES.get('attachment', None)
            upload_token = request.query_params.get(UPLOADTOKEN, None)

            if attachment_file:
                destination = open(os.path.join(resource_api_setting.LOAD_TMP_DIR, attachment_file.name), 'wb+')
                for chunk in attachment_file.chunks():  # 分块写入文件
                    destination.write(chunk)
                destination.close()
                filenames = [attachment_file.name]
            if not filenames:
                return response.Response(status=status.HTTP_201_CREATED)

            delay_task.new_task(self._batch_loads, 2, (filenames, upload_token, attachment_file.name))

            return response.Response(status=status.HTTP_201_CREATED)

    def _batch_loads(self, filenames, upload_token, file_name):
        user = self.request.user
        path = self.request.path
        info = ";".join([path, file_name])
        try:
            for filename in filenames:
                load_task_event(filename)
            RecordLoads.objects.create(slug=upload_token, status=True, info=info, user=user)
        except Exception as e:
            RecordLoads.objects.create(slug=upload_token, info=info, user=user, status=False, errorinfo=str(e))
            logger.info(e)
        self.clear_cache()


@api_view(['GET'])
def task_list(request):
    if request.method == 'GET':
        p_type = int(request.query_params.get('type_id', None))
        if p_type is None:
            return response.Response(constant.ILLEGAL_REQUEST_PARAMETERS, status=status.HTTP_200_OK)
        category = request.query_params.get('category', None)
        event = int(request.query_params.get('event', None))
        task_list = get_task_list(p_type=p_type, event=event, category=category)
        taskSerializer = get_task_serializer(p_type)
        if taskSerializer:
            if task_list:
                return list_view(request, task_list, taskSerializer)
            else:
                return response.Response(constant.ILLEGAL_REQUEST_PARAMETERS, status=status.HTTP_200_OK)
        else:
            return response.Response(constant.ILLEGAL_REQUEST_PARAMETERS, status=status.HTTP_200_OK)
