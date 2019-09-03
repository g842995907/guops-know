# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import os
import shutil
import zipfile

from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers, exceptions

from common_framework.utils.rest.serializers import is_en

from practice.api import PRACTICE_TYPE_INFILTRATION
from practice.base_serializers import BaseEnvTaskSerializer, EnvTaskSerializerForEditMixin

from practice_infiltration.models import PracticeInfiltrationTask, PracticeInfiltrationCategory
from practice_infiltration.response import CONSTANTTYPE
from practice_infiltration.utils.utils import handle_markdown

from oj import settings

logger = logging.getLogger(__name__)


class PracticeInfiltrationTaskSerializer(BaseEnvTaskSerializer):
    TASK_TYPE = PRACTICE_TYPE_INFILTRATION
    question_type = serializers.SerializerMethodField()

    def get_question_type(self, obj):
        return CONSTANTTYPE.OPERATION_QUESTIONS

    class Meta:
        model = PracticeInfiltrationTask
        fields = (
            'title_dsc', 'event_name', 'content', 'category', 'score', 'hash', 'title', 'event',
            'answer', 'public', 'is_copy', 'last_edit_username', 'id', 'last_edit_time', 'file_url', 'file', 'url',
            'difficulty_rating', 'category_cn_name', 'category_name',
            'public_official_writeup', 'official_writeup', 'is_choice_question', 'builtin',
            'is_dynamic_env', 'task_env', 'markdown', 'solving_mode', 'score_multiple', 'flag_servers',
            'question_type', 'creater_username', 'knowledges_list')


class PracticeInfiltrationTaskSerializerForEdit(EnvTaskSerializerForEditMixin, PracticeInfiltrationTaskSerializer):
    pass


class PracticeInfiltrationCategorySerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = PracticeInfiltrationCategory
        fields = ('id', 'cn_name', 'en_name', 'name')

    def get_name(self, obj):
        if is_en(self):
            return obj.en_name
        else:
            return obj.cn_name


def extract_all(zip_filename, extract_dir, filename_encoding='GBK'):
    zf = zipfile.ZipFile(zip_filename, 'r')
    for file_info in zf.infolist():
        filename = unicode(str(file_info.filename), filename_encoding).encode("utf-8")
        if not filename.endswith('/'):
            output_filename = os.path.join(extract_dir, filename)
            output_file_dir = os.path.dirname(output_filename)
            if not os.path.exists(output_file_dir):
                os.makedirs(output_file_dir)
            with open(output_filename, 'wb') as output_file:
                shutil.copyfileobj(zf.open(file_info.filename), output_file)
    zf.close()
