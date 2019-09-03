# -*- coding: utf-8 -*-
import logging
import os

from django.conf import settings
from django.core.cache import cache
from django.utils.translation import ugettext_lazy as _
from rest_framework import status, exceptions
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework import viewsets, permissions, filters

from base_auth.utils.rest.permissions import IsAdmin
from base.utils import license
from base.utils.rest.mixins import CacheModelMixin, PMixin, DestroyModelMixin

from system.utils import logset
from system.utils.list_view import list_view
from system.utils.module import get_all_module
from system.utils.system_logo import save_system_logo, delete_origin_logo
from system.models import SystemConfiguration, OperationLog
from system.cms import serializers as m_serializers
from system.models import UpgradeVersion
from system.cms.serializers import UpgradeVersionSerializer, RunLogSerializer

logger = logging.getLogger(__name__)


class UpgradeVersionViewSet(DestroyModelMixin, CacheModelMixin, PMixin, viewsets.ModelViewSet):
    queryset = UpgradeVersion.objects.all()
    serializer_class = UpgradeVersionSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    ordering_fields = ('create_time',)
    ordering = ('-create_time',)


class SystemConfigurationViewSet(CacheModelMixin, viewsets.GenericViewSet):
    permission_classes = (IsAuthenticated, IsAdmin,)
    serializer_class = m_serializers.SystemConfigurationSerializer

    def list(self, request, *args, **kwargs):
        context = {
            'system_name': license.get_system_config('system_name') or '',
            'copyright': license.get_system_config('copyright') or '',
            'person_env_count': license.get_system_config('person_env_count') or '',
            'public_register': license.get_system_config('public_register') or '',
            'audit': license.get_system_config('audit') or '',
            'version': license.get_system_config('version') or license.get_version("system"),
            'answer_prefix': license.get_system_config('answer_prefix') or '',
        }

        logo = license.get_system_config('logo')
        if logo:
            system_logo_path = os.path.join(settings.MEDIA_URL, 'system_logo')
            context['logo'] = os.path.join(system_logo_path, logo)
        else:
            context['logo'] = ''
        return Response(data=context)

    @action(methods=['post'], detail=False)
    def batch_update(self, request):
        system_name = request.data.get('system_name')
        if system_name:
            if system_name.__len__() > 30:
                raise exceptions.ValidationError({'system_name': [_("x_length_30")]})
            else:
                self._deal_db_update(key='system_name', value=system_name)

        copyright = request.data.get('copyright')
        if copyright is not None:
            self._deal_db_update(key='copyright', value=copyright)

        answer_prefix = request.data.get('answer_prefix')
        if answer_prefix is not None:
            self._deal_db_update(key='answer_prefix', value=answer_prefix)

        public_register = request.data.get('public_register')
        if public_register and public_register in [0, 1]:
            self._deal_db_update(key='public_register', value=public_register)

        audit = request.data.get('audit')
        if audit and audit in [0, 1]:
            self._deal_db_update(key='audit', value=audit)

        logo = request.data.get('logo')
        if logo:
            filename = save_system_logo(logo)
            if SystemConfiguration.objects.filter(key='logo').exists():
                configuration = SystemConfiguration.objects.filter(key='logo').first()
                system_logo_path = os.path.join(settings.MEDIA_ROOT, 'system_logo')
                full_file_name = os.path.join(system_logo_path, configuration.value)
                delete_origin_logo(full_file_name)
                configuration.value = filename
                configuration.save()
            else:
                SystemConfiguration.objects.create(
                    key='logo',
                    value=filename,
                )

        person_env_count = request.data.get('person_env_count')
        if person_env_count is not None:
            if person_env_count:
                all_env_sc = SystemConfiguration.objects.filter(key='all_env_count')
                if all_env_sc.exists():
                    if int(person_env_count) > int(all_env_sc.first().value):
                        raise exceptions.ValidationError({'person_env_count': [_("x_not_exceed_max")]})
                self._deal_db_update(key='person_env_count', value=person_env_count)

            elif person_env_count == '':
                self._deal_db_update(key='person_env_count', value=person_env_count)

        system_cache_list = ["person_env_count", "logo", "audit", "public_register", "system_name",
                             "copyright", "answer_prefix"]
        for cache_name in system_cache_list:
            cache.delete("_t_system_%s" % cache_name)

        return Response(status=status.HTTP_201_CREATED)

    @staticmethod
    def _deal_db_update(key, value):
        if SystemConfiguration.objects.filter(key=key).exists():
            configuration = SystemConfiguration.objects.filter(key=key).first()
            configuration.value = value
            configuration.save()
        else:
            SystemConfiguration.objects.create(
                key=key,
                value=value,
            )


class RunLogViewSet(PMixin, GenericViewSet):
    permission_classes = (IsAuthenticated, IsAdmin,)
    serializer_class = RunLogSerializer

    def list(self, request, *args, **kwargs):
        logs = logset.get_log_file_list()
        return list_view(request, logs, RunLogSerializer)

    @action(methods=['POST'], detail=False)
    def update_db(self, request):
        log_level = self.shift_data.get('log_level', int)
        log_size = self.shift_data.get('log_size', int)
        log_count = self.shift_data.get('log_count', int)

        log_dict = {'log_level': log_level, 'log_size': log_size, 'log_count': log_count}
        # redis发布
        from redis import StrictRedis
        # redis = StrictRedis(password=settings.REDIS_PASS)
        redis = StrictRedis() # 本地环境
        redis.publish("setLogLevel", log_dict)

        _log_level = SystemConfiguration.objects.filter(key='log_level').first()
        _log_size = SystemConfiguration.objects.filter(key='log_size').first()
        _log_count = SystemConfiguration.objects.filter(key='log_count').first()

        def _tmp_fun(_db_o, value, key):
            if _db_o:
                _db_o.value = value
                _db_o.save()
            else:
                SystemConfiguration.objects.create(
                    key=key,
                    value=value,
                )

        _tmp_fun(_log_level, log_level, 'log_level')
        _tmp_fun(_log_size, log_size, 'log_size')
        _tmp_fun(_log_count, log_count, 'log_count')

        DEL_PATH = os.path.join(settings.BASE_DIR, 'log')
        DEL_FILES = os.listdir(DEL_PATH)
        for file in DEL_FILES:
            if 'oj.log' in file:
                file = DEL_PATH + '/' + file
                with open(file, 'w') as t:
                    t.truncate()

        return Response(status=status.HTTP_201_CREATED)

class OperationLogViewSet(CacheModelMixin, PMixin , viewsets.ModelViewSet):
    queryset = OperationLog.objects.all()
    serializer_class = m_serializers.OperationLogSerializer
    permission_classes = (IsAuthenticated, IsAdmin,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('content', 'create_user__first_name')
    ordering_fields = ('id',)
    ordering = ('-id',)

    def get_queryset(self):
        queryset = self.queryset
        _module = self.query_data.get('module', int)
        if _module is not None:
            queryset = queryset.filter(module=_module)

        # _level = self.query_data.get('level', OperationLog.SyslogLevel.values())
        # if _level is not None:
        #     queryset = queryset.filter(level=_level)

        _status = self.query_data.get('status', OperationLog.LogStatus.values())
        if _status is not None:
            queryset = queryset.filter(log_status=_status)

        return queryset

    @action(methods=['GET'], detail=False)
    def module(self,request):
        context = get_all_module()
        return Response(context)