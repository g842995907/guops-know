# -*- coding: utf-8 -*-
from django.db import transaction
from django.utils import timezone

from common_auth.api import task_share_teacher
from common_env.models import Env

from rest_framework import filters, viewsets, status
from rest_framework.decorators import detail_route
from rest_framework.permissions import IsAuthenticated
from rest_framework import exceptions
from rest_framework.response import Response

from common_framework.utils.rest.mixins import CacheModelMixin, DestroyModelMixin, PublicModelMixin, RequestDataMixin
from common_framework.utils.rest.permission import IsStaffPermission
from practice.api import RealDestroyModelMixin, PublicWriteModelMixin

from practice_man_machine import models as man_machine_models
from practice import constant
from practice_man_machine.response import TaskResError
from practice.widgets.env.utils import remove_env_scripts

from . import serializers as mserializers


class ManMachineTaskViewSet(CacheModelMixin, RequestDataMixin, DestroyModelMixin, PublicModelMixin,
                            PublicWriteModelMixin, viewsets.ModelViewSet):
    queryset = man_machine_models.ManMachineTask.objects.all()
    serializer_class = mserializers.ManMachineTaskSerializer
    permission_classes = (IsAuthenticated, IsStaffPermission,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('title',)
    ordering_fields = ('id',)
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

    def is_ignore_share(self):
        ignore_share = self.query_data.get('ignore_share', int)
        if ignore_share:
            self.queryset = self.queryset.filter(is_copy=True)
            return True
        else:
            return False

    def sub_perform_create(self, serializer):
        if len(serializer.validated_data['title']) > 100:
            raise exceptions.ValidationError({'title': [TaskResError.TITLE_TO_LONG]})
        if man_machine_models.ManMachineTask.objects.filter(title=serializer.validated_data['title'],
                                                            event=serializer.validated_data['event']).exists():
            raise exceptions.ValidationError({'title': [TaskResError.TITLE_HAVE_EXISTED]})

        serializer.save(last_edit_user=self.request.user, create_user=self.request.user)
        return True

    def sub_perform_update(self, serializer):
        task = serializer.save(
            last_edit_time=timezone.now(),
            last_edit_user=self.request.user
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


class ManMachineCategoryViewSet(CacheModelMixin, RealDestroyModelMixin,
                                viewsets.ModelViewSet):
    queryset = man_machine_models.ManMachineCategory.objects.all()
    serializer_class = mserializers.ManMachineCategorySerializer
    permission_classes = (IsAuthenticated, IsStaffPermission,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('cn_name', 'en_name')
    ordering_fields = ('id',)
    ordering = ('id',)
