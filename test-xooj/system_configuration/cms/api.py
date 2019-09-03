# -*- coding: utf-8 -*-
import logging
import os
import threading
import time

from django.db.models import QuerySet
from django.core.cache import cache
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from rest_framework import viewsets, filters, status, exceptions, response
from rest_framework.decorators import list_route, detail_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from common_framework.utils.request import is_en
from common_framework.utils.rest.list_view import list_view
from common_framework.utils.rest.mixins import CacheModelMixin, RequestDataMixin, DestroyModelMixin
from common_framework.utils.rest.permission import IsStaffPermission
from common_framework.utils.constant import Status
from oj import settings
from oj.config import ORGANIZATION_EN, ORGANIZATION_CN
from system_configuration.cms.serializers import RunLogSerializer
from system_configuration.models import SystemConfiguration, Backup, SysLog, OperationLog, SysNotice, UserAction, \
    UserNotice
from common_auth.models import Faculty, Major, Classes
from system_configuration.utils.backup import dump_sql, load_sql, get_last_migrate_time, dir_backup, dir_recover
from system_configuration.utils.captcha import rest_captcha_val
from system_configuration.utils.init_database import init_database
from system_configuration.utils.loger import logset
from system_configuration.utils.system_logo import save_system_logo, delete_origin_logo
from system_configuration.constant import GroupType, NoticeType
from . import serializers as m_serializers
from system_configuration import constant
from system_configuration.response import SysNoticeError

logger = logging.getLogger(__name__)


