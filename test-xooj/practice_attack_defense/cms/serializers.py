# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from common_framework.utils.rest.serializers import is_en
from practice.api import PRACTICE_TYPE_ATTACK_DEFENSE
from practice.base_serializers import BaseEnvTaskSerializer, EnvTaskSerializerForEditMixin
from practice_attack_defense.models import PracticeAttackDefenseTask, PracticeAttackDefenseCategory

logger = logging.getLogger(__name__)


class PracticeAttackDefenseTaskSerializer(BaseEnvTaskSerializer):
    TASK_TYPE = PRACTICE_TYPE_ATTACK_DEFENSE
    
    class Meta:
        model = PracticeAttackDefenseTask
        fields = (
            'title_dsc', 'event_name', 'content', 'category', 'score', 'hash', 'title', 'event',
            'answer', 'public', 'is_copy', 'last_edit_username', 'id', 'last_edit_time', 'file_url', 'file', 'url',
            'difficulty_rating', 'category_cn_name', 'category_name',
            'public_official_writeup', 'official_writeup', 'is_choice_question', 'builtin',
            'is_dynamic_env', 'task_env', 'creater_username', 'knowledges_list')
        extra_kwargs = {
            'title': {
                'validators': [UniqueValidator(queryset=PracticeAttackDefenseTask.objects.all())]
            }
        }


class PracticeAttackDefenseTaskSerializerForEdit(EnvTaskSerializerForEditMixin, PracticeAttackDefenseTaskSerializer):
    pass


class PracticeAttackDefenseCategorySerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = PracticeAttackDefenseCategory
        fields = ('id', 'cn_name', 'en_name', 'name')

    def get_name(self, obj):
        if is_en(self):
            return obj.en_name
        else:
            return obj.cn_name
