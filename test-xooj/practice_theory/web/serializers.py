# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
import collections
import json

from rest_framework import serializers
from django.utils.html import escape

from common_framework.utils.rest.serializers import is_en
from practice.models import PracticeSubmitSolved
from practice_theory.models import ChoiceTask, ChoiceCategory
from lxml.html.clean import clean_html


class ChoiceTaskSerializer(serializers.ModelSerializer):
    title_dsc = serializers.SerializerMethodField()
    event_name = serializers.SerializerMethodField()
    options_dsc = serializers.SerializerMethodField()
    event_id = serializers.SerializerMethodField()
    difficulty_rating = serializers.SerializerMethodField()
    category_name = serializers.SerializerMethodField()

    class Meta:
        model = ChoiceTask
        fields = (
            'title_dsc', 'event_name', 'content', 'options_dsc', 'multiple', 'category', 'score', 'hash',
            'answer', 'public', 'id', 'event_id', 'difficulty_rating', 'title', 'category_name')

    def get_title_dsc(self, obj):
        if obj.title:
            return escape(obj.title)

    def get_event_name(self, obj):
        return obj.event.name

    def get_event_id(self, obj):
        return obj.event.id

    def get_options_dsc(self, obj):
        if obj.option:
            return collections.OrderedDict(sorted(json.loads(obj.option).items(), key=lambda t: t[0]))
        else:
            return None

    def get_difficulty_rating(self, obj):
        return None

    def get_category_name(self, obj):
        try:
            language = self.context.get('request').LANGUAGE_CODE
            if language != 'zh-hans':
                return obj.category.en_name
        except Exception, e:
            pass
        return obj.category.cn_name


class ChoiceCategorySerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = ChoiceCategory
        fields = ('id', 'cn_name', 'en_name', 'name')

    def get_name(self, obj):
        if is_en(self):
            return obj.en_name
        else:
            return obj.cn_name
