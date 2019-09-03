# -*- coding: utf-8 -*-
from rest_framework import serializers

from common_framework.utils.image import save_image
from common_framework.utils.rest import serializers as common_serializers
from common_framework.utils.rest.serializers import is_en
from django.utils.translation import ugettext_lazy as _
from practice_capability import models as capability_modules
from practice_capability.constant import TestpaperType, AppType



class TestPaperSerializer(serializers.ModelSerializer,
                          common_serializers.BaseShareSerializer,
                          common_serializers.CreateUserNameAndShareSerializer):
    def to_internal_value(self, data):
        full_logo_name = data.get('logo', None)
        data._mutable = True
        if full_logo_name:
            data['logo'] = save_image(full_logo_name)
        data._mutable = False
        ret = super(TestPaperSerializer, self).to_internal_value(data)
        return ret

    class Meta:
        model = capability_modules.TestPaper
        fields = (
            'id', 'name', 'hash', 'task_number', 'task_all_score',
            'create_time', 'create_user', 'logo', 'introduction', 'status',
            'public', 'creater_username', 'is_other_share', 'share', 'share_count',
        )


class TestPaperTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = capability_modules.TestPaperTask
        fields = '__all__'


class SerializerNew:
    def __init__(self, raw, tpt, language):
        self.data = {
            'title_dsc': self.get_title(raw),
            'title': raw.title,
            'id': int(raw.id),
            'category_name': self.get_name(raw,language),
            "hash":raw.hash,
            "score": float(tpt),
            'content': raw.content if len(raw.content) != 0 else raw.title
        }

        p_type = int(raw.hash.split('.')[-1])
        if p_type != AppType.THEROY:
            self.data['question_type'] = _("x_operation_problem")
        else:
            if raw.multiple == TestpaperType.SINGLE:
                self.data['question_type'] = _("x_single_choice")
            elif raw.multiple == TestpaperType.MULTIPLE :
                self.data['question_type'] = _("x_multiple_choice")
            elif raw.multiple == TestpaperType.JUDGMENT :
                self.data['question_type'] = _("x_judgment_problem")

    def get_name(self, raw, language):
        if language != 'zh-hans':
            return raw.category.en_name
        else:
            return raw.category.cn_name

    def get_title(self,raw):
        if hasattr(raw,'multiple'):
            return raw.content
        else:
            return raw.title

class LessonCategoriesSerializer:
    def __init__(self, raw, hash):

        self.data = {
            'id': self.get_id_type(raw.id, hash),
            'name': raw.cn_name,
            'cn_name':raw.cn_name,
            'en_name': raw.en_name,
        }

    def get_id_type(self, id, hash):
        hash_type = hash.split(".")[-1]
        id_type = str(id) + "_" + hash_type
        return id_type