# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import collections
import json
import os
import shutil
import zipfile

from django.db import transaction
from django.db.models import Count
from django.utils.translation import ugettext_lazy as _
from rest_framework import exceptions, serializers

from common_env.models import Env
from common_framework.utils.constant import Status
from common_framework.utils.image import save_image
from common_framework.utils.models.data import get_sub_model_data
from common_framework.utils.request import is_en as request_is_en
from common_framework.utils.rest import serializers as common_serializers
from course import models as course_models
from course.cms.response import CONSTANTTYPE
from course.utils.course_util import get_class_group_env_info, get_class_group_info, check_class_groups
from course.widgets.utils import handle_markdown_new
from oj import settings
from x_note.models import Note
from . import error

Type = course_models.Lesson.Type

class DirectionSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    def get_name(self, obj):
        if common_serializers.is_en(self):
            name = obj.en_name
        else:
            name = obj.cn_name
        return name

    class Meta:
        model = course_models.Direction
        fields = ('id', 'cn_name', 'en_name', 'status', 'name')


class SubDirectionSerializer(serializers.ModelSerializer):
    parent_name = serializers.SerializerMethodField()

    def get_parent_name(self, obj):
        if obj.parent:
            return obj.parent.cn_name
        return None

    class Meta:
        model = course_models.Direction
        fields = ('id', 'cn_name', 'en_name', 'status', 'parent', 'parent_name')


class CourseSerializer(
    common_serializers.BaseAuthAndShareSerializer,
    common_serializers.CreateUserNameAndShareSerializer,
    serializers.ModelSerializer):
    count = serializers.SerializerMethodField()
    theory_count = serializers.SerializerMethodField()
    experiment_count = serializers.SerializerMethodField()
    direction_i18n_name = serializers.SerializerMethodField()
    sub_direction_i18n_name = serializers.SerializerMethodField()
    parent_id = serializers.SerializerMethodField()
    identity_id = serializers.SerializerMethodField()

    def get_identity_id(self, obj):
        return obj.id

    def get_parent_id(self, obj):
        return None

    def get_count(self, obj):
        # return course_models.Lesson.objects.filter(course=obj).filter(status=Status.NORMAL).count()
        if hasattr(obj, 'count'):
            return obj.count
        return None

    def get_theory_count(self, obj):
        return course_models.Lesson.objects.filter(course=obj).filter(
            status=Status.NORMAL).filter(type=course_models.Lesson.Type.THEORY).count()

    def get_experiment_count(self, obj):
        return course_models.Lesson.objects.filter(course=obj).filter(
            status=Status.NORMAL).filter(type=course_models.Lesson.Type.EXPERIMENT).count()

    def get_direction_i18n_name(self, obj):
        if not obj.direction:
            return None

        try:
            language = self.context.get("request").LANGUAGE_CODE
            if language != "zh-hans":
                return obj.direction.en_name
        except Exception, e:
            pass
        return obj.direction.cn_name

    def get_sub_direction_i18n_name(self, obj):
        if not obj.sub_direction:
            return None

        try:
            language = self.context.get("request").LANGUAGE_CODE
            if language != "zh-hans":
                return obj.sub_direction.en_name
        except Exception, e:
            pass
        return obj.sub_direction.cn_name

    def to_internal_value(self, data):
        full_logo_name = data.get('logo', None)
        data._mutable = True
        if full_logo_name:
            data['logo'] = save_image(full_logo_name)
        data._mutable = False
        ret = super(CourseSerializer, self).to_internal_value(data)
        return ret

    class Meta:
        model = course_models.Course
        fields = (
            'id', 'name', 'direction', 'sub_direction',
            'logo', 'introduction', 'difficulty',
            'create_user', 'last_edit_user', 'hash', 'public',
            'create_time', 'update_time', 'theory_count',
            'experiment_count', 'count', 'lock', 'builtin',
            'direction_i18n_name', 'sub_direction_i18n_name', 'course_writeup',
            'creater_username', 'is_other_share', 'auth', 'auth_count', 'all_auth_count', 'share', 'share_count', 'parent_id', "identity_id"
        )


class LessonEnvSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()

    def get_title(self, obj):
        return obj.env.name

    class Meta:
        model = course_models.LessonEnv
        fields = ('env', 'type', 'destroy_delay', 'destroy_time', 'title')
        read_only_fields = ('destroy_time', 'title')


class LessonSerializer(serializers.ModelSerializer,
                       common_serializers.CreateUserNameAndShareSerializer,
                       common_serializers.BaseAuthAndShareSerializer):
    course_name = serializers.SerializerMethodField()
    report_count = serializers.SerializerMethodField()
    lesson_env = serializers.SerializerMethodField()
    capabili_name = serializers.SerializerMethodField()
    knowledges_list = serializers.SerializerMethodField()
    count = serializers.SerializerMethodField()
    parent_id = serializers.SerializerMethodField()
    identity_id = serializers.SerializerMethodField()
    direction_i18n_name = serializers.SerializerMethodField()
    exercise_public = serializers.SerializerMethodField()

    def get_direction_i18n_name(self, obj):
        if obj.type == Type.THEORY:
            return CONSTANTTYPE.HEORETICAL_LESSON
        elif obj.type == Type.EXPERIMENT:
            return CONSTANTTYPE.EXPERIMENT_LESSON

    def get_share_count(self, obj):
        return -1

    def get_auth_count(self, obj):
        return -1

    def get_all_auth_count(self, obj):
        return -1

    def get_identity_id(self, obj):
        return obj.id + 100000000

    def get_parent_id(self, obj):
        return obj.course_id

    def get_count(self, obj):
        return 1

    def get_knowledges_list(self, obj):
        if obj.knowledges:
            return obj.knowledges.split(',')

    def get_capabili_name(self, obj):
        if obj.testpaper:
            return obj.testpaper.id
        return None

    def get_report_count(self, obj):
        return Note.objects.filter(resource=obj.hash).filter(status=Status.NORMAL).count()

    def get_course_name(self, obj):
        if obj.course:
            return obj.course.name
        return None

    def get_lesson_env(self, obj):
        lesson_env = obj.envs.filter(env__status=Env.Status.TEMPLATE).first()
        if not lesson_env:
            return None
        return LessonEnvSerializer(lesson_env).data

    def get_exercise_public(self, obj):
        if obj.exercise_public:
            return True
        return False

    def create(self, validated_data):
        with transaction.atomic():
            lesson = super(LessonSerializer, self).create(validated_data)

            request = self.context['request']
            # 非实验课程无环境
            if validated_data.get('type') != course_models.Lesson.Type.EXPERIMENT:
                if validated_data.get('type') == course_models.Lesson.Type.PRACTICE or validated_data.get(
                        'type') == course_models.Lesson.Type.EXAM:
                    capabili_name = request.data.get('capabili_name', False)
                    if capabili_name.isdigit():
                        lesson.testpaper_id = int(capabili_name)
                        lesson.save()
                return lesson

            # 动态环境创建环境信息
            lesson_env_data = get_sub_model_data(request.data, ['lesson_env'])
            if lesson_env_data and lesson_env_data.get('env').strip():
                lesson_env_serializer = create_lesson_env(lesson, lesson_env_data)
                lesson.envs.add(lesson_env_serializer.instance)

        return lesson

    def update(self, instance, validated_data):
        with transaction.atomic():
            lesson = super(LessonSerializer, self).update(instance, validated_data)
            request = self.context['request']

            # 非实验课程无环境
            if (validated_data.get('type') is not None and validated_data.get(
                    'type') != course_models.Lesson.Type.EXPERIMENT) or \
                    (validated_data.get('type') is None and lesson.type != course_models.Lesson.Type.EXPERIMENT):
                if validated_data.get('type') == course_models.Lesson.Type.PRACTICE or validated_data.get(
                        'type') == course_models.Lesson.Type.EXAM:
                    capabili_name = request.data.get('capabili_name', False)
                    if capabili_name.isdigit():
                        lesson.testpaper_id = int(capabili_name)
                        lesson.save()
                return lesson

            # 动态环境更新环境信息
            lesson_env = instance.envs.filter(env__status=Env.Status.TEMPLATE).first()
            lesson_env_data = get_sub_model_data(request.data, ['lesson_env'])
            if lesson_env_data:
                # 更新环境信息
                if lesson_env:
                    if 'env' in lesson_env_data and not lesson_env_data['env']:
                        lesson_env_data.pop('env')
                    lesson_env_serializer = update_lesson_env(lesson_env, lesson, lesson_env_data)
                # 创建环境信息
                elif lesson_env_data.get('env').strip():
                    lesson_env_serializer = create_lesson_env(lesson, lesson_env_data)
                    lesson.envs.add(lesson_env_serializer.instance)
        return lesson

    def to_internal_value(self, data):
        pdf_file = data.get('pdf', None)
        data._mutable = True
        if pdf_file == '':
            del data['pdf']
        video_file = data.get('video', None)
        if video_file == '':
            del data['video']
        attachment = data.get('attachment', None)
        if attachment == '':
            del data['attachment']
        data._mutable = False
        if data.get('pdf', None) is not None:
            data._mutable = True
            if os.path.splitext(pdf_file.name)[1] != ".zip" and os.path.splitext(pdf_file.name)[1] != ".pdf":
                raise exceptions.NotAcceptable(_('x_only_zip_pdf'))
            if os.path.splitext(pdf_file.name)[1] == ".zip":
                # zipfiles = zipfile.ZipFile(pdf_file, "r")
                extract_path = os.path.join(settings.MEDIA_ROOT, 'tmp')
                if not os.path.exists(extract_path):
                    os.mkdir(extract_path)
                extract_full_path = os.path.join(extract_path, 'pdfzip')
                if os.path.exists(extract_full_path):
                    shutil.rmtree(extract_full_path)
                    os.mkdir(extract_full_path)
                # zipfiles.extractall(extract_full_path)
                # zipfiles.close()
                data['markdownfile'] = pdf_file
                extract_all(pdf_file, extract_full_path)
                data['pdf'] = None
                # data['markdown'] = handle_markdown(extract_full_path)
                data['markdown'] = None
                handle_markdown_data = handle_markdown_new(extract_full_path)
                if handle_markdown_data:
                    data['html'] = handle_markdown_data['html']
                    data['html_type'] = handle_markdown_data['html_type']
                else:
                    raise exceptions.ValidationError({'pdf': [error.UPLAOD_ZIP_WRONG]})
            data._mutable = False
        ret = super(LessonSerializer, self).to_internal_value(data)
        return ret

    class Meta:
        model = course_models.Lesson
        fields = (
            'name', 'course_name', 'course', 'public', 'exercise_public', 'type', 'attachment',
            'id', 'pdf', 'video', 'practice', 'homework', 'env', 'difficulty',
            'practice_name', 'homework_name', 'hash', 'report_count', 'duration',
            'status', 'create_time', 'update_time', 'order', 'lesson_env', 'markdown', 'video_state', 'markdownfile',
            "capabili_name", 'creater_username', 'create_user',
            'html_type', 'html', 'knowledges', 'knowledges_list', "count", "parent_id", "identity_id", "share_count",
            "auth_count", "all_auth_count", "direction_i18n_name", "builtin", "lesson_type"
        )


