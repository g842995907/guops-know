# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from common_framework.utils.constant import Status
from course_occupation.models import OccupationSystem, OccupationLink, OccupationCourse
from course.models import Lesson


class OccupationSerializer(serializers.ModelSerializer):
    advanced_name = serializers.SerializerMethodField()
    name = serializers.CharField(validators=[UniqueValidator(queryset=OccupationSystem.objects.all())])

    class Meta:
        model = OccupationSystem
        fields = ('id', 'name', 'advanced_name', 'describe', 'difficulty', 'public', 'builtin')

    def get_advanced_name(self, obj):
        advanced_namelist = OccupationLink.objects.filter(occupation=obj.pk)
        namelist = []
        for advanced in advanced_namelist:
            namelist.append(advanced.advanced.name)
        if namelist:
            return namelist
        else:
            return '-'


class OccupationCourseSerializer(serializers.ModelSerializer):
    # 课时数
    course_count = serializers.SerializerMethodField()
    course_name = serializers.SerializerMethodField()
    course_direction = serializers.SerializerMethodField()
    course_sub_direction = serializers.SerializerMethodField()

    def get_course_count(self, obj):
        # return Lesson.objects.filter(course=obj.course).filter(status=Status.NORMAL).count()
        if hasattr(obj, 'course_count'):
            return obj.course_count
        return None

    def get_course_name(self, obj):
        return obj.course.name

    def get_course_direction(self, obj):
        if not obj.course.direction:
            return None
        try:
            language = self.context.get("request").LANGUAGE_CODE
            if language != "zh-hans":
                return obj.course.direction.en_name
        except Exception as e:
            pass
        return obj.course.direction.cn_name

    def get_course_sub_direction(self, obj):
        if not obj.course.sub_direction:
            return None
        try:
            language = self.context.get("request").LANGUAGE_CODE
            if language != "zh-hans":
                return obj.course.sub_direction.en_name
        except Exception as e:
            pass
        return obj.course.sub_direction.cn_name

    class Meta:
        model = OccupationCourse
        fields = (
            'id', 'occupation_system', 'course', 'course_direction', 'course_name', 'course_sub_direction',
            'course_count',
            'stage', 'obligatory')
