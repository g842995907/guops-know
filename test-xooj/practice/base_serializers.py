# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import json

from django.db import transaction
from django.utils.html import escape

from rest_framework import exceptions, serializers

from common_framework.utils.models.data import get_sub_model_data

from common_env.models import Env
from common_framework.utils.rest.serializers import BaseCreateNameSerializer
from common_web.x_markdown import md_to_html
from practice.api import PRACTICE_TYPE_REAL_VULN

from practice.base_models import SolvedBaseTask, TaskEnv
from practice.response import TaskResError
from practice.utils.task import generate_task_hash, get_type_by_hash

logger = logging.getLogger(__name__)


class TaskEnvSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskEnv
        fields = ('env', 'type', 'is_dynamic_flag', 'flag_count', 'flags', 'destroy_delay', 'destroy_time')
        read_only_fields = ('flags', 'check_script', 'attack_script', 'destroy_time')


class TaskEnvForShowSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()

    def get_title(self, obj):
        return obj.env.name

    class Meta:
        model = TaskEnv
        fields = ('title', 'env', 'type', 'is_dynamic_flag', 'flag_count', 'destroy_delay')
        read_only_fields = ('title', 'env', 'type', 'is_dynamic_flag', 'flag_count', 'destroy_delay')


class BasePracticeSameSerializer(BaseCreateNameSerializer):
    category_name = serializers.SerializerMethodField()
    category_cn_name = serializers.SerializerMethodField()
    last_edit_username = serializers.SerializerMethodField()
    knowledges_list = serializers.SerializerMethodField()
    is_choice_question = serializers.SerializerMethodField()
    category_cn_en_names = serializers.SerializerMethodField()

    def get_is_choice_question(self, obj):
        return False

    def get_knowledges_list(self, obj):
        if obj.knowledges:
            return obj.knowledges.split(",")

    def get_category_name(self, obj):
        try:
            language = self.context.get('request').LANGUAGE_CODE
            if language != 'zh-hans':
                return obj.category.en_name
        except Exception, e:
            pass
        return obj.category.cn_name

    def get_category_cn_en_names(self, obj):
        if obj.category:
            return dict(
                cn_name=obj.category.cn_name,
                en_name=obj.category.en_name
            )
        return dict(
                cn_name=None,
                en_name=None
            )

    def get_category_cn_name(self, obj):
        try:
            language = self.context.get('request').LANGUAGE_CODE
            if language != 'zh-hans':
                return obj.category.en_name
        except Exception, e:
            pass
        return obj.category.cn_name

    def get_last_edit_username(self, obj):
        if obj.last_edit_user:
            return obj.last_edit_user.username
        else:
            return None


class BaseTaskSerializer(BasePracticeSameSerializer,
                         serializers.ModelSerializer):
    title_dsc = serializers.SerializerMethodField()
    event_name = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    has_flag = serializers.SerializerMethodField()

    class Meta:
        model = SolvedBaseTask
        fields = '__all__'

    def get_has_flag(self, obj):
        return True

    def get_title_dsc(self, obj):
        return escape(obj.title)

    def get_title(self, obj):
        return escape(obj.title)

    def get_event_name(self, obj):
        return escape(obj.event.name)

    def get_file_url(self, obj):
        if obj.file:
            file_attach = {
                'name': obj.file.name,
                'url': obj.file.url,
            }
        else:
            file_attach = None

        return file_attach