def create_lesson_env(lesson, lesson_env_data):
    lesson_env_serializer = LessonEnvSerializer(data=lesson_env_data)
    lesson_env_serializer.is_valid(raise_exception=True)
    lesson_env_validated_data = lesson_env_serializer.validated_data

    if not lesson_env_validated_data.get('env'):
        raise exceptions.ValidationError({'lesson_env__env': [error.PLEASE_SELECT_ENV]})

    if lesson_env_validated_data['env'].status != Env.Status.TEMPLATE:
        raise exceptions.ValidationError({'lesson_env__env': [error.INVALID_ENV]})
    lesson_env_serializer.save()
    return lesson_env_serializer


def update_lesson_env(lesson_env, lesson, lesson_env_data):
    lesson_env_serializer = LessonEnvSerializer(
        lesson_env,
        data=lesson_env_data,
        partial=True
    )
    lesson_env_serializer.is_valid(raise_exception=True)
    lesson_env_serializer.save()


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


class NewLessonSerializer(serializers.ModelSerializer):
    course_name = serializers.SerializerMethodField()
    lesson_env = serializers.SerializerMethodField()
    video_logo = serializers.SerializerMethodField()

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
        return LessonEnvSerializer(lesson_env).data

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


class LessonJstreeSerializer(serializers.ModelSerializer):
    type = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()
    parents = serializers.SerializerMethodField()
    lesson_type = serializers.SerializerMethodField()

    def get_parents(self, obj):
        value_list = obj.parents.split(',')
        return value_list

    def get_id(self, obj):
        return obj.self_id

    def get_type(self, obj):
        if obj.type == 2:
            return 'file'
        return 'default'

    def get_lesson_type(self, obj):
        if obj.lesson:
            return obj.lesson.type
        return None

    class Meta:
        model = course_models.LessonJstree
        fields = "__all__"


