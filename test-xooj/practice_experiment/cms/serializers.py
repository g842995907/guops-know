# -*- coding: utf-8 -*-
from rest_framework import serializers

from practice_experiment import models as experiment_models
from common_auth.serializers import ClassesSerializer
from common_framework.utils.constant import Status
from common_framework.utils.image import save_image


class DirectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = experiment_models.Direction
        fields = ('cn_name', 'en_name', 'update_time', 'create_time', 'id')


class ExperimentSerializer(serializers.ModelSerializer):
    direction_cn_name = serializers.SerializerMethodField()
    direction_en_name = serializers.SerializerMethodField()
    direction_i18n_name = serializers.SerializerMethodField()
    auth_count = serializers.SerializerMethodField()
    auth_classes = ClassesSerializer(many=True, read_only=True)

    def get_direction_cn_name(self, obj):
        return obj.direction.cn_name

    def get_direction_en_name(self, obj):
        return obj.direction.en_name

    def get_direction_i18n_name(self, obj):
        try:
            language = self.context.get("request").LANGUAGE_CODE
            if language != "zh-hans":
                return obj.direction.en_name
        except Exception, e:
            pass
        return obj.direction.cn_name

    def get_auth_count(self, obj):
        return len(obj.auth_classes.all())

    def to_internal_value(self, data):
        full_logo_name = data.get('logo', None)
        data._mutable = True
        if full_logo_name:
            data['logo'] = save_image(full_logo_name)
        data._mutable = False
        ret = super(ExperimentSerializer, self).to_internal_value(data)
        return ret

    class Meta:
        model = experiment_models.Experiment
        fields = ('name', 'auth_count', 'hash', 'create_time', 'practice',
                  'update_time', 'last_edit_user', 'pdf', 'video', 'practice_name',
                  'id', 'direction_cn_name', 'direction_en_name', 'direction',
                  'public', 'creater', 'direction_i18n_name',
                  'introduction', 'logo', 'difficulty', 'auth_classes')

