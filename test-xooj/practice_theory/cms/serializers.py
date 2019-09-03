# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
import collections
import json
from lxml.html.clean import clean_html
from rest_framework import serializers
from django.utils.html import escape

from common_framework.utils.rest.serializers import is_en
from practice.base_serializers import BasePracticeSameSerializer
from practice_theory.constant import TheoryResError, CONSTANTTYPE
from practice_theory.models import ChoiceTask, ChoiceCategory
from rest_framework import exceptions


class ChoiceTaskSerializer(BasePracticeSameSerializer,
                           serializers.ModelSerializer):
    title_dsc = serializers.SerializerMethodField()
    event_name = serializers.SerializerMethodField()
    is_choice_question = serializers.SerializerMethodField()
    question_type = serializers.SerializerMethodField()
    options_dsc = serializers.SerializerMethodField()

    def get_options_dsc(self, obj):
        if obj.option:
            return collections.OrderedDict(sorted(json.loads(obj.option).items(), key=lambda t: t[0]))
        else:
            return None

    class Meta:
        model = ChoiceTask
        fields = (
            'title_dsc', 'event_name', 'content', 'option', 'multiple', 'category', 'score', 'hash', 'title', 'event',
            'answer', 'public', 'is_copy', 'last_edit_username', 'id', 'last_edit_time', 'multiple', 'category_cn_name', 'builtin',
            'category_name', 'is_choice_question','question_type','creater_username', 'options_dsc', 'knowledges_list', 'difficulty_rating')

    def get_question_type(self, obj):
        if obj.multiple == 1:
            return CONSTANTTYPE.MULTIPLE_CHOICE_QUESTION
        elif obj.multiple == 0:
            return CONSTANTTYPE.SINGLE_CHOICE_QUESTION
        elif obj.multiple == 2:
            return CONSTANTTYPE.JUDGMENT_CHOICE_QUESTION

    def get_title_dsc(self, obj):
        if obj.title:
            title = re.sub('&nbsp;', '', obj.title)
            title = escape(title)
        else:
            try:
                dr = re.compile(r'<[^>]+>', re.S)
                title = dr.sub('', obj.content)
                title = re.sub('&nbsp;', '', title)
                # if len(title) > 15:
                #     title = title[:15] + '...'
                # else:
                #     title = title[:15]
            except:
                title = None
        return title

    def get_event_name(self, obj):
        return obj.event.name

    def get_is_choice_question(self, obj):
        return True

    def to_internal_value(self, data):
        if len(data.get("option")) > 1024:
            raise exceptions.ValidationError({"option":TheoryResError.LENFTH_TOO_LONG})
        ret = super(ChoiceTaskSerializer, self).to_internal_value(data)
        return ret


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
