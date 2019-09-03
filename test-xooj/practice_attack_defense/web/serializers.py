# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.html import escape
from rest_framework import serializers

from common_framework.utils.rest.serializers import is_en
from practice.base_serializers import BaseTaskSerializer
from practice_attack_defense.models import PracticeAttackDefenseTask, PracticeAttackDefenseCategory


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


class PracticeAttackDefenseTaskSerializer(BaseTaskSerializer):
    class Meta:
        model = PracticeAttackDefenseTask
        fields = (
            'title_dsc', 'event_name', 'content', 'category', 'title',
            'hash', 'score', 'is_dynamic_env', 'category_name', 'event', 'public_official_writeup', 'official_writeup')

