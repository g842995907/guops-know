# -*- coding: utf-8 -*-

from rest_framework import serializers
from common_framework.utils.constant import Status

from course_occupation import models as course_occupation_models


class OccupationSystemSerializer(serializers.ModelSerializer):
    label = serializers.SerializerMethodField()
    occupation_to = serializers.SerializerMethodField()

    def get_label(self, obj):
        return obj.name

    def get_occupation_to(self, obj):
        return obj.occupation.all().values('advanced')

    class Meta:
        model = course_occupation_models.OccupationSystem
        fields = ('id', 'label', 'describe', 'occupation_to')


class OccupationIsChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = course_occupation_models.OccupationIsChoice
        fields = ('id', 'user', 'occupation')
