# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from rest_framework import serializers
from django.utils.html import escape

from practice.models import TaskEvent, PracticeSubmitSolved


class TaskEventSerializer(serializers.ModelSerializer):
    name_dsc = serializers.SerializerMethodField()
    task_count = serializers.SerializerMethodField()
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = TaskEvent
        fields = (
            'name_dsc', 'type', 'logo', 'weight', 'type', 'id', 'task_count', 'logo_url', 'lock'
        )

    def get_name_dsc(self, obj):
        return escape(obj.name)

    def get_task_count(self, obj):
        if hasattr(obj, 'task_count'):
            return obj.task_count
        return None

    def get_logo_url(self, obj):
        if obj.logo:
            return obj.logo.url
        else:
            return None


class PracticeSubmitSolvedSerializer(serializers.ModelSerializer):
    class Meta:
        model = PracticeSubmitSolved
        fields = '__all__'


# extra serializers
class PracticeRankSerializer(serializers.Serializer):
    obj_id = serializers.IntegerField()
    obj_name = serializers.CharField(max_length=2048)
    faculty_name = serializers.SerializerMethodField()
    major_name = serializers.SerializerMethodField()
    classes_name = serializers.SerializerMethodField()
    solved_count = serializers.IntegerField()
    sum_score = serializers.FloatField()

    def get_faculty_name(self, obj):
        if obj.get('faculty_name') is not None:
            return obj['faculty_name']
        else:
            return ''

    def get_major_name(self, obj):
        if obj.get('major_name') is not None:
            return obj['major_name']
        else:
            return ''

    def get_classes_name(self, obj):
        if obj.get('classes_name') is not None:
            return obj['classes_name']
        else:
            return ''
