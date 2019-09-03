# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import serializers
from django.utils.html import escape

from common_framework.utils.rest.serializers import is_en
from practice.base_serializers import BaseTaskSerializer
from practice.models import PracticeSubmitSolved
from practice_exercise.models import PracticeExerciseTask, PracticeExerciseCategory


class PracticeExerciseCategorySerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = PracticeExerciseCategory
        fields = ('id', 'cn_name', 'en_name', 'name')

    def get_name(self, obj):
        if is_en(self):
            return obj.en_name
        else:
            return obj.cn_name


class PracticeExerciseTaskSerializer(BaseTaskSerializer):
    official_writeup = serializers.SerializerMethodField()

    class Meta:
        model = PracticeExerciseTask
        fields = (
            'title_dsc', 'event_name', 'file_url', 'content', 'public_official_writeup', 'official_writeup', 'category',
            'hash', 'score', 'is_dynamic_env', 'url', 'difficulty_rating', 'title', 'category_name', 'lock', 'event',
            'markdown', 'solving_mode', 'score_multiple', 'has_flag', 'category_cn_en_names')

    def get_official_writeup(self, obj):
        if obj.public_official_writeup:
            return obj.official_writeup
        else:
            return None
