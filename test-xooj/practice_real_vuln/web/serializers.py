# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import serializers

from common_env.models import Env
from common_framework.utils.rest.serializers import is_en
from practice.base_serializers import BaseTaskSerializer
from practice.models import PracticeSubmitSolved
from practice_real_vuln.models import RealVulnTask, RealVulnCategory


class RealVulnCategorySerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = RealVulnCategory
        fields = ('id', 'cn_name', 'en_name', 'name')

    def get_name(self, obj):
        if is_en(self):
            return obj.en_name
        else:
            return obj.cn_name


class RealVulnTaskSerializer(BaseTaskSerializer):
    official_writeup = serializers.SerializerMethodField()

    class Meta:
        model = RealVulnTask
        fields = (
            'title_dsc', 'event_name', 'file_url', 'content', 'public_official_writeup', 'official_writeup', 'category',
            'hash', 'score', 'is_dynamic_env', 'url', 'difficulty_rating', 'title', 'identifier', 'category_name',
            'lock', 'event', 'markdown', 'solving_mode', 'score_multiple', 'has_flag', 'category_cn_en_names')

    def get_official_writeup(self, obj):
        if obj.public_official_writeup:
            return obj.official_writeup
        else:
            return None

    def get_has_flag(self, obj):
        if obj.is_dynamic_env:
            task_env = obj.envs.filter(env__status=Env.Status.TEMPLATE).first()
            if task_env.is_dynamic_flag:
                return True
            elif not obj.answer:
                return False
        elif not obj.answer:
            return False
        return True
