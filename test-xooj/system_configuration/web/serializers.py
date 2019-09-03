# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import gettext, ugettext
from rest_framework import serializers

from common_framework.utils.image import save_image
from django.utils.html import escape
from system_configuration.models import SystemConfiguration, SysNotice, UserNotice


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
    esc_value = serializers.SerializerMethodField()

    class Meta:
        model = SystemConfiguration
        fields = ('key', 'value', 'esc_value')

    def get_esc_value(self, obj):
        if obj.key == 'system_name' or obj.key == 'copyright':
            return escape(obj.value)
        return obj.value


class SysNoticeSerializer(serializers.ModelSerializer):
    real_group = serializers.SerializerMethodField()
    notice_type = serializers.SerializerMethodField()
    read = serializers.SerializerMethodField()
    publisher = serializers.SerializerMethodField()

    def get_read(self, obj):
        user = self.context.get("request").user
        return UserNotice.objects.filter(sys_notice=obj.id, user=user).count() > 0 and True or False

    def get_notice_type(self, obj):
        return get_notice_type()[obj.type]

    def get_real_group(self, obj):
        if obj.classes is None:
            return get_groups()[obj.group]
        else:
            return obj.classes.name

    def get_publisher(self, obj):
        if obj.type == 1 or obj.type == 2:
            return ugettext('x_system_module')
        else:
            return obj.creator.first_name or obj.creator.username

    class Meta:
        model = SysNotice
        fields = (
            'id', 'name', 'content', 'group', 'create_time', 'last_edit_time',
            'faculty', 'major', 'classes', 'real_group', 'type', 'notice_type', 'read', 'publisher'
        )


class UserNoticeSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserNotice
        fields = ('id', 'sys_notice', 'user')