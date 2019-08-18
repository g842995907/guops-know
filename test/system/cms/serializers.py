# -*- coding: utf-8 -*-
import json

from rest_framework import serializers
from base.utils.rest.serializers import ModelSerializer

from ..models import UpgradeVersion, SystemConfiguration, OperationLog


class UpgradeVersionSerializer(ModelSerializer):
    class Meta:
        model = UpgradeVersion
        fields = '__all__'


class SystemConfigurationSerializer(ModelSerializer):
    class Meta:
        model = SystemConfiguration
        fields = '__all__'


class OperationLogSerializer(ModelSerializer):
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
        from system.utils.module import get_module_name as _get
        return _get(obj.module)

    class Meta:
        model = OperationLog
        fields = (
            'create_time', 'create_user', 'module', 'user_name',
            'operation_type', 'operation_obj', 'operation_str',
            'content', 'level',
            'log_status', 'module_name',
        )






class RunLogSerializer:
    def __init__(self, log):
        self.data = {
            'name': log.get('name'),
            'size': log.get('size'),
            'create_time': log.get('create_time'),
            'modify_time': log.get('modify_time'),
        }


class InstanceListSerializer(object):
    def __init__(self, row):
        self.data = {
            'id': row.get('id'),
            'server_name': row.get('name'),
            'server_ip': row.get('server_ip'),
            'server_status': row.get('status'),
            'create_time': row.get('create_time'),
            'node': row.get('node'),
            'create_user': row.get('create_user'),
        }
