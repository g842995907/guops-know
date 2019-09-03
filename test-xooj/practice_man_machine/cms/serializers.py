# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from rest_framework import serializers

from common_framework.utils.rest.serializers import is_en

from practice.api import PRACTICE_TYPE_MAN_MACHINE
from practice.base_serializers import BaseEnvTaskSerializer, EnvTaskSerializerForEditMixin

from practice_man_machine.models import ManMachineTask, ManMachineCategory

logger = logging.getLogger(__name__)


class ManMachineTaskSerializer(BaseEnvTaskSerializer):
    TASK_TYPE = PRACTICE_TYPE_MAN_MACHINE

    class Meta:
        model = ManMachineTask
        fields = (
            'title_dsc', 'event_name', 'content', 'category', 'score', 'hash', 'title', 'event',
            'answer', 'public', 'is_copy', 'last_edit_username', 'id', 'last_edit_time', 'file_url', 'file', 'url',
            'difficulty_rating', 'category_cn_name', 'category_name', 'is_choice_question',
            'public_official_writeup', 'official_writeup',
            'is_dynamic_env', 'task_env')


class PracticeExerciseTaskSerializerForEdit(EnvTaskSerializerForEditMixin, ManMachineTaskSerializer):
    pass


class ManMachineCategorySerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = ManMachineCategory
        fields = ('id', 'cn_name', 'en_name', 'name')

    def get_name(self, obj):
        if is_en(self):
            return obj.en_name
        else:
            return obj.cn_name
