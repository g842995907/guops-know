# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import serializers

from common_framework.utils.rest.serializers import is_en
from practice.base_serializers import BaseTaskSerializer
from practice.models import PracticeSubmitSolved
from practice_man_machine.models import ManMachineTask, ManMachineCategory


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


class ManMachineTaskSerializer(BaseTaskSerializer):
    class Meta:
        model = ManMachineTask
        fields = (
            'title_dsc', 'event_name', 'file_url', 'content', 'public_official_writeup', 'official_writeup', 'category',
            'hash', 'score', 'is_dynamic_env', 'url', 'difficulty_rating', 'title', 'category_name', 'event')