class LessonCopySerializer(serializers.ModelSerializer):
    # envs
    class Meta:
        model = course_models.Lesson
        exclude = ('id', 'course', 'create_time', 'update_time', 'envs',
                   "pdf", "html", "video", "attachment", "hash", "create_user", "markdownfile", 'video_change',
                   'video_preview', 'video_poster', 'builtin')


class CourseScheduleSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    course_name = serializers.SerializerMethodField()
    lesson_name = serializers.SerializerMethodField()
    faculty_name = serializers.SerializerMethodField()
    major_name = serializers.SerializerMethodField()
    classes_name = serializers.SerializerMethodField()

    def get_faculty_name(self, obj):
        if obj.faculty:
            return obj.faculty.name

    def get_major_name(self, obj):
        if obj.major:
            return obj.major.name

    def get_classes_name(self, obj):
        if obj.course:
            return obj.classes.name

    def get_course_name(self, obj):
        if obj.course:
            return obj.course.name

    def get_lesson_name(self, obj):
        if obj.lesson:
            return obj.lesson.name

    def get_title(self, obj):
        if obj.course and obj.lesson and obj.faculty and obj.major and obj.classes:
            course_info = [obj.course.name, obj.lesson.name]
            course_info = "/".join(course_info)
            class_info = [obj.faculty.name, obj.major.name, obj.classes.name]
            class_info = "/".join(class_info)
            return course_info + '\n' + class_info
        else:
            return error.COURSE_INFO_WRONG

    class Meta:
        model = course_models.CourseSchedule
        fields = ('id', 'course', 'lesson', 'start', 'end', 'faculty', 'major', 'classes', 'title', 'dow',
                  'course_name', 'lesson_name', 'faculty_name', 'major_name', 'classes_name')


class ClassroomGroupInfoSerializer(serializers.ModelSerializer):
    group_env_info = serializers.SerializerMethodField()

    def get_group_env_info(self, obj):
        return get_class_group_env_info(obj)

    class Meta:
        model = course_models.ClassroomGroupInfo
        fields = ('id', 'classroom', 'groups', 'group_env_info')


