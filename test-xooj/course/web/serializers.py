# -*- coding: utf-8 -*-
from django.utils.html import strip_tags

from rest_framework import serializers
from common_env.models import Env

from common_framework.utils.constant import Status
from course import models as course_models
from course.cms import serializers as cms_serializers


class DirectionSerializer(cms_serializers.DirectionSerializer):
    class Meta:
        model = course_models.Direction
        fields = ('cn_name', 'en_name', 'id')


class CourseSerializer(cms_serializers.CourseSerializer):
    strip_introduction = serializers.SerializerMethodField()

    def get_strip_introduction(self, obj):
        return strip_tags(obj.introduction)

    def get_count(self, obj):
        return course_models.Lesson.objects.filter(course=obj).filter(status=Status.NORMAL, public=True).count()

    def get_theory_count(self, obj):
        return course_models.Lesson.objects.filter(course=obj).filter(
            status=Status.NORMAL, public=True).filter(type=course_models.Lesson.Type.THEORY).count()

    def get_experiment_count(self, obj):
        return course_models.Lesson.objects.filter(course=obj).filter(
            status=Status.NORMAL, public=True).filter(type=course_models.Lesson.Type.EXPERIMENT).count()

    class Meta:
        model = course_models.Course
        fields = ('id', 'name', 'direction', 'sub_direction', 'logo',
                  'introduction', 'difficulty', 'hash', 'count', 'lock',
                  'auth_count', 'direction_i18n_name', 'strip_introduction',
                  'sub_direction_i18n_name', 'theory_count', 'experiment_count', 'course_writeup')


class LessonSerializer(cms_serializers.LessonSerializer):
    learning_status = serializers.SerializerMethodField()
    knowledges_list = serializers.SerializerMethodField()

    def get_knowledges_list(self, obj):
        if obj.knowledges:
            return obj.knowledges.split(',')

    def get_learning_status(self, obj):
        current_user = self.context.get("request").user
        record = course_models.Record.objects.filter(user=current_user).filter(lesson__id=obj.id)
        if record:
            record = record[0]
            return record.progress
        return 0

    class Meta:
        model = course_models.Lesson
        fields = (
            'name', 'course_name', 'course', 'type', 'attachment',
            'id', 'pdf', 'video', 'env', 'difficulty',
            'hash', 'lesson_env', 'learning_status', 'markdown', 'knowledges', 'knowledges_list',
        )


class NewLessonSerializer(serializers.ModelSerializer):
    course_name = serializers.SerializerMethodField()
    lesson_env = serializers.SerializerMethodField()
    video_logo = serializers.SerializerMethodField()
    lesson_exercise = serializers.SerializerMethodField()
    knowledges_list = serializers.SerializerMethodField()
    exercise_public = serializers.SerializerMethodField()

    def get_exercise_public(self, obj):
        if obj.exercise_public:
            return True
        return False

    def get_knowledges_list(self, obj):
        if obj.knowledges:
            return obj.knowledges.split(',')

    def get_video_logo(self, obj):
        from system_configuration.models import SystemConfiguration
        if SystemConfiguration.objects.filter(key='system_name').exists():
            system_name = SystemConfiguration.objects.filter(key='system_name').first().value
            return system_name
        return None

    def get_course_name(self, obj):
        if obj.course:
            return obj.course.name
        return None

    def get_lesson_env(self, obj):
        lesson_env = obj.envs.filter(env__status=Env.Status.TEMPLATE).first()
        if not lesson_env:
            return None
        return cms_serializers.LessonEnvSerializer(lesson_env).data

    def get_lesson_exercise(self, obj):
        lesson_exercises_count = course_models.LessonPaperTask.objects.filter(lesson=obj, type=course_models.LessonPaperTask.Type.EXERCISE).count()
        if lesson_exercises_count > 0:
            return True
        return False

    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)
        super(NewLessonSerializer, self).__init__(*args, **kwargs)

        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)

    class Meta:
        model = course_models.Lesson
        fields = '__all__'


class RecordSerializer(serializers.ModelSerializer):

    class Meta:
        model = course_models.Record
        fields = '__all__'


class LessonSerializer1(serializers.ModelSerializer):
    learning_status = serializers.SerializerMethodField()
    lesson_type = serializers.SerializerMethodField()
    study_type = serializers.SerializerMethodField()
    lesson_id = serializers.SerializerMethodField()
    testpaper_id = serializers.SerializerMethodField()

    def get_testpaper_id(self, obj):
        if obj.testpaper:
            return obj.testpaper.id
        return None

    def get_learning_status(self, obj):
        current_user = self.context.get("request").user
        record = course_models.Record.objects.filter(user=current_user).filter(lesson__id=obj.id)
        if record:
            record = record[0]
            return record.progress
        return 0

    def get_lesson_type(self, obj):
        return obj.type

    def get_study_type(self, obj):
        return obj.lesson_type

    def get_lesson_id(self, obj):
        return obj.id

    class Meta:
        model = course_models.Lesson
        fields = (
            'name', 'lesson_type','testpaper_id',
            'lesson_id', 'difficulty', 'study_type',
            'learning_status'
        )


class LessonJstreeSerializer(cms_serializers.LessonJstreeSerializer):
    lesson = LessonSerializer1()

    class Meta:
        model = course_models.LessonJstree
        fields ="__all__"


class CourseScheduleSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()

    def get_title(self, obj):
        request = self.context['request']
        user = request.user
        course_info = ''
        class_info = ''
        teacher_info = ''

        if obj.course and obj.lesson:
            course_info = [obj.course.name, obj.lesson.name]
            course_info = "/".join(course_info)

        if obj.faculty and obj.major and obj.classes:
            class_info = [obj.faculty.name, obj.major.name, obj.classes.name]
            class_info = "/".join(class_info)

        if obj.create_user:
            teacher_info = obj.create_user.first_name

        if user.is_staff:
            return course_info + '\n' + class_info
        else:
            return course_info + '\n' + teacher_info

    class Meta:
        model = course_models.CourseSchedule
        fields = ('id', 'course', 'lesson', 'start', 'end', 'faculty', 'major', 'classes', 'title', 'dow')