# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import os
import shutil
import zipfile

from django.utils.translation import ugettext_lazy as _
from common_framework.utils.rest.serializers import is_en

from rest_framework import serializers, exceptions

from practice.api import PRACTICE_TYPE_REAL_VULN
from practice.base_serializers import BaseEnvTaskSerializer, EnvTaskSerializerForEditMixin

from practice_real_vuln.models import RealVulnTask, RealVulnCategory
from practice_real_vuln.response import CONSTANTTYPE
from practice_real_vuln.utils.utils import handle_markdown
from oj import settings

logger = logging.getLogger(__name__)


class RealVulnTaskSerializer(BaseEnvTaskSerializer):
    TASK_TYPE = PRACTICE_TYPE_REAL_VULN
    question_type = serializers.SerializerMethodField()

    def get_question_type(self, obj):
        return CONSTANTTYPE.OPERATION_QUESTIONS

    # def to_internal_value(self, data):
    #     pdf_file = data.get('markdown', None)
    #     data._mutable = True
    #     if pdf_file == '':
    #         data['markdown'] = None
    #     data._mutable = False
    #     if data.get('markdown', None) is not None:
    #         data._mutable = True
    #         if os.path.splitext(pdf_file.name)[1] != ".zip":
    #             raise exceptions.NotAcceptable(_('writeup_markdown_only_zip'))
    #         else:
    #             # zipfiles = zipfile.ZipFile(pdf_file, "r")
    #             extract_path = os.path.join(settings.MEDIA_ROOT, 'tmp')
    #             if not os.path.exists(extract_path):
    #                 os.mkdir(extract_path)
    #             extract_full_path = os.path.join(extract_path, 'markdownzip')
    #             if os.path.exists(extract_full_path):
    #                 shutil.rmtree(extract_full_path)
    #                 os.mkdir(extract_full_path)
    #             # zipfiles.extractall(extract_full_path)
    #             # zipfiles.close()
    #             extract_all(pdf_file, extract_full_path)
    #             data['markdown'] = handle_markdown(extract_full_path)
    #             if not data['markdown']:
    #                 # 处理zip包， 但不是markdown的问题
    #                 raise exceptions.NotAcceptable(_('x_writeup_custom_upload_x_format_not_true'))
    #
    #         data._mutable = False
    #     ret = super(RealVulnTaskSerializer, self).to_internal_value(data)
    #     return ret

    class Meta:
        model = RealVulnTask
        fields = (
            'title_dsc', 'event_name', 'content', 'category', 'score', 'hash', 'title', 'event',
            'answer', 'public', 'is_copy', 'last_edit_username', 'id', 'last_edit_time', 'file_url', 'file', 'url',
            'difficulty_rating', 'category_cn_name', 'category_name', 'is_choice_question',
            'public_official_writeup', 'official_writeup', 'builtin',
            'is_dynamic_env', 'task_env', 'identifier', 'markdown', 'solving_mode', 'score_multiple', 'flag_servers', 'question_type',
            'creater_username', 'knowledges_list')


class PracticeExerciseTaskSerializerForEdit(EnvTaskSerializerForEditMixin, RealVulnTaskSerializer):
    pass


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
