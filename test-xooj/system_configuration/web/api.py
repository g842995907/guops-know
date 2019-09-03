# -*- coding: utf-8 -*-
from django.db.models import Q
from rest_framework import viewsets, filters, permissions, status
from rest_framework.decorators import list_route, detail_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common_auth.models import User
from common_framework.utils.constant import Status
from common_framework.utils.rest.mixins import CacheModelMixin, RequestDataMixin
from system_configuration.constant import GroupType
from system_configuration.models import SystemConfiguration, SysNotice, UserNotice
from . import serializers as m_serializers


class SystemConfigurationViewSet(CacheModelMixin, viewsets.ReadOnlyModelViewSet):
    queryset = SystemConfiguration.objects.all()
    serializer_class = m_serializers.SystemConfigurationSerializer
    permission_classes = (permissions.AllowAny,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)


class SysNoticeViewSet(CacheModelMixin, viewsets.ReadOnlyModelViewSet):
    queryset = SysNotice.objects.filter(status=Status.NORMAL)
    serializer_class = m_serializers.SysNoticeSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    ordering_fields = ('create_time',)
    ordering = ('-create_time',)

    def get_queryset(self):
        queryset = self.queryset
        user = self.request.user

        if user.is_superuser:
            queryset = queryset.exclude(Q(group=3) & ~Q(notified_person=user))
        if user.is_staff and not user.is_superuser:
            queryset = queryset.filter(Q(group=GroupType.ALL) | Q(group=GroupType.TEACHER) | Q(notified_person=user))
        if not user.is_staff:
            if user.classes:
                queryset = queryset.filter(
                    Q(group=GroupType.ALL) | Q(group=GroupType.STUDENT) | Q(classes=user.classes) | Q(notified_person=user))
            else:
                queryset = queryset.filter(Q(group=GroupType.ALL) | Q(group=GroupType.STUDENT))

        delete_ids = []
        delete_notices = UserNotice.objects.filter(Q(user=user) & Q(status=UserNotice.Status.IGNORE)).all()
        for delete_notice in delete_notices:
            delete_ids.append(delete_notice.sys_notice.id)

        queryset = queryset.exclude(id__in=delete_ids)
        return queryset


class UserNoticeViewSet(CacheModelMixin, viewsets.ModelViewSet):
    serializer_class = m_serializers.UserNoticeSerializer
    ordering = ('-id',)

    def sub_perform_create(self, serializer):
        UserNotice.objects.get_or_create(
            sys_notice=serializer.validated_data.get('sys_notice'),
            user=serializer.validated_data.get('user'),
        )
        return True

    @list_route(methods=['delete'])
    def batch_destroy(self, request):
        ids = self.request.data.getlist('ids',[])
        if not ids:
            return Response(status=status.HTTP_204_NO_CONTENT)

        user_id = self.request.user.id
        usernotice_list = []
        for id in ids:
            user_notice = UserNotice(
                sys_notice_id=id,
                user=User(user_id),
                status=UserNotice.Status.IGNORE
            )
            usernotice_list.append(user_notice)
        UserNotice.objects.bulk_create(usernotice_list)
        self.clear_cache()

        return Response(status=status.HTTP_200_OK)