class BaseEnvTaskSerializer(BaseTaskSerializer):
    task_env = serializers.SerializerMethodField()

    def get_task_env(self, obj):
        if not obj.is_dynamic_env:
            return None
        task_env = obj.envs.filter(env__status=Env.Status.TEMPLATE).first()
        if not task_env:
            return None

        return TaskEnvForShowSerializer(task_env).data

    def create(self, validated_data):
        with transaction.atomic():
            task = super(BaseEnvTaskSerializer, self).create(validated_data)
            taskhash = generate_task_hash(type=self.TASK_TYPE)
            task.hash = taskhash
            task.save()

            # 非动态环境只创建题目
            if not validated_data.get('is_dynamic_env'):
                return task

            # 动态环境创建环境信息
            request = self.context['request']
            task_env_data = get_sub_model_data(request.data, ['task_env'])
            if task_env_data:
                task_env_serializer = create_task_env(task, task_env_data)
                task.envs.add(task_env_serializer.instance)
            else:
                raise exceptions.ValidationError({'task_env__env': [TaskResError.NO_TASK_ENV]})

        return task

    def update(self, instance, validated_data):
        with transaction.atomic():
            task = super(BaseEnvTaskSerializer, self).update(instance, validated_data)
            # 非动态环境只更新题目
            if validated_data.get('is_dynamic_env') is False or \
                (validated_data.get('is_dynamic_env') is None and task.is_dynamic_env is False):
                return task

            # 动态环境更新环境信息
            request = self.context['request']
            task_env = instance.envs.filter(env__status=Env.Status.TEMPLATE).first()
            task_env_data = get_sub_model_data(request.data, ['task_env'])
            if task_env_data:
                # 更新环境信息
                if task_env:
                    task_env_serializer = update_task_env(task_env, task, task_env_data)
                # 创建环境信息
                else:
                    task_env_serializer = create_task_env(task, task_env_data)
                    task.envs.add(task_env_serializer.instance)
            else:
                if not task_env:
                    raise exceptions.ValidationError({'task_env__env': [TaskResError.NO_TASK_ENV]})
        return task
    class Meta:
        model = SolvedBaseTask
        fields = '__all__'


def create_task_env(task, task_env_data):
    task_env_serializer = TaskEnvSerializer(data=task_env_data)
    task_env_serializer.is_valid(raise_exception=True)
    task_env_validated_data = task_env_serializer.validated_data

    if not task_env_validated_data.get('env'):
        raise exceptions.ValidationError({'task_env__env': [TaskResError.PLEASE_SELECT_ENV]})

    if task_env_validated_data['env'].status != Env.Status.TEMPLATE:
        raise exceptions.ValidationError({'task_env__env': [TaskResError.INVALID_ENV]})

    # 非动态flag从answer读取
    if not task_env_validated_data.get('is_dynamic_flag'):
        answer = task.answer
        if not answer:
            # 真实漏洞静态flag可以为空
            p_type = get_type_by_hash(task.hash)
            if p_type != PRACTICE_TYPE_REAL_VULN:
                raise exceptions.ValidationError({'answer': [TaskResError.NO_FLAGS]})
        flags = answer.split('|')
        task_env_validated_data['flags'] = flags
        task_env_validated_data['flag_count'] = len(flags)
    task_env_serializer.save()
    return task_env_serializer


def update_task_env(task_env, task, task_env_data):
    task_env_serializer = TaskEnvSerializer(
        task_env,
        data=task_env_data,
        partial=True
    )
    task_env_serializer.is_valid(raise_exception=True)
    task_env_validated_data = task_env_serializer.validated_data
    # 非动态flag从answer读取
    if task_env_validated_data.get('is_dynamic_flag') is False or \
        (task_env_validated_data.get('is_dynamic_flag') is None and task_env.is_dynamic_flag is False):
        answer = task.answer
        # 更新静态flag
        if not answer:
            raise exceptions.ValidationError({'answer': [TaskResError.NO_FLAGS]})
        flags = answer.split('|')
        task_env_validated_data['flags'] = json.dumps(flags)
        task_env_validated_data['flag_count'] = len(flags)
    task_env_serializer.save()


class EnvTaskSerializerForEditMixin(object):
    def get_task_env(self, obj):
        # 非动态环境也要获取用于更新
        task_env = obj.envs.filter(env__status=Env.Status.TEMPLATE).first()
        if not task_env:
            return None

        return TaskEnvForShowSerializer(task_env).data

