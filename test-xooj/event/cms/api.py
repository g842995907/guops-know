# -*- coding: utf-8 -*-
from django.db import transaction
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from rest_framework import exceptions, filters, mixins, status, viewsets
from rest_framework.decorators import list_route, detail_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common_auth.api import oj_share_teacher
from common_auth.models import Classes
from common_framework.utils.rest import filter as common_filters
from common_framework.utils.rest import mixins as common_mixins
from common_framework.utils.rest.permission import IsStaffPermission
from event import models as event_models
from event.utils import common
from event.utils.mixins import ProductMixin
from event.utils.task import TaskHandler
from system_configuration.cms.api import add_sys_notice
from system_configuration.models import SysNotice
from . import error
from . import serializers as mserializers


class EventViewSet(
    common_mixins.RecordMixin,
    ProductMixin,
    common_mixins.CacheModelMixin,
    common_mixins.PublicModelMixin,
    common_mixins.DestroyModelMixin,
    viewsets.ModelViewSet
):
    queryset = event_models.Event.objects.all()
    serializer_class = mserializers.EventSerializer
    permission_classes = (IsAuthenticated, IsStaffPermission,)
    filter_backends = (filters.SearchFilter, common_filters.BootstrapOrderFilter)
    search_fields = ('name',)
    ordering_fields = ('process', 'create_time', 'start_time', 'end_time', 'name', 'public')
    ordering = ('process', '-create_time')

    def init_type_queryset(self):
        self.queryset = self.queryset.filter(type=self.event_type)

    @oj_share_teacher
    def get_queryset(self):
        # queryset = common.get_user_event_queryset(self.request.user, self.queryset)
        queryset = self.queryset
        mode = self.query_data.get('mode', event_models.Event.Mode.values())
        if mode is not None:
            queryset = queryset.filter(mode=mode)

        integral_mode = self.query_data.get('integral_mode', event_models.Event.IntegralMode.values())
        if integral_mode is not None:
            queryset = queryset.filter(integral_mode=integral_mode)

        reward_mode = self.query_data.get('reward_mode', event_models.Event.RewardMode.values())
        if reward_mode is not None:
            queryset = queryset.filter(reward_mode=reward_mode)

        now = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        process = self.query_data.get('process', event_models.Event.Process.values())
        if process is not None:
            if process == event_models.Event.Process.INPROGRESS:
                queryset = queryset.filter(start_time__lte=now, end_time__gt=now)
            elif process == event_models.Event.Process.COMING:
                queryset = queryset.filter(start_time__gt=now)
            elif process == event_models.Event.Process.OVER:
                queryset = queryset.filter(end_time__lte=now)
            else:
                pass
        else:
            process = '''
                CASE 
                    WHEN (start_time <= '{now}' and end_time > '{now}') THEN {inprogress} 
                    WHEN start_time > '{now}' then {coming} 
                    WHEN end_time <= '{now}' THEN {over} 
                END
            '''.format(
                now=now,
                inprogress=event_models.Event.Process.INPROGRESS,
                coming=event_models.Event.Process.COMING,
                over=event_models.Event.Process.OVER,
            )
        copy_exam_id = self.query_data.get('copy_exam_id', int)
        if copy_exam_id is not None:
            queryset = queryset.exclude(id=copy_exam_id)
        queryset = queryset.extra(
            select={'process': process}
        )

        return queryset

    def sub_perform_create(self, serializer):
        serializer.save(
            type=self.event_type,
            create_user=self.request.user,
            last_edit_user=self.request.user,
        )
        return True

    def sub_perform_update(self, serializer):
        # 管理员或创建者才能共享教员
        # if is_admin(self.request.user) or serializer.instance.create_user == self.request.user:
        #     if not serializer.validated_data.has_key('teachers'):
        #         serializer.validated_data['teachers'] = []
        # else:
        #     serializer.validated_data.pop('teachers', None)

        # 动态分数还是题目分数变了, 更新相关的题目缓存,
        integral_mode = serializer.validated_data.get('integral_mode')
        if integral_mode is not None and serializer.instance.integral_mode != integral_mode:
            if hasattr(self, 'task_related_cache_class'):
                self.clear_cls_cache(self.task_related_cache_class)

        # 更新token相关缓存
        public_token = serializer.validated_data.get('public_token')
        if public_token is not None and serializer.instance.public_token != public_token:
            if hasattr(self, 'token_related_cache_class'):
                self.clear_cls_cache(self.token_related_cache_class)

        serializer.save(
            last_edit_time=timezone.now(),
            last_edit_user=self.request.user,
        )
        return True

    def sub_perform_destroy(self, instance):
        instance.status = event_models.Event.Status.DELETE
        instance.save()
        return True

    # 初始化比赛，重置比赛, 用于测试
    @detail_route(methods=['post'], )
    def reset(self, request, pk):
        event = self.get_object()
        now = timezone.now()
        if event.start_time < now:
            raise exceptions.PermissionDenied(error.ONLY_CAN_RESET_COMING_EVENT)

        with transaction.atomic():
            # 清空报名
            event_models.EventSignupUser.original_objects.filter(
                event=pk
            ).delete()
            event_models.EventSignupTeam.original_objects.filter(
                event=pk
            ).delete()
            # 　清空提交的Writeup
            event_models.EventWriteup.original_objects.filter(
                event=pk
            ).delete()
            # 　清空提交日志
            event_models.EventUserSubmitLog.objects.filter(
                event_task__event=pk
            ).delete()
            # 　清空得分记录
            event_models.EventUserAnswer.objects.filter(
                event_task__event=pk
            ).delete()
            # 　清空比赛公告
            event_models.EventNotice.original_objects.filter(
                event=pk
            ).delete()
            # 　清空题目提示
            event_models.EventTaskNotice.original_objects.filter(
                event_task__event=pk
            ).delete()
            # 　清空题目访问记录
            event_models.EventTaskAccessLog.objects.filter(
                event_task__event=pk
            ).delete()
        # 清空相关缓存
        if hasattr(self, 'reset_related_cache_class'):
            self.clear_cls_cache(self.reset_related_cache_class)
        return Response(status=status.HTTP_200_OK)

    def after_set_auth(self, obj, ac_to_add, ac_to_del):
        start = obj.start_time.strftime("%Y-%m-%d %H:%M:%S")
        end = obj.start_time.strftime("%Y-%m-%d %H:%M:%S")
        name = obj.name
        content = "~".join([start, end]) + '\n' + name
        for classes_id in ac_to_add:
            classes = Classes.objects.get(id=classes_id)
            if classes:
                add_sys_notice(
                    user=self.request.user,
                    name=_("x_event_notice"),
                    content=content,
                    classes=classes,
                    type=SysNotice.Type.EVENTMESSAGE
                )