class SystemConfigurationViewSet(CacheModelMixin, RequestDataMixin, viewsets.ModelViewSet):
    queryset = SystemConfiguration.objects.all()
    serializer_class = m_serializers.SystemConfigurationSerializer
    permission_classes = (IsAuthenticated, IsStaffPermission,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('name',)
    ordering_fields = ('id',)
    ordering = ('-id',)

    @list_route(methods=['post'], )
    def batch_update(self, request):
        system_name = request.POST.get('system_name')
        if system_name:
            if system_name == '':
                raise exceptions.ValidationError({'system_name': [_("x_required_field")]})
            elif system_name.__len__() > 30:
                raise exceptions.ValidationError({'system_name': [_("x_length_30")]})
            else:
                if SystemConfiguration.objects.filter(key='system_name').exists():
                    configuration = SystemConfiguration.objects.filter(key='system_name').first()
                    configuration.value = system_name
                    configuration.save()
                else:
                    SystemConfiguration.objects.create(
                        key='system_name',
                        value=system_name,
                    )
        copyright = request.POST.get('copyright')
        if copyright or copyright == '':
            if SystemConfiguration.objects.filter(key='copyright').exists():
                configuration = SystemConfiguration.objects.filter(key='copyright').first()
                configuration.value = copyright
                configuration.save()
            else:
                SystemConfiguration.objects.create(
                    key='copyright',
                    value=copyright,
                )
        answer_prefix = request.POST.get('answer_prefix')
        if answer_prefix or answer_prefix == '':
            if SystemConfiguration.objects.filter(key='answer_prefix').exists():
                configuration = SystemConfiguration.objects.filter(key='answer_prefix').first()
                configuration.value = answer_prefix
                configuration.save()
            else:
                SystemConfiguration.objects.create(
                    key='answer_prefix',
                    value=answer_prefix,
                )
        logo = request.POST.get('logo')
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

        organization = request.POST.get('organization')
        if organization:
            s_c = SystemConfiguration.objects.filter(key='organization')
            if s_c.exists():
                s_c = s_c.first()
                s_c.value = organization
                s_c.save()
            else:
                SystemConfiguration.objects.create(
                    key='organization',
                    value=organization,
                )

        person_env_count = request.POST.get('person_env_count')
        if person_env_count or person_env_count == '':
            if person_env_count:
                all_env_sc = SystemConfiguration.objects.filter(key='all_env_count')
                if all_env_sc.exists():
                    if int(person_env_count) > int(all_env_sc.first().value):
                        raise exceptions.ValidationError({'person_env_count': [_("x_not_exceed_max")]})
                if SystemConfiguration.objects.filter(key='person_env_count').exists():
                    configuration = SystemConfiguration.objects.filter(key='person_env_count').first()
                    configuration.value = person_env_count
                    configuration.save()
                else:
                    SystemConfiguration.objects.create(
                        key='person_env_count',
                        value=person_env_count,
                    )
            elif person_env_count == '':
                if SystemConfiguration.objects.filter(key='person_env_count').exists():
                    configuration = SystemConfiguration.objects.filter(key='person_env_count').first()
                    configuration.value = person_env_count
                    configuration.save()
                else:
                    SystemConfiguration.objects.create(
                        key='person_env_count',
                        value=person_env_count,
                    )

        public_register = request.POST.get('public_register')
        if public_register:
            if SystemConfiguration.objects.filter(key='public_register').exists():
                configuration = SystemConfiguration.objects.filter(key='public_register').first()
                configuration.value = public_register
                configuration.save()
            else:
                SystemConfiguration.objects.create(
                    key='public_register',
                    value=public_register,
                )
        audit = request.POST.get('audit')
        if audit:
            if SystemConfiguration.objects.filter(key='audit').exists():
                configuration = SystemConfiguration.objects.filter(key='audit').first()
                configuration.value = audit
                configuration.save()
            else:
                SystemConfiguration.objects.create(
                    key='audit',
                    value=audit,
                )

        try:
            desktop_transmission_quality = request.POST.get('desktop_transmission_quality')
        except:
            desktop_transmission_quality = None
        if desktop_transmission_quality and desktop_transmission_quality in SystemConfiguration.DesktopTransmissionQuality.values():
            if SystemConfiguration.objects.filter(key='desktop_transmission_quality').exists():
                configuration = SystemConfiguration.objects.filter(key='desktop_transmission_quality').first()
                configuration.value = desktop_transmission_quality
                configuration.save()
            else:
                SystemConfiguration.objects.create(
                    key='desktop_transmission_quality',
                    value=desktop_transmission_quality,
                )
        self.clear_cache()

        return Response(status=status.HTTP_204_NO_CONTENT)


class BackupViewSet(CacheModelMixin, RequestDataMixin, viewsets.ModelViewSet):
    queryset = Backup.objects.all()
    permission_classes = (IsAuthenticated, IsStaffPermission,)
    serializer_class = m_serializers.BackupSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('name',)
    ordering_fields = ('id',)
    ordering = ('-id',)

    def get_queryset(self):
        queryset = self.queryset.filter(status=Backup.Status.DONE)
        return queryset

    def sub_perform_create(self, serializer):
        logger.info('create start')
        logger.info(timezone.now())
        if not os.path.exists(settings.BACKUP_ROOT):
            os.mkdir(settings.BACKUP_ROOT)
        backup_name = '%s.json' % (hex(int(time.time())))
        path = os.path.join(settings.BACKUP_ROOT, backup_name)
        migration_time = get_last_migrate_time()
        backup = serializer.save(
            creater=self.request.user,
            backup_name=path,
            status=Backup.Status.CREATING,
            migrate_time=migration_time
        )
        logger.info('thread start')
        logger.info(timezone.now())
        THREAD = threading.Thread(target=dump_sql, args=(backup.id,))
        THREAD.start()
        logger.info('thread end')
        logger.info(timezone.now())
        PDF_THREAD = threading.Thread(target=dir_backup, args=(backup.id,))
        PDF_THREAD.start()
        return True

    @detail_route(methods=['post'], )
    def recover(self, request, pk):
        try:
            backup = Backup.objects.get(pk=pk)
        except:
            raise exceptions.NotFound(u'备份不存在')
        migration_time = get_last_migrate_time()
        if backup.migrate_time is None:
            raise exceptions.ValidationError(u"数据库已升级,不能恢复备份")
        if migration_time > backup.migrate_time:
            raise exceptions.ValidationError(u"数据库已升级,不能恢复备份")
        backup.load_status = Backup.LoadStatus.CREATING
        backup.save()
        THREAD = threading.Thread(target=load_sql, args=(pk,))
        THREAD.start()
        PDF_THREAD = threading.Thread(target=dir_recover, args=(backup.id,))
        PDF_THREAD.start()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @list_route(methods=['get'], )
    def query_state(self, request):
        backup = self.queryset.order_by("-create_time").first()
        return Response({"status": backup.status}, status=status.HTTP_200_OK)

    @detail_route(methods=['get'], )
    def query_load_state(self, request, pk):
        try:
            backup = Backup.objects.get(pk=pk)
        except:
            raise exceptions.NotFound(u'备份不存在')
        if backup.load_status == Backup.LoadStatus.DONE:
            cache.clear()
        return Response({"status": backup.load_status}, status=status.HTTP_200_OK)

    @list_route(methods=['delete'], )
    def batch_destroy(self, request):
        ids = request.data.getlist('ids', [])
        if not ids:
            return Response(status=status.HTTP_204_NO_CONTENT)

        queryset = self.queryset.filter(id__in=ids)
        if hasattr(self, 'clear_cache') and self.perform_batch_destroy(queryset):
            self.clear_cache()

        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_batch_destroy(self, queryset):
        for backup in queryset:
            backup.status = Backup.Status.DELETED
            if os.path.exists(backup.backup_name):
                os.remove(backup.backup_name)
            backup_pre = hex(int(time.mktime(backup.create_time.timetuple())))
            for path in settings.BACKUP_DIRS:
                zip_path = '%s_%s.zip' % (path, str(backup_pre))
                if os.path.exists(os.path.join(settings.MEDIA_ROOT, zip_path)):
                    os.remove(os.path.join(settings.MEDIA_ROOT, zip_path))
            backup.save()
        return True


class FactoryResetViewSet(RequestDataMixin, viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated, IsStaffPermission,)

    @list_route(methods=['post'], )
    def factory_reset(self, request):
        rest_captcha_val(request)
        init_database()
        cache.clear()
        return Response(status=status.HTTP_204_NO_CONTENT)


class RunLogViewSet(RequestDataMixin, GenericViewSet):
    permission_classes = (IsAuthenticated, IsStaffPermission,)

    @list_route(methods=['get', 'post'])
    def django_list_log(self, request):
        if request.method == 'GET':
            logs = logset.get_log_file_list()
            return list_view(request, logs, RunLogSerializer)

        elif request.method == 'POST':
            log_level = self.shift_data.get('log_level', int)
            log_size = self.shift_data.get('log_size', int)
            log_count = self.shift_data.get('log_count', int)

            logset.set_loging_param(log_level, log_size, log_count)

            self.update_db(log_level, log_size, log_count)
            # self.update_db()

            return response.Response({'action': 'ok'})

    def update_db(self, log_level, log_size, log_count):

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


class SystemLogViewSet(RequestDataMixin, CacheModelMixin, viewsets.ModelViewSet):
    queryset = SysLog.objects.all()
    serializer_class = m_serializers.SysLogSerializer
    permission_classes = (IsAuthenticated, IsStaffPermission,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('content', 'create_user__first_name')
    ordering_fields = ('id',)
    ordering = ('-id',)

    def get_queryset(self):
        queryset = self.queryset

        # _level = self.query_data.get('level', OperationLog.SyslogLevel.values())
        # if _level is not None:
        #     queryset = queryset.filter(level=_level)

        _status = self.query_data.get('status', OperationLog.LogStatus.values())
        if _status is not None:
            queryset = queryset.filter(log_status=_status)

        return queryset

    # def sub_perform_create(self, serializer):
    #     serializer.save(
    #         create_user=self.request.user,
    #     )


class OperationLogViewSet(RequestDataMixin, CacheModelMixin, viewsets.ModelViewSet):
    queryset = OperationLog.objects.all()
    serializer_class = m_serializers.OperationLogSerializer
    permission_classes = (IsAuthenticated, IsStaffPermission,)
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


class SysNoticeViewSet(RequestDataMixin, CacheModelMixin, DestroyModelMixin, viewsets.ModelViewSet):
    queryset = SysNotice.objects.filter(Q(status=Status.NORMAL) & Q(type=NoticeType.SYSNOTICE))
    serializer_class = m_serializers.SysNoticeSerializer
    permission_classes = (IsAuthenticated,)
    ordering = ('-id',)

    def get_queryset(self):
        # self.clear_cache()
        queryset = self.queryset
        user = self.request.user

        if user.is_staff and not user.is_superuser:
            queryset = queryset.filter(Q(group=GroupType.ALL) | Q(group=GroupType.TEACHER))
        if not user.is_staff:
            if user.classes:
                queryset = queryset.filter(
                    Q(group=GroupType.ALL) | Q(group=GroupType.STUDENT) | Q(classes=user.classes))
            else:
                queryset = queryset.filter(Q(group=GroupType.ALL) | Q(group=GroupType.STUDENT))

        return queryset

    def sub_perform_create(self, serializer):
        if is_en(self.request):
            ORGANIZATION = ORGANIZATION_EN
        else:
            ORGANIZATION = ORGANIZATION_CN
        if serializer.validated_data.get('group') == 3:
            if serializer.validated_data.get('faculty') is None:
                raise exceptions.ValidationError(SysNoticeError.PLEASE_SELECT_FORMAT.format(ORGANIZATION['Second_level']))
            if serializer.validated_data.get('major') is None:
                raise exceptions.ValidationError(SysNoticeError.PLEASE_SELECT_FORMAT.format(ORGANIZATION['Third_level']))
            if serializer.validated_data.get('classes') is None:
                raise exceptions.ValidationError(SysNoticeError.PLEASE_SELECT_FORMAT.format(ORGANIZATION['Fourth_level']))

        if serializer.validated_data.get('name') is None:
            raise exceptions.ValidationError(SysNoticeError.LOST_TITLE)

        if serializer.validated_data.get('content') is None:
            raise exceptions.ValidationError(SysNoticeError.LOST_CONTENT)

        if len(serializer.validated_data.get('content')) > 100:
            raise exceptions.ValidationError(SysNoticeError.CONTENTLT100)

        if SysNotice.objects.filter(name=serializer.validated_data.get('name')).exists():
            raise exceptions.ValidationError(SysNoticeError.NAME_HAVE_EXISTED)
        else:
            serializer.save(
                creator=self.request.user,
            )
        return True

    def sub_perform_update(self, serializer):
        if is_en(self.request):
            ORGANIZATION = ORGANIZATION_EN
        else:
            ORGANIZATION = ORGANIZATION_CN
        faculty = Faculty(self.request.data.get("faculty"))
        major = Major(self.request.data.get("major"))
        classes = Classes(self.request.data.get("classes"))

        if serializer.validated_data.get('group') == 3:
            if serializer.validated_data.get('faculty') is None:
                raise exceptions.ValidationError(SysNoticeError.PLEASE_SELECT_FORMAT.format(ORGANIZATION['Second_level']))
            if serializer.validated_data.get('major') is None:
                raise exceptions.ValidationError(SysNoticeError.PLEASE_SELECT_FORMAT.format(ORGANIZATION['Third_level']))
            if serializer.validated_data.get('classes') is None:
                raise exceptions.ValidationError(SysNoticeError.PLEASE_SELECT_FORMAT.format(ORGANIZATION['Fourth_level']))

        if serializer.validated_data.get('group') is not 3:
            faculty = None
            major = None
            classes = None

        if serializer.validated_data.get('name'):
            if SysNotice.objects.filter(name=serializer.validated_data.get('name')):
                raise exceptions.ValidationError(SysNoticeError.NAME_HAVE_EXISTED)

        serializer.save(
            faculty=faculty,
            major=major,
            classes=classes
        )

        # 更新后将已读的消息状态重置为未读
        read_notice = UserNotice.objects.filter(sys_notice_id=self.get_object().id, status=UserNotice.Status.READ)
        read_notice.update(status=UserNotice.Status.DELETE)

        return True

    def sub_perform_destroy(self, instance):
        instance.status = Status.DELETE
        instance.save()
        return True


def add_sys_log(user, title, content, log_status=SysLog.LogStatus.SUCCESS, level=SysLog.SyslogLevel.INFO):
    SysLog.objects.create(
        create_user=user,
        title=title,
        content=content,
        level=level,
        log_status=log_status,
    )

    related_cache_class = (
        'system_configuration.cms.api.SystemLogViewSet',
    )

    CacheModelMixin.clear_cls_cache(related_cache_class)


def add_operate_log(user, module_id, content, operation_obj, operation_str,
                    operation_type=OperationLog.OType.CREATE,
                    log_status=OperationLog.LogStatus.SUCCESS,
                    level=OperationLog.SyslogLevel.INFO):
    OperationLog.objects.create(
        create_user=user,
        content=content,
        level=level,
        log_status=log_status,

        module=module_id,
        operation_obj=operation_obj,
        operation_type=operation_type,
        operation_str=operation_str,
    )

    related_cache_class = (
        'system_configuration.cms.api.OperationLogViewSet',
    )

    CacheModelMixin.clear_cls_cache(related_cache_class)


def add_sys_notice(user, name, content, group=SysNotice.Group.SELECT, classes=None,
                   notified_person=None, type=SysNotice.Type.SYSMESSAGE):

    if isinstance(notified_person, QuerySet):
        # 批量创建
        notified_person_list = []
        for notifie_user in notified_person:
            temp_sysnotice = SysNotice(
                creator=user,
                name=name,
                content=content,
                group=group,
                classes=classes,
                notified_person=notifie_user,
                type=type,
            )
            notified_person_list.append(temp_sysnotice)

        SysNotice.objects.bulk_create(notified_person_list)
    else:
        SysNotice.objects.create(
            creator=user,
            name=name,
            content=content,
            group=group,
            classes=classes,
            notified_person=notified_person,
            type=type,
        )


class UserActionViewSet(CacheModelMixin, RequestDataMixin, viewsets.ReadOnlyModelViewSet):
    queryset = UserAction.objects.all()
    permission_classes = (IsAuthenticated, IsStaffPermission,)
    serializer_class = m_serializers.UserActionSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('user__username', 'user__first_name', 'content',)
    ordering_fields = ('time',)
    ordering = ('-time',)

    def get_queryset(self):
        queryset = self.queryset

        user_id = self.query_data.get('user', int)
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        return queryset
