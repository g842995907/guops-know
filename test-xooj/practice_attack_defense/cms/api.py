# -*- coding: utf-8 -*-
import re
from django.utils import timezone
from rest_framework import exceptions
from rest_framework import filters, status, viewsets
from rest_framework.decorators import detail_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common_auth.api import task_share_teacher
from common_env.models import Env
from common_framework.utils.constant import Status
from common_framework.utils.rest import filter as common_filters
from common_framework.utils.rest.mixins import CacheModelMixin, DestroyModelMixin, PublicModelMixin, RequestDataMixin
from common_framework.utils.rest.permission import IsStaffPermission
from practice import constant
from practice.api import PublicWriteModelMixin
from practice.constant import TaskStatus
from practice.widgets.env.utils import remove_env_scripts
from practice_attack_defense import models as attack_defense_models
from practice_attack_defense.response import TaskResError, TaskCategoryError
from . import serializers as mserializers


class PracticeAttackDefenseTaskViewSet(CacheModelMixin, DestroyModelMixin, RequestDataMixin, PublicModelMixin,
                                       PublicWriteModelMixin, viewsets.ModelViewSet):
    queryset = attack_defense_models.PracticeAttackDefenseTask.objects.all()
    serializer_class = mserializers.PracticeAttackDefenseTaskSerializer
    permission_classes = (IsAuthenticated, IsStaffPermission,)
    filter_backends = (filters.SearchFilter, common_filters.BootstrapOrderFilter)
    search_fields = ('title',)
    ordering_fields = ('id', 'last_edit_time', 'public', 'title', 'public_official_writeup')
    ordering = ('-id',)

    @task_share_teacher
    def get_queryset(self):
        queryset = self.queryset
        is_copy = self.query_data.get('is_copy', int)
        if is_copy is not None:
            queryset = queryset.filter(is_copy=is_copy)
        event_id = self.query_data.get('event', int)
        if event_id:
            queryset = queryset.filter(event_id=event_id)
        category = self.query_data.get('category')
        if category:
            queryset = queryset.filter(category=category)
        return queryset

    def sub_perform_create(self, serializer):
        knowledges = None
        if self.request.data.getlist('knowledges'):
            knowledges = self.request.data.getlist('knowledges', [])
            knowledges = [x for x in knowledges if x != '']
            knowledges = ",".join(knowledges)
        if len(serializer.validated_data['title']) > 100:
            raise exceptions.ValidationError({'title': [TaskResError.TITLE_TO_LONG]})
        if not re.search(u'^[_a-zA-Z0-9\u4e00-\u9fa5]+$',serializer.validated_data['title']):
            raise exceptions.ValidationError({'title': [TaskResError.NAME_CONVENYIONS]})
        if attack_defense_models.PracticeAttackDefenseTask.objects.filter(
                title=serializer.validated_data['title'],
                status=TaskStatus.NORMAL,
                is_copy=False,
                event=serializer.validated_data['event'],
                ).exists():
            raise exceptions.ValidationError({'title': [TaskResError.TITLE_HAVE_EXISTED]})

        serializer.save(last_edit_user=self.request.user, create_user=self.request.user, knowledges=knowledges,)
        return True

    def sub_perform_update(self, serializer):
        knowledges = None
        if not re.search(u'^[_a-zA-Z0-9\u4e00-\u9fa5]+$',serializer.validated_data['title']):
            raise exceptions.ValidationError({'title': [TaskResError.NAME_CONVENYIONS]})
        if self.request.data.getlist('knowledges'):
            knowledges = self.request.data.getlist('knowledges', [])
            knowledges = [x for x in knowledges if x != '']
            knowledges = ",".join(knowledges)
        task = serializer.save(
            last_edit_time=timezone.now(),
            last_edit_user=self.request.user,
            knowledges=knowledges,
        )
        return True

    def sub_perform_destroy(self, instance):
        instance.status = constant.TaskStatus.DELETE
        instance.save()
        return True

    @detail_route(methods=['delete'])
    def delete_env_file(self, request, pk=None):
        task = self.get_object()
        task_env = task.envs.filter(env__status=Env.Status.TEMPLATE).first()
        if task_env:
            if task_env.env_file:
                task_env.env_file.delete()

            if task_env.check_script:
                remove_env_scripts(task_env.check_script)
            task.check_script = None
            task.attack_script = None
            task.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class PracticeAttackDefenseCategoryViewSet(CacheModelMixin, DestroyModelMixin,
                                           viewsets.ModelViewSet):
    queryset = attack_defense_models.PracticeAttackDefenseCategory.objects.all()
    serializer_class = mserializers.PracticeAttackDefenseCategorySerializer
    permission_classes = (IsAuthenticated, IsStaffPermission,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('cn_name', 'en_name')
    ordering_fields = ('id',)
    ordering = ('id',)

    def sub_perform_create(self, serializer):
        if attack_defense_models.PracticeAttackDefenseCategory.objects.filter(
                cn_name=serializer.validated_data['cn_name']).exists():
            raise exceptions.ValidationError({'cn_name': [TaskCategoryError.NAME_HAVE_EXISTED]})
        serializer.save()
        return True

    def perform_batch_destroy(self, queryset):
        ids = self.request.data.getlist('ids', [])
        has_normal_choiceTask = attack_defense_models.PracticeAttackDefenseTask.original_objects.filter(
            category__in=ids,
            is_copy=False,
            status=Status.NORMAL)
        if has_normal_choiceTask:
            raise exceptions.NotAcceptable(TaskResError.TYPE_USEING)
        queryset.update(status=Status.DELETE)
        return True
