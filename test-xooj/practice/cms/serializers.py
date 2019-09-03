# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.html import escape
from rest_framework import serializers

from common_framework.utils.image import save_image
from common_framework.utils.rest import serializers as common_serializers
from practice.models import TaskEvent


class TaskEventSerializer(serializers.ModelSerializer,
                          common_serializers.BaseAuthAndShareSerializer,
                          common_serializers.CreateUserNameAndShareSerializer):
    name_dsc = serializers.SerializerMethodField()
    last_edit_username = serializers.SerializerMethodField()
    task_count = serializers.SerializerMethodField()
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = TaskEvent
        fields = (
            'id', 'name_dsc', 'last_edit_username', 'type', 'logo', 'name', 'logo_url', 'auth',
            'weight', 'create_user', 'type', 'public', 'auth_count', 'task_count', 'builtin',
            'creater_username', 'is_other_share', 'auth', 'auth_count', 'all_auth_count', 'share', 'share_count',
        )

    def get_name_dsc(self, obj):
        return escape(obj.name)

    def get_last_edit_username(self, obj):
        if obj.last_edit_user:
            return obj.last_edit_user.username
        else:
            return None

    def get_task_count(self, obj):
        if hasattr(obj, 'task_count'):
            return obj.task_count
        return None

    def get_logo_url(self, obj):
        if obj.logo:
            return obj.logo.url
        else:
            return None

    def to_internal_value(self, data):
        full_logo_name = data.get('logo', None)
        data._mutable = True

        if full_logo_name:
            logofile = save_image(full_logo_name)
            data['logo'] = logofile
        data._mutable = False
        ret = super(TaskEventSerializer, self).to_internal_value(data)
        return ret