class BaseEventSignupViewSet(ProductMixin,
                             common_mixins.DestroyModelMixin,
                             common_mixins.CacheModelMixin,
                             mixins.UpdateModelMixin,
                             mixins.DestroyModelMixin,
                             viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsAuthenticated, IsStaffPermission,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    ordering_fields = ('time',)
    ordering = ('-time',)

    def init_type_queryset(self):
        self.queryset = self.queryset.filter(event__type=self.event_type)

    def get_queryset(self):
        queryset = common.get_user_event_related_queryset(self.request.user, self.queryset)

        event = self.query_data.get('event', int)
        if event is not None:
            queryset = queryset.filter(event=event)

        return queryset

    def sub_perform_update(self, serializer):
        serializer.save(
            last_edit_time=timezone.now(),
            last_edit_user=self.request.user,
        )
        return True

    def sub_perform_destroy(self, instance):
        instance.status = event_models.BaseEventSignup.Status.DELETE
        instance.save()
        return True


class EventSignupUserViewSet(BaseEventSignupViewSet):
    queryset = event_models.EventSignupUser.objects.all()
    serializer_class = mserializers.EventSignupUserSerializer
    search_fields = ('user__username', 'event__name')


class EventSignupTeamViewSet(BaseEventSignupViewSet):
    queryset = event_models.EventSignupTeam.objects.all()
    serializer_class = mserializers.EventSignupTeamSerializer
    search_fields = ('team__name', 'event__name')


class BaseEventSignupDetailViewSet(ProductMixin,
                                   common_mixins.CacheModelMixin,
                                   viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsAuthenticated, IsStaffPermission,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    ordering_fields = ('sum_score', 'last_submit_time', 'time',)
    ordering = ('-sum_score', 'last_submit_time', 'time',)

    def init_type_queryset(self):
        self.queryset = self.queryset.filter(event__type=self.event_type)

    def get_queryset(self):
        queryset = common.get_user_event_related_queryset(self.request.user, self.queryset)

        event = self.query_data.get('event', int)
        if event is not None:
            queryset = queryset.filter(event=event)
        else:
            raise exceptions.ValidationError(error.EVENT_NOT_EXIST)

        table_user_answer = event_models.EventUserAnswer._meta.db_table
        table_task = event_models.EventTask._meta.db_table

        from_str = '''
            FROM {table_user_answer} 
                INNER JOIN {table_task} 
                ON {table_user_answer}.event_task_id = {table_task}.id 
                    and {table_task}.event_id = {event}
            WHERE 
                {table_user_answer}.{obj_id_attr} = {table_signup_obj}.{obj_id_attr} 
                and {table_user_answer}.status = {status_normal}
        '''.format(
            table_user_answer=table_user_answer,
            table_task=table_task,
            event=event,
            status_normal=event_models.EventUserAnswer.Status.NORMAL,
            table_signup_obj=self.queryset.model._meta.db_table,
            obj_id_attr='{}_id'.format(self._obj_name),
        )

        queryset = queryset.extra(
            select={
                'solved_count': 'SELECT count(0) {from_str}'.format(
                    table_user_answer=table_user_answer,
                    from_str=from_str
                ),
                'sum_score': 'SELECT sum({table_user_answer}.score) {from_str}'.format(
                    table_user_answer=table_user_answer,
                    from_str=from_str
                ),
                'last_submit_time': 'SELECT max({table_user_answer}.time) {from_str}'.format(
                    table_user_answer=table_user_answer,
                    from_str=from_str
                ),
            }
        )

        return queryset


class EventSignupUserDetailViewSet(BaseEventSignupDetailViewSet):
    queryset = event_models.EventSignupUser.objects.all()
    search_fields = ('user__username', 'event__name')
    _obj_name = 'user'


class EventSignupTeamDetailViewSet(BaseEventSignupDetailViewSet):
    queryset = event_models.EventSignupTeam.objects.all()
    search_fields = ('team__name', 'event__name')
    _obj_name = 'team'


class EventTaskViewSet(ProductMixin,
                       common_mixins.CacheModelMixin,
                       common_mixins.DestroyModelMixin,
                       viewsets.ModelViewSet):
    queryset = event_models.EventTask.objects.all()
    serializer_class = mserializers.EventTaskSerializer
    permission_classes = (IsAuthenticated, IsStaffPermission,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('event__name',)
    ordering_fields = ('event', 'seq')
    ordering = ('event', 'seq')
    task_handler_class = TaskHandler

    def init_type_queryset(self):
        self.queryset = self.queryset.filter(event__type=self.event_type)

    def get_queryset(self):
        queryset = common.get_user_event_related_queryset(self.request.user, self.queryset)

        event = self.query_data.get('event', int)
        if event is not None:
            queryset = queryset.filter(event=event)

        task_type = self.query_data.get('type', event_models.EventTask.Type.values())
        if task_type is not None:
            queryset = queryset.filter(type=task_type)

        from django.db.models import Count
        queryset = queryset.annotate(sloved_count=Count('eventuseranswer'))

        return queryset

    @list_route(methods=['post'], )
    def batch_create(self, request):
        event_pk = self.shift_data.get('event', int)
        task_hashs = self.shift_data.getlist('task_hashs', str)
        task_scores = self.shift_data.getlist('task_scores', int)
        if not task_hashs:
            raise exceptions.ValidationError(error.EMPTY_REQUEST)

        if task_scores and len(task_scores) != len(task_hashs):
            raise exceptions.ValidationError(error.TASK_SCORE_NOT_CORRESPONDING)

        try:
            event = common.get_user_event(request.user, event_pk)
        except event_models.Event.DoesNotExist as e:
            raise exceptions.NotFound(error.EVENT_NOT_EXIST)

        handled_task_hashs = self.task_handler_class.handle_tasks(task_hashs)

        seq = event_models.EventTask.objects.filter(event=event).count() + 1
        event_tasks = []
        for i, task_hash in enumerate(handled_task_hashs):
            event_task = event_models.EventTask(
                event=event,
                seq=seq,
                task_hash=task_hash,
                type=task_hash.split('.')[-1],
                status=event_models.EventTask.Status.CLOSE
            )
            if task_scores:
                event_task.task_score = task_scores[i]
            event_tasks.append(event_task)
            seq = seq + 1

        event_models.EventTask.objects.bulk_create(event_tasks)
        self.clear_cache()

        return Response(status=status.HTTP_200_OK)

    @list_route(methods=['patch'], )
    def batch_public(self, request):
        ids = self.shift_data.getlist('ids', int)
        if not ids:
            return Response(status=status.HTTP_204_NO_CONTENT)

        public = self.shift_data.get('public', int)

        queryset = self.queryset.filter(id__in=ids)
        if queryset.update(public=public, public_time=timezone.now()) > 0:
            self.clear_cache()

        return Response(status=status.HTTP_200_OK)


class EventWriteupViewSet(ProductMixin,
                          common_mixins.CacheModelMixin,
                          viewsets.ReadOnlyModelViewSet):
    queryset = event_models.EventWriteup.objects.all()
    serializer_class = mserializers.EventWriteupSerializer
    permission_classes = (IsAuthenticated, IsStaffPermission,)
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = ('time',)
    ordering = ('-time',)

    def init_type_queryset(self):
        self.queryset = self.queryset.filter(event__type=self.event_type)

    def get_queryset(self):
        queryset = common.get_user_event_related_queryset(self.request.user, self.queryset)

        user = self.query_data.get('user', int)
        if user is not None:
            queryset = queryset.filter(user=user)

        team = self.query_data.get('team', int)
        if team is not None:
            queryset = queryset.filter(team=team)

        event = self.query_data.get('event', int)
        if event is not None:
            queryset = queryset.filter(event=event)

        return queryset


class EventUserSubmitLogViewSet(ProductMixin,
                                common_mixins.CacheModelMixin,
                                viewsets.ReadOnlyModelViewSet):
    queryset = event_models.EventUserSubmitLog.objects.all()
    serializer_class = mserializers.EventUserSubmitLogSerializer
    permission_classes = (IsAuthenticated, IsStaffPermission,)
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = ('time')
    ordering = ('-time')

    def init_type_queryset(self):
        self.queryset = self.queryset.filter(event_task__event__type=self.event_type)

    def get_queryset(self):
        queryset = common.get_user_event_task_related_queryset(self.request.user, self.queryset)

        user = self.query_data.get('user', int)
        if user is not None:
            queryset = queryset.filter(user=user)

        team = self.query_data.get('team', int)
        if team is not None:
            queryset = queryset.filter(team=team)

        event_task = self.query_data.get('event_task', int)
        if event_task is not None:
            queryset = queryset.filter(event_task=event_task)

        return queryset


class EventUserAnswerViewSet(ProductMixin,
                             common_mixins.CacheModelMixin,
                             mixins.UpdateModelMixin,
                             viewsets.ReadOnlyModelViewSet):
    queryset = event_models.EventUserAnswer.objects.all()
    serializer_class = mserializers.EventUserAnswerSerializer
    permission_classes = (IsAuthenticated, IsStaffPermission,)
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = ('event_task', 'time')
    ordering = ('event_task', '-time')

    def init_type_queryset(self):
        self.queryset = self.queryset.filter(event_task__event__type=self.event_type)

    def get_queryset(self):
        queryset = common.get_user_event_task_related_queryset(self.request.user, self.queryset)

        user = self.query_data.get('user', int)
        if user is not None:
            queryset = queryset.filter(user=user)

        team = self.query_data.get('team', int)
        if team is not None:
            queryset = queryset.filter(team=team)

        event_task = self.query_data.get('event_task', int)
        if event_task is not None:
            queryset = queryset.filter(event_task=event_task)

        return queryset

    def sub_perform_update(self, serializer):
        serializer.save(
            last_edit_time=timezone.now(),
            last_edit_user=self.request.user,
        )
        return True


class BaseNoticeViewSet(ProductMixin,
                        common_mixins.CacheModelMixin,
                        common_mixins.DestroyModelMixin,
                        viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, IsStaffPermission,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('notice',)
    ordering_fields = ('is_topped', 'create_time')
    ordering = ('-is_topped', '-create_time')

    def sub_perform_create(self, serializer):
        serializer.save(
            create_user=self.request.user,
            last_edit_user=self.request.user,
        )
        return True

    def sub_perform_update(self, serializer):
        serializer.save(
            last_edit_time=timezone.now(),
            last_edit_user=self.request.user,
        )
        return True

    @list_route(methods=['patch'], )
    def batch_top(self, request):
        ids = self.shift_data.getlist('ids', int)
        if not ids:
            return Response(status=status.HTTP_204_NO_CONTENT)

        is_topped = self.shift_data.get('is_topped', int)

        queryset = self.queryset.filter(id__in=ids)
        if self.perform_batch_top(queryset, is_topped):
            self.clear_cache()

        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_batch_top(self, queryset, is_topped):
        if queryset.update(is_topped=is_topped) > 0:
            return True
        return False


class EventNoticeViewSet(BaseNoticeViewSet):
    queryset = event_models.EventNotice.objects.all()
    serializer_class = mserializers.EventNoticeSerializer

    def init_type_queryset(self):
        self.queryset = self.queryset.filter(event__type=self.event_type)

    def get_queryset(self):
        queryset = common.get_user_event_related_queryset(self.request.user, self.queryset)

        event = self.query_data.get('event', int)
        if event:
            queryset = queryset.filter(event=event)

        return queryset


class EventTaskNoticeViewSet(BaseNoticeViewSet):
    queryset = event_models.EventTaskNotice.objects.all()
    serializer_class = mserializers.EventTaskNoticeSerializer

    def init_type_queryset(self):
        self.queryset = self.queryset.filter(event_task__event__type=self.event_type)

    def get_queryset(self):
        queryset = common.get_user_event_task_related_queryset(self.request.user, self.queryset)

        event = self.query_data.get('event', int)
        if event:
            queryset = queryset.filter(event_task__event=event)

        event_task = self.query_data.get('event_task', int)
        if event_task:
            queryset = queryset.filter(event_task=event_task)

        return queryset
