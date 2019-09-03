# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json

from rest_framework import serializers

from django.utils.translation import gettext
from common_framework.utils.image import save_image
from system_configuration.models import SystemConfiguration, Backup, SysLog, OperationLog, SysNotice, UserAction
from system_configuration.utils.backup import get_last_migrate_time


def get_groups():
    groups = [
        gettext('x_all_user'),
        gettext('x_teacher_group'),
        gettext('x_student_group'),
        gettext('x_choose_class'),
    ]
    return groups


def get_notice_type():
    notice_type = [
        gettext('x_sys_notice'),
        gettext('x_sys_message'),
        gettext('x_team_message'),
        gettext('x_schedule_message'),
        gettext('x_event_message'),
        gettext('x_user_message'),
    ]
    return notice_type


class SystemConfigurationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemConfiguration
        fields = ('key', 'value', 'id')

    def to_internal_value(self, data):
        full_logo_name = data.get('logo', None)
        data._mutable = True

        if full_logo_name:
            logofile = save_image(full_logo_name)
            data['logo'] = logofile
        data._mutable = False
        ret = super(SystemConfigurationSerializer, self).to_internal_value(data)
        return ret


class BackupSerializer(serializers.ModelSerializer):
    creater_username = serializers.SerializerMethodField()
    can_load = serializers.SerializerMethodField()

    class Meta:
        model = Backup
        fields = ('create_time', 'backup_name', 'id', 'status', 'creater_username', 'can_load')

    def get_creater_username(self, obj):
        if obj.create_user:
            return obj.create_user.first_name
        else:
            return None

    def get_can_load(self, obj):
        migration_time = get_last_migrate_time()
        if obj.migrate_time is None:
            return False
        if migration_time > obj.migrate_time:
            return False
        return True


class RunLogSerializer:
    def __init__(self, log):
        self.data = {
            # 'id': log.get('name'),
            'name': log.get('name'),
            'size': log.get('size'),
            'create_time': log.get('create_time'),
            'modify_time': log.get('modify_time'),
        }


class SysLogSerializer(serializers.ModelSerializer):
    create_username = serializers.SerializerMethodField()

    def get_create_username(self, obj):
        if obj.create_user:
            return obj.create_user.first_name if obj.create_user.first_name else obj.create_user.username
        else:
            return None

    class Meta:
        model = SysLog
        fields = (
            'create_username',
            'create_time',
            'title', 'content',
            'log_status',
        )


class OperationLogSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()
    module_name = serializers.SerializerMethodField()

    def get_content(self, obj):
        try:
            return json.loads(obj.content)
        except Exception as e:
            return None

    def get_user_name(self, obj):
        return obj.create_user.first_name

    def get_module_name(self, obj):
        from common_product.module import get_module_name as _get
        return _get(obj.module)

    class Meta:
        model = OperationLog
        fields = (
            'create_time', 'create_user', 'module', 'user_name',
            'operation_type', 'operation_obj', 'operation_str',
            'content', 'level',
            'log_status', 'module_name',
        )


class SysNoticeSerializer(serializers.ModelSerializer):
    real_group = serializers.SerializerMethodField()
    notice_type = serializers.SerializerMethodField()
    creator_username = serializers.SerializerMethodField()
    faculty_name = serializers.SerializerMethodField()
    major_name = serializers.SerializerMethodField()
    classes_name = serializers.SerializerMethodField()

    def get_faculty_name(self, obj):
        if obj.faculty:
            return obj.faculty.name
        else:
            return None

    def get_major_name(self, obj):
        if obj.major:
            return obj.major.name
        else:
            return None

    def get_classes_name(self, obj):
        if obj.classes:
            return obj.classes.name
        else:
            return None

    def get_creator_username(self, obj):
        if obj.creator:
            return obj.creator.first_name or obj.creator.username
        else:
            return None

    def get_notice_type(self, obj):
        return get_notice_type()[obj.type]

    def get_real_group(self, obj):
        if obj.classes is None:
            return get_groups()[obj.group]
        else:
            return None

    class Meta:
        model = SysNotice
        fields = (
            'id', 'name', 'content', 'group', 'create_time', 'last_edit_time',
            'faculty', 'major', 'classes', 'real_group', 'notice_type', 'creator_username','faculty_name',
            'major_name', 'classes_name'
        )


class UserActionSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()

    def get_username(self, obj):
        return obj.user.first_name or obj.create_user.username

    class Meta:
        model = UserAction
        fields = (
            'id', 'time', 'user', 'content', 'username'
        )