class ClassroomGroupTemplateSerializer(serializers.ModelSerializer):
    group_info = serializers.SerializerMethodField()

    def get_group_info(self, obj):
        info_ret = get_class_group_info(obj.classes, json.loads(obj.groups))
        if info_ret['group_changed']:
            obj.groups = json.dumps(info_ret['groups'])
            obj.save()

        return info_ret['group_infos']

    def create(self, validated_data):
        classes = validated_data['classes']
        try:
            groups = json.loads(validated_data['groups'])
            if not check_class_groups(classes, groups):
                raise exceptions.PermissionDenied()
        except Exception as e:
            raise exceptions.PermissionDenied()

        return super(ClassroomGroupTemplateSerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        if 'groups' in validated_data:
            try:
                groups = json.loads(validated_data['groups'])
                if not check_class_groups(instance.classes, groups):
                    raise exceptions.PermissionDenied()
            except Exception as e:
                raise exceptions.PermissionDenied()

        return super(ClassroomGroupTemplateSerializer, self).update(instance, validated_data)

    class Meta:
        model = course_models.ClassroomGroupTemplate
        fields = ('id', 'classes', 'name', 'groups', 'group_info')


class ScheduleSignSerializer(serializers.ModelSerializer):
    class Meta:
        model = course_models.ScheduleSign
        fields = ('id', 'sign_in', 'sign_in_time', 'need_help')


class SerializerNew:
    def __init__(self, raw, tpt):
        self.data = {
            'title': raw.title,
            'id': str(raw.id),
            'hash': str(raw.hash),
            'score': float(tpt.score),
            'content': raw.content
        }
        p_type = int(raw.hash.split('.')[-1])
        if p_type == 0:
            self.data['option'] = raw.option
            self.data['options_dsc'] = self.data['options_dsc'] = collections.OrderedDict(
                sorted(json.loads(raw.option).items(), key=lambda t: t[0]))
            self.data['multiple'] = raw.multiple


class Serializer:
    def __init__(self, raw, tpt):
        self.data = {
            'title': raw.title,
            'id': str(raw.id),
            'hash': str(raw.hash),
            'score': int(tpt.score),
            'content': raw.content
        }

        p_type = int(raw.hash.split('.')[-1])
        if p_type == 0:
            self.data['options'] = raw.option
            self.data['options_dsc'] = collections.OrderedDict(
                sorted(json.loads(raw.option).items(), key=lambda t: t[0]))
            self.data['is_choice_question'] = 1
            self.data['is_multiple_choice'] = 1 if raw.multiple else 0


class StatisticsSerializer:
    def __init__(self, statistics):
        self.data = {
            'id': statistics.get('user'),
            'report_id': statistics.get('report_id'),
            'first_name': statistics.get('user__first_name') if statistics.get('user__first_name') else statistics.get('user__username'),
            'complete_practice': statistics.get('complete_practice', 0),
            'resource': statistics.get('resource', None),
            'experiment_is_pass': statistics.get('experiment_is_pass', False),
            'experiment_mark_score': statistics.get('experiment_mark_score', 0),
            'teacher': statistics.get('teacher', None),
            'update_time': statistics.get('update_time', None)
        }
        organization = "/".join(
            [statistics.get('user__faculty__name'),
             statistics.get('user__major__name'),
             statistics.get('user__classes__name')]
            ) if not type(statistics.get('user__faculty__name')) == type(None) else None
        self.data['organization'] = organization


class ClassStatisticsSerializer:
    def __init__(self, statistics):
        self.data = {
            'id': statistics.get('user__classes'),
            'class_name': statistics.get('user__classes__name'),
            'complete_lessons': statistics.get('complete_lessons', 0),
            'complete_experiment': statistics.get('complete_experiment', 0),
            'complete_practice': statistics.get('complete_practice', 0),
            'experiment_mark_score': statistics.get('experiment_mark_score', float(0)),
        }
        organization = "/".join(
            [statistics.get('user__faculty__name'),
             statistics.get('user__major__name')
             ])
        self.data['organization'] = organization


class UserStatisticsSerializer:
    def __init__(self, statistics):
        self.data = {
            'id': statistics.get('id'),
            'first_name': statistics.get('first_name', None),
            'group_name': statistics.get('group_name', None),
            'online': statistics.get('online', None),
            'complete_lessons': statistics.get('complete_lessons', 0),
            'complete_experiment': statistics.get('complete_experiment', 0),
            'complete_practice': statistics.get('complete_practice', 0),
            'experiment_mark_score': statistics.get('experiment_mark_score', float(0)),
        }
        organization = "/".join(
            [statistics.get('faculty__name'),
             statistics.get('major__name'),
             statistics.get('classes__name')
             ]) if not type(statistics.get('faculty__name')) == type(None) else None
        self.data['organization'] = organization


class CourseStatisticsSerializer:
    def __init__(self, row, request=None):

        direction_i18n_name = row.get('direction__cn_name')
        if request and request_is_en(request):
            direction_i18n_name = row.get('direction__en_name')

        self.data = {
            'id': row.get('id'),
            'name': row.get('name'),
            'direction_i18n_name': direction_i18n_name,
            'difficulty': row.get('difficulty'),
            'count': row.get('count'),
            'lesson_study_count': 0 if row.get('count') == 0 else course_models.Record.objects.filter(
                                    lesson__course_id=row['id']).values('user_id').annotate(Count('user_id')).count(),
            'report_learn_count': row.get('report_learn_count', 0),
            'creater_username': row.get('create_user__first_name'),
            'identity_id': int(row.get('id')),
            'parent_id': None,
            'expand': False
        }


class LessonStatisticsSerializer:
    def __init__(self, statistics):
        self.data = {
            'id': statistics.get('id'),
            'name': statistics.get('name'),
            'course': statistics.get('course_id'),
            'direction_i18n_name': self.get_direction_i18n_name(statistics),
            'difficulty': statistics.get('difficulty', 0),
            'count': statistics.get('count', 1),
            'lesson_study_count': statistics.get('lesson_study_count', 0),
            'report_learn_count': statistics.get('report_learn_count', 0),
            'creater_username': statistics.get('create_user__first_name'),
            'share_count': statistics.get('share_count', -1),
            'auth_count': statistics.get('auth_count', -1),
            'identity_id': int(statistics.get('id')) + 100000000,
            'parent_id': int(statistics.get('course_id')),
            'is_lesson': True
        }

    def get_direction_i18n_name(self, obj):
        if obj['type'] == Type.THEORY:
            return CONSTANTTYPE.HEORETICAL_LESSON
        elif obj['type'] == Type.EXPERIMENT:
            return CONSTANTTYPE.EXPERIMENT_LESSON


class SingleClassStatisticsSerializer:
    def __init__(self, statistics):
        self.data = {
            'name': statistics.get('user__first_name', None),
            'complete_lessons': statistics.get('learned_count', 0),
            'complete_experiment': statistics.get('note_count', 0),
            'experiment_mark_score': statistics.get('average_score', float(0)),
        }


class StatisticsDetailSerializer:
    def __init__(self, statistics):
        self.data = {
            'user_id': statistics.get('user_id'),
            'first_name': statistics.get('user__first_name'),
            'lesson_name': statistics.get('lesson__name', None),
            'experiment_report': statistics.get('experiment_report', 0),
            'experiment_mark_score': statistics.get('experiment_mark_score', 0),
            'mark_score_teacher': statistics.get('teacher', None),
            'update_time': statistics.get('update_time', None),
            'lesson_type': statistics.get('lesson__type') if statistics.get(
                'lesson__type') == course_models.Lesson.Type.EXPERIMENT else None,
            'lesson_hash': statistics.get('lesson__hash', None)
        }
        if statistics.get('note', None):
            note = statistics.get('note')
            self.data['experiment_mark_score'] = note.get('score')
            self.data['update_time'] = str(note.get('update_time'))
            self.data['mark_score_teacher'] = note.get('teacher_name')
            self.data['ispass'] = note.get('ispass')


class ClassesRoomReportSerializer:
    def __init__(self, obj):
        self.data = {
            'first_name': obj.get('first_name'),
            'id': obj.get('id'),
            'experiment_mark_score': obj.get('experiment_mark_score', 0),
            'mark_score_teacher': obj.get('teacher', None),
            'update_time': obj.get('update_time', None),
            'ispass': obj.get('ispass', None),
        }
        if obj.get('note', None):
            note = obj.get('note')
            self.data['experiment_mark_score'] = note.get('score')
            self.data['update_time'] = str(note.get('update_time'))
            self.data['mark_score_teacher'] = note.get('teacher_name')
            self.data['ispass'] = note.get('ispass')
            self.data['resource'] = note.get('resource')

        organization = "/".join(
            [obj.get('faculty__name'),
             obj.get('major__name'),
             obj.get('classes__name')])
        self.data['organization'] = organization


class ClassesScheduleMonitorSerializer:
    def __init__(self, obj):
        organization = "/".join(
            [obj.get('faculty__name'),
             obj.get('major__name'),
             obj.get('classes__name')])
        self.data = {
            'first_name': obj.get('first_name'),
            'user_id': obj.get('id'),
            'organization': organization,
            'assistance_link': obj.get('assistance_link', None)
        }

        if obj.get('sign_obj', None):
            sign_obj = obj.get('sign_obj')
            self.data['sign_in'] = sign_obj.get('sign_in')
            self.data['need_help'] = sign_obj.get('need_help')
            self.data['sign_in_time'] = sign_obj.get('sign_in_time')
