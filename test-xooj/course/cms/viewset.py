# -*- coding: utf-8 -*-
import json
import logging
import os
import shutil
import uuid
from cStringIO import StringIO
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models import Avg
from django.db.models import Count
from django.db.models import ProtectedError, Q
from django.http.response import FileResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from rest_framework import exceptions
from rest_framework import filters, viewsets, status, response
from rest_framework.decorators import list_route, detail_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common_auth.api import oj_share_teacher
from common_auth.constant import GroupType
from common_auth.models import User
from common_auth.setting import api_settings as auth_api_settings
from common_auth.utils import ADMIN_GROUPS
from common_env import models as env_models
from common_env.cms.serializers import ActiveEnvSerializer
from common_env.handlers.exceptions import PoolFullException
from common_env.models import Env
from common_framework.models import AuthAndShare
from common_framework.utils import delay_task
from common_framework.utils.constant import Status
from common_framework.utils.rest import filter as common_filters
from common_framework.utils.rest import mixins as common_mixins
from common_framework.utils.rest.list_view import list_view
from common_framework.utils.rest.request import RequestData
from common_resource.setting import api_settings as resource_api_setting
from course import models as course_modules
from course.cms import serializers
from course.constant import CourseResError, ReportStatus
from course.constant import VIDEOSTATE
from course.models import CourseSchedule, ClassroomGroupInfo, ClassroomGroupTemplate
from course.utils import create_watermark, add_watermark
from course.utils.course_util import dump_course, load_course, scan_course_resource, lesson_jstree_CURD, Method_Type, \
    get_class_group_env_info, create_default_class_group_info, create_group_env, delete_group_env, \
    update_class_group_info, transfer_group_user
from course.web import viewset as web_viewsets
from course.widgets.handle_video_utils import handle_video_cut
from practice import api as practice_api
from practice.api import get_task_object
from practice_capability.models import TestPaper
from practice_capability.models import TestPaperTask
from system_configuration.cms.api import add_sys_notice
from system_configuration.models import SysNotice
from x_note.models import Note, RecordLoads
from x_note.serializers import NoteSerializer
from . import error

logger = logging.getLogger(__name__)


class DirectionViewSet(common_mixins.RequestDataMixin,
                       common_mixins.CacheModelMixin,
                       common_mixins.DestroyModelMixin,
                       viewsets.ModelViewSet):
    queryset = course_modules.Direction.objects.filter(
        status=Status.NORMAL).filter(parent__isnull=True)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.DirectionSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    ordering_fields = ('id',)
    ordering = ('-id',)
    search_fields = ('cn_name', 'en_name',)

    def sub_perform_update(self, serializer):
        if serializer.validated_data.get('cn_name') is None:
            raise exceptions.ValidationError({'cn_name': [_("x_required_field")]})
        if serializer.validated_data.get('en_name') is None:
            raise exceptions.ValidationError({'en_name': [_("x_required_field")]})
        serializer.save()
        return True

    def sub_perform_destroy(self, instance):
        if course_modules.Course.objects.filter(direction_id=instance.id).filter(status=Status.NORMAL).exists():
            raise exceptions.ValidationError({'name': _("x_be_used_notdeleted")})
        if course_modules.Direction.objects.filter(
                parent=instance.id).filter(status=Status.NORMAL).exists():
            raise exceptions.ValidationError({'name': _("x_subtype_below_current_type")})
        super(DirectionViewSet, self).sub_perform_destroy(instance)


class SubDirectionViewSet(common_mixins.RequestDataMixin,
                          common_mixins.CacheModelMixin,
                          common_mixins.DestroyModelMixin,
                          viewsets.ModelViewSet):
    queryset = course_modules.Direction.objects.filter(
        status=Status.NORMAL).filter(parent__isnull=False)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.SubDirectionSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    ordering_fields = ('id',)
    ordering = ('-id',)
    search_fields = ('cn_name', 'en_name',)

    def sub_perform_update(self, serializer):
        if serializer.validated_data.get('cn_name') is None:
            raise exceptions.ValidationError({'cn_name': [_("x_required_field")]})
        if serializer.validated_data.get('en_name') is None:
            raise exceptions.ValidationError({'en_name': [_("x_required_field")]})
        serializer.save()
        return True

    def get_queryset(self):
        queryset = self.queryset
        parent_id = self.request.query_params.get("parent_id")
        if parent_id == "":
            queryset = self.queryset.filter(parent_id=-1)
        elif parent_id:
            queryset = self.queryset.filter(parent_id=parent_id)
        return queryset

    def sub_perform_destroy(self, instance):
        if course_modules.Course.objects.filter(
                sub_direction_id=instance.id).filter(status=Status.NORMAL).exists():
            raise exceptions.ValidationError({'name': _("x_be_used_notdeleted")})
        super(SubDirectionViewSet, self).sub_perform_destroy(instance)


class CourseViewSet(
    common_mixins.RecordMixin,
    common_mixins.CacheModelMixin,
    common_mixins.PublicModelMixin,
    common_mixins.DestroyModelMixin,
    common_mixins.AuthsMixin,
    common_mixins.ShareTeachersMixin,
    viewsets.ModelViewSet):
    queryset = course_modules.Course.objects.filter(status=Status.NORMAL)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.CourseSerializer
    related_cache_class = (web_viewsets.CourseViewSet,)
    filter_backends = (filters.SearchFilter, common_filters.BootstrapOrderFilter)
    search_fields = ('name',)
    ordering_fields = ('update_time', '-update_time', 'count', 'name', 'public')
    ordering = ('lock',)

    def sub_perform_create(self, serializer):
        if serializer.validated_data.get('name') is None:
            raise exceptions.ValidationError({'name': [CourseResError.REQUIRED_FIELD]})
        elif course_modules.Course.objects.filter(name=serializer.validated_data.get('name'),
                                                  status=Status.NORMAL).exists():
            raise exceptions.ValidationError({'name': [CourseResError.COURSE_HAVE_EXISTED]})
        instance = serializer.save(
            last_edit_user=self.request.user,
            create_user=self.request.user
        )
        # 增加课时jstree根目录
        lesson_jstree_CURD(Method_Type.COURSE_CREATE, course_modules.LessonJstree, instance)

        return True

    def sub_perform_destroy(self, instance):
        course_modules.Lesson.objects.filter(course=instance).update(status=Status.DELETE)
        instance.status = Status.DELETE
        instance.save()
        return True

    def sub_perform_update(self, serializer):
        if serializer.validated_data.has_key('name'):
            if serializer.validated_data.get('name') == '':
                raise exceptions.ValidationError({'name': [CourseResError.REQUIRED_FIELD]})
            elif course_modules.Course.objects.filter(name=serializer.validated_data.get('name'),
                                                      status=Status.NORMAL).exists():
                raise exceptions.ValidationError({'name': [CourseResError.COURSE_HAVE_EXISTED]})
        if serializer.validated_data.get('public') is None:
            serializer.validated_data['public'] = False

        instance = serializer.save()
        lesson_jstree_CURD(Method_Type.COURSE_CREATE, course_modules.LessonJstree, instance)
        return True

    @oj_share_teacher
    def get_queryset(self):
        queryset = self.queryset
        data = RequestData(self.request, is_query=True)
        search_text = data.get('search_text')
        if search_text is not None:
            search_text = search_text.strip()
            lessons = course_modules.Lesson.objects.filter(name__icontains=search_text, status=Status.NORMAL)
            queryset = queryset.filter(Q(name__icontains=search_text) | Q(id__in=lessons.values('course_id'))).distinct()

        direction = data.get('search_direction', int)
        if direction is not None:
            queryset = queryset.filter(direction=direction)

        sub_direction = data.get('search_sub_direction', int)
        if sub_direction is not None:
            queryset = queryset.filter(sub_direction=sub_direction)

        difficulty = data.get('search_difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)

        except_course = data.get('except_course', int)
        if except_course is not None:
            queryset = queryset.exclude(id=except_course)

        sys_course = data.get('sys_course')
        my_course = data.get('my_course')
        share_course = data.get('share_course')
        if sys_course is not None:
            if sys_course == my_course == share_course == 'true':
                queryset = queryset
            elif sys_course == 'true' or my_course == 'true' or share_course == 'true':
                none_queryset = queryset.none()
                if sys_course == 'true':
                    none_queryset = none_queryset | queryset.filter(builtin=True).distinct()

                if my_course == 'true':
                    none_queryset = none_queryset | queryset.filter(create_user=self.request.user).distinct()

                if share_course == 'true':
                    from common_framework.models import AuthAndShare
                    none_queryset = none_queryset | queryset.filter(
                        Q(share_teachers__in=[self.request.user], share=AuthAndShare.ShareMode.CUSTOM_SHARE_MODE) |
                        Q(share=AuthAndShare.ShareMode.ALL_SHARE_MODE)
                    ).distinct()
                queryset = none_queryset
            else:
                queryset = queryset.none()

        lesson_table = course_modules.Lesson._meta.db_table

        queryset = queryset.extra(
            select={
                'count': '''
                      SELECT COUNT(*) from {lesson_table} WHERE 
                      {lesson_table}.course_id = {course_table}.id AND {lesson_table}.status = {status}
                    '''.format(
                    lesson_table=lesson_table,
                    course_table=queryset.model._meta.db_table,
                    status=Status.NORMAL,
                )
            }
        )
        return queryset

    @list_route(methods=['get'])
    def list_manage(self, request):
        rows = []
        courses = self.get_queryset().order_by('-update_time')
        data = RequestData(self.request, is_query=True)
        search_text = data.get('search_text')

        total = len(courses)

        sort = data.get('sort')
        if sort is not None:
            order = data.get('order')
            if order == 'desc':
                courses = courses.order_by('-' + sort)
            else:
                courses = courses.order_by(sort)

        page = data.get('page', int) if data.get('page', int) else 1

        pagesize = data.get('pagesize', int)
        if pagesize is not None:
            if (pagesize * page) > total:
                page = total / pagesize + 1
        else:
            pagesize = 10

        courses = courses[(page - 1) * pagesize:page * pagesize]
        data_start = (page - 1) * pagesize + 1
        data_end = data_start + len(courses) - 1

        for course in courses:
            courseserializer = serializers.CourseSerializer(course)
            courseserializer.context['request'] = self.request
            rows.append(courseserializer.data)

        # rows.extend(serializers.CourseSerializer(course).data for course in courses)

        if search_text is not None:
            course_ids = [course['id'] for course in rows]
            lessons = course_modules.Lesson.objects.filter(name__icontains=search_text, status=Status.NORMAL,
                                                           course_id__in=course_ids).distinct()
            rows.extend([serializers.LessonSerializer(lesson).data for lesson in lessons])

        return Response(data={'total': total, 'rows': rows, 'page': page, 'data_start': data_start, 'data_end': data_end,
                              'pagesize': pagesize}, status=status.HTTP_200_OK)

    @list_route(methods=['get'])
    def course_statistics(self, request):
        course_rows = []
        lesson_rows = []
        courses = self.get_queryset().order_by('-update_time')
        data = RequestData(self.request, is_query=True)
        search_text = data.get('search_text')
        sort = request.query_params.get('sort', None)
        order = request.query_params.get('order', None)

        course_dict = courses.values('id', 'name', 'direction__cn_name', 'direction__en_name', 'difficulty', 'count', 'create_user__first_name')

        # 获取课时下学习人数
        lesson_study_quertset = course_modules.Record.objects.exclude(lesson__status=Status.DELETE).exclude(user__status=Status.DELETE)
        lesson_study_dict = lesson_study_quertset.values('lesson_id').annotate(
            lesson_study_count=Count('lesson_id'))
        lesson_study_dict = {lesson['lesson_id']: lesson['lesson_study_count'] for lesson in lesson_study_dict}

        # 获取课时下实验报告提交人数
        report_queryset = Note.objects.filter(resource__icontains='.lesson_report').exclude(user__status=Status.DELETE)
        if report_queryset.exists():
            report_dict = report_queryset.values('resource').annotate(report_learn_count=Count('resource'))
            hash_list = [report['resource'].split('_')[0] for report in report_dict]
            report_learn_dict = {}
            lesson_hash_queryset = course_modules.Lesson.objects.filter(hash__in=hash_list)
            if lesson_hash_queryset.exists():
                lesson_hash_dict = {lesson_hash.hash: lesson_hash.id for lesson_hash in lesson_hash_queryset}

            for report in report_dict:
                if report['resource'].split('_')[0] in lesson_hash_dict.keys():
                    report_learn_dict.update({
                        lesson_hash_dict.get(report['resource'].split('_')[0]): report['report_learn_count']
                    })
        else:
            report_learn_dict = {}

        # 获取课程下的实验提交人数
        course_learn_dicts = {}
        for lesson_id in report_learn_dict.keys():
            course_id = course_modules.Lesson.objects.filter(id=lesson_id).first().course.id
            if course_learn_dicts.has_key(course_id):
                course_learn_dicts[course_id].append(report_learn_dict[lesson_id])
            else:
                course_learn_dicts[course_id] = [report_learn_dict[lesson_id]]

        for course in course_dict:
            if course['count'] == 0:
                course['report_learn_count'] = 0

            if course['id'] in course_learn_dicts.keys():
                course['report_learn_count'] = sum(course_learn_dicts.get(course['id']))
            course_rows.append(serializers.CourseStatisticsSerializer(course, request).data)

        # 排序
        if sort and order == 'desc':
            course_rows = sorted(course_rows, key=lambda x: x[sort], reverse=True)
        elif sort and order == 'asc':
            course_rows = sorted(course_rows, key=lambda x: x[sort])

        # 分页
        total = len(course_rows)
        page = data.get('page', int) if data.get('page', int) else 1
        pagesize = data.get('pagesize', int)
        if pagesize is not None:
            if (pagesize * page) > total:
                page = total / pagesize + 1
        else:
            pagesize = 10
        course_rows = course_rows[(page - 1) * pagesize:page * pagesize]
        course_ids = [course['id'] for course in course_rows]
        data_start = (page - 1) * pagesize + 1
        data_end = data_start + len(course_rows) - 1

        if search_text is not None:
            lesson_queryset = course_modules.Lesson.objects.filter(name__icontains=search_text,
                                                                   status=Status.NORMAL,
                                                                   course_id__in=course_ids).distinct()
        else:
            lesson_queryset = course_modules.Lesson.objects.filter(status=Status.NORMAL).filter(
                course_id__in=course_ids)
        lesson_dict = lesson_queryset.values('id', 'course_id', 'name', 'type', 'difficulty',
                                             'create_user__first_name')
        lesson_dict = self.get_dict_by_key(lesson_dict, 'course_id')

        for course in course_rows:
            if course['id'] in lesson_dict.keys():
                lesson_list = lesson_dict.get(course['id'])
                for lesson in lesson_list:
                    if lesson['id'] in lesson_study_dict.keys():
                        lesson['lesson_study_count'] = lesson_study_dict.get(lesson['id'])

                    if lesson['id'] in report_learn_dict.keys():
                        lesson['report_learn_count'] = report_learn_dict.get(lesson['id'])

                    lesson_rows.append(serializers.LessonStatisticsSerializer(lesson).data)

        rows = course_rows + lesson_rows

        return Response(
            data={'total': total, 'rows': rows, 'page': page, 'data_start': data_start, 'data_end': data_end,
                  'pagesize': pagesize}, status=status.HTTP_200_OK)

    def get_dict_by_key(self, objs, key):
        obj_dicts = {}
        for obj in objs:
            get_key = obj.get(key)
            if obj_dicts.has_key(get_key):
                obj_dicts[get_key].append(obj)
            else:
                obj_dicts[get_key] = [obj]
        return obj_dicts

    def get_faculty_major_objs(self, request, course_id, faculty=None, major=None):
        if not course_id:
            return []

        course = course_modules.Course.objects.filter(id=course_id).first()
        if not course:
            return []

        return course

    def perform_batch_destroy(self, queryset):
        for course in queryset:
            course_modules.Lesson.objects.filter(course=course).update(status=Status.DELETE)
        queryset.update(status=Status.DELETE)
        return True

    @list_route(methods=['get'], )
    def batch_dumps(self, request):
        downloadToken = 'downloadToken'
        ids = request.query_params.getlist('ids', [])
        download_token = request.query_params.get(downloadToken)
        if not ids:
            return response.Response(status=status.HTTP_200_OK)

        # if len(ids) > 1:
        #     logger.error('only one course!')
        #     return response.Response(status=status.HTTP_200_OK)

        queryset = self.queryset.filter(id__in=ids)
        if not queryset:
            return response.Response(status=status.HTTP_200_OK)

        dump_path = dump_course(queryset)

        def file_iterator(file_name, chunk_size=512):
            with open(file_name, 'rb') as f:
                while True:
                    c = f.read(chunk_size)
                    if c:
                        yield c
                    else:
                        f.close()
                        os.remove(file_name)
                        break

        res = FileResponse(file_iterator(dump_path))
        res['Content-Length'] = os.path.getsize(dump_path)
        res['Content-Type'] = 'application/octet-stream'
        res['Content-Disposition'] = 'attachment;filename="%s"' % os.path.basename(dump_path.encode('utf8'))
        res.set_cookie(downloadToken, download_token)
        return res

    @list_route(methods=['get', 'post'], )
    def batch_loads(self, request):
        if request.method == 'GET':
            files = scan_course_resource()
            return response.Response({'files': files})
        elif request.method == 'POST':
            UPLOADTOKEN = 'uploadToken'
            filenames = request.data.getlist('filenames', [])
            attachment_file = request.FILES.get('attachment', None)
            upload_token = request.query_params.get(UPLOADTOKEN, None)

            if attachment_file:
                destination = open(os.path.join(resource_api_setting.LOAD_TMP_DIR, attachment_file.name), 'wb+')
                for chunk in attachment_file.chunks():  # 分块写入文件
                    destination.write(chunk)
                destination.close()
                filenames = [attachment_file.name]
            if not filenames:
                return response.Response(status=status.HTTP_201_CREATED)

            delay_task.new_task(self._batch_loads, 2, (filenames, upload_token, attachment_file.name))

            res = response.Response(status=status.HTTP_201_CREATED)
            # res.set_cookie(UPLOADTOKEN, upload_token, max_age=80)
            return res

    def _batch_loads(self, filenames, upload_token, file_name):
        user = self.request.user
        path = self.request.path
        info = ";".join([path, file_name])
        try:
            for filename in filenames:
                load_course(filename)
            RecordLoads.objects.create(slug=upload_token, status=True, info=info, user=user)
        except Exception as e:
            RecordLoads.objects.create(slug=upload_token, info=info, user=user, status=False, errorinfo=str(e))
            logger.info(e)
        self.clear_cache()

    @list_route(methods=['get'], )
    def statistics(self, request):
        # 某个课时下面， 所有的学生学习课时的情况
        lesson_id = request.query_params.get('course_id')
        faculty = self.query_data.get('faculty', int)
        major = self.query_data.get('major', int)
        classes = self.query_data.get('classes', int)
        search = request.query_params.get('search')

        record_queryset = course_modules.Record.objects.filter(lesson_id=lesson_id,
                                                               progress=course_modules.Record.Progress.LEARED
                                                               ).exclude(user__status=Status.DELETE)

        if faculty > 0:
            record_queryset = record_queryset.filter(user__faculty_id=faculty)

        if major > 0:
            record_queryset = record_queryset.filter(user__major_id=major)

        if classes > 0:
            record_queryset = record_queryset.filter(user__classes_id=classes)

        if search:
            user_ids = User.objects.filter(first_name__icontains=search).values_list('id')
            record_queryset = record_queryset.filter(user_id__in=list(user_ids))

        record_lessons = record_queryset.values('user', 'user__first_name', 'user__username', 'user__faculty__name', 'user__major__name',
                                                'user__classes__name').annotate(learned_count=Count('user'))

        # 完成实验，和实验平均分, 该课程下的所有课时
        report_hash = course_modules.Lesson.objects.filter(id=lesson_id).first().hash + '_report'
        notes = Note.objects.filter(resource=report_hash).exclude(user__status=User.USER.DELETE)
        note_dicts = {note.user_id: note for note in notes}

        # 完成课后练习
        lesson_record_solveds = course_modules.LessonPaperRecord.objects.filter(lesson_id=lesson_id, solved=True)
        lesson_record_solveds_dict = self.get_dict_key_to_obj(lesson_record_solveds, 'submit_user_id')

        for record_lesson in record_lessons:
            record_lesson_user_id = record_lesson['user']
            if record_lesson_user_id in note_dicts.keys():
                record_lesson['experiment_mark_score'] = note_dicts.get(record_lesson_user_id).score
                record_lesson['update_time'] = note_dicts.get(record_lesson_user_id).update_time
                record_lesson['resource'] = note_dicts.get(record_lesson_user_id).resource
                record_lesson['report_id'] = note_dicts.get(record_lesson_user_id).id
                record_lesson['experiment_is_pass'] = True
                record_lesson['teacher'] = note_dicts.get(record_lesson_user_id).teacher.username if \
                                                            note_dicts.get(record_lesson_user_id).teacher else None

            if record_lesson_user_id in lesson_record_solveds_dict.keys():
                leson_record_list = lesson_record_solveds_dict.get(record_lesson_user_id)
                lesson_record_count, isRemove = self.calc_objs_count_and_avg(leson_record_list, 'solved')
                record_lesson['complete_practice'] = lesson_record_count

        return list_view(request, record_lessons, serializers.StatisticsSerializer)

    def get_dict_key_to_obj(self, objs, key):
        obj_dicts = {}
        for obj in objs:
            get_key = getattr(obj, key)
            if obj_dicts.has_key(get_key):
                obj_dicts[get_key].append(obj)
            else:
                obj_dicts[get_key] = [obj]
        return obj_dicts

    def calc_objs_count_and_avg(self, objs, key, **kwargs):
        report_complete_count = 0
        report_sum_score = 0
        for obj in objs:
            if getattr(obj, key) is not True:
                continue
            if kwargs.get('filter_option', None):
                tuple_option = kwargs.get('filter_option')
                if getattr(obj, tuple_option[0]) not in tuple_option[1]:
                    continue
            report_complete_count += 1
            report_sum_score += obj.score
        try:
            report_avg = float(report_sum_score) / report_complete_count
        except ZeroDivisionError:
            report_avg = 0

        return report_complete_count, report_avg

    @detail_route(methods=['get'], )
    def statistics_detail(self, request, pk):
        user_id = int(pk)
        course_id = self.query_data.get('course_id', int)

        lesson_id = self.query_data.get('lesson_name', int)
        search = request.query_params.get('search')
        record_queryset = course_modules.Record.objects.filter(lesson__course_id=course_id,
                                                               progress=course_modules.Record.Progress.LEARED,
                                                               user_id=user_id)
        if lesson_id:
            record_queryset = record_queryset.filter(lesson_id=lesson_id)

        if search:
            record_queryset = record_queryset.filter(lesson__name__icontains=search)

        record_queryset = record_queryset.values('user__first_name', 'lesson__name', 'lesson__type', 'lesson__hash',
                                                 'user')

        notes = Note.objects.filter(resource__icontains='.lesson_report', user_id=user_id)

        notes_dict = {}
        for note in notes:
            notes_dict[note.resource] = note

        for record in record_queryset:
            report_lesson_hash = record['lesson__hash'] + '_report'
            if report_lesson_hash in notes_dict.keys():
                note_obj = notes_dict.get(report_lesson_hash)
                record['note'] = NoteSerializer(note_obj).data
            else:
                record['note'] = None

        return list_view(request, record_queryset, serializers.StatisticsDetailSerializer)

    @list_route(methods=['get'], )
    def class_statistics(self, request):
        id = request.query_params.get('class_id', None)

        faculty = self.query_data.get('faculty', int)
        major = self.query_data.get('major', int)
        search = request.query_params.get('search')
        sort = request.query_params.get('sort', None)
        order = request.query_params.get('order', None)

        record_queryset = course_modules.Record.objects.filter(progress=course_modules.Record.Progress.LEARED).exclude(
            user__status=User.USER.DELETE)

        if faculty > 0:
            record_queryset = record_queryset.filter(user__faculty_id=faculty)

        if major > 0:
            record_queryset = record_queryset.filter(user__major_id=major)

        if search:
            record_queryset = record_queryset.filter(user__classes__name__icontains=search)

        # 完成的课时
        class_records = record_queryset.values('user__classes', 'user__classes__name', 'user__faculty__name',
                                               'user__major__name').annotate(
            complete_lessons=Count('user__classes')).exclude(user__classes=None)

        # 完成的实验和实验平均分
        notes = Note.objects.filter(resource__icontains='.lesson_report').exclude(user__status=User.USER.DELETE)
        note_list = notes.values('user__classes', 'user__classes__name').annotate(
            note_count=Count('user__classes')).exclude(user__classes=None)
        for note in note_list:
            note["average_score"] = \
            notes.filter(user__classes=note["user__classes"]).aggregate(average_score=Avg("score"))["average_score"]
        note_dicts = {note['user__classes']: note for note in note_list}

        # 完成的课后练习数
        lesson_record_solveds = course_modules.LessonPaperRecord.objects.filter(solved=True)
        lesson_record_list = lesson_record_solveds.values("submit_user_id__classes",
                                                          "submit_user_id__classes__name").annotate(
            lesson_count=Count("submit_user_id__classes"))
        lesson_record_dicts = {lesson_record['submit_user_id__classes']: lesson_record for lesson_record in lesson_record_list}

        for class_record in class_records:
            class_id = class_record["user__classes"]
            if class_id in note_dicts.keys():
                class_record["complete_experiment"] = note_dicts.get(class_id).get("note_count")
                class_record["experiment_mark_score"] = note_dicts.get(class_id).get("average_score")
            else:
                class_record["complete_experiment"] = 0
                class_record["experiment_mark_score"] = 0

            if class_id in lesson_record_dicts.keys():
                class_record["complete_practice"] = lesson_record_dicts.get(class_id).get('lesson_count')
            else:
                class_record["complete_practice"] = 0

        rows = [serializers.ClassStatisticsSerializer(row).data for row in class_records]

        if sort and order == 'desc':
            class_records = sorted(class_records, key=lambda x: x[sort], reverse=True)
        elif sort and order == 'asc':
            class_records = sorted(class_records, key=lambda x: x[sort])

        if id:
            for row in rows:
                if row["id"] == int(id):
                    return Response(data=row, status=status.HTTP_200_OK)
                    break
        else:
            # return Response(data={'total': len(class_records), 'rows': rows}, status=status.HTTP_200_OK)
            return list_view(request, class_records, serializers.ClassStatisticsSerializer)

    @list_route(methods=['get'], )
    def single_class_statistics(self, request):
        x_axis = []
        lesson = []
        experiment = []
        score = []
        class_id = request.query_params.get("class_id", None)
        student_list = [user.first_name for user in
                        User.objects.filter(classes_id=class_id).exclude(status=User.USER.DELETE)]

        record_queryset = course_modules.Record.objects.filter(progress=course_modules.Record.Progress.LEARED,
                                                               user__classes_id=class_id).exclude(
            user__status=User.USER.DELETE)

        # 学生完成的课时
        class_records = record_queryset.values('user', 'user__first_name', 'user__classes__name', 'user__faculty__name',
                                               'user__major__name').annotate(learned_count=Count('user')).order_by(
            '-learned_count')

        # 完成的实验和实验平均分
        notes = Note.objects.filter(resource__icontains='.lesson_report',
                                    user__classes_id=class_id).exclude(user__status=User.USER.DELETE)
        note_list = notes.values('user', 'user__first_name', 'user__classes__name').annotate(
            note_count=Count('user'))
        for note in note_list:
            note["average_score"] = \
                notes.filter(user=note["user"]).aggregate(average_score=Avg("score"))["average_score"]

        for class_record in class_records:
            user_id = class_record["user"]
            for note in note_list:
                if note["user"] == user_id:
                    class_record["note_count"] = note["note_count"]
                    class_record["average_score"] = round(note["average_score"])

        rows = [serializers.SingleClassStatisticsSerializer(row).data for row in class_records]
        for row in rows[:30:1]:
            x_axis.append(row['name'])
            lesson.append(row['complete_lessons'])
            experiment.append(row['complete_experiment'])
            score.append(row['experiment_mark_score'])
            student_list.remove(row['name'])

        # for student in student_list:
        #     x_axis.append(student)
        #     lesson.append(0)
        #     experiment.append(0)
        #     score.append(float(0))

        jsons = {"x_axis": {"data": x_axis},
                 "lesson": {"data": lesson},
                 "experiment": {"data": experiment},
                 "score": {"data": score},
                 "sys_type": {"data": 'OJ'}
                 }
        return Response(data=jsons, status=status.HTTP_200_OK)

    @list_route(methods=['get'])
    def user_statistics(self, request):
        faculty = self.query_data.get('faculty', int)
        major = self.query_data.get('major', int)
        classes = self.query_data.get('classes', int)
        search = request.query_params.get('search')
        sort = request.query_params.get('sort', None)
        order = request.query_params.get('order', None)

        user_queryset = User.objects.exclude(status=Status.DELETE)

        if faculty > 0:
            user_queryset = user_queryset.filter(faculty_id=faculty)

        if major > 0:
            user_queryset = user_queryset.filter(major_id=major)

        if classes > 0:
            user_queryset = user_queryset.filter(major_id=major)

        if search:
            user_queryset = user_queryset.filter(first_name__icontains=search)

        user_list = user_queryset.values('id', 'first_name', 'classes__name', 'faculty__name', 'major__name', 'is_superuser')

        # 完成的课时
        record_queryset = course_modules.Record.objects.filter(progress=course_modules.Record.Progress.LEARED).exclude(
            user__status=User.USER.DELETE)
        class_records_dict = self.get_dict_key_to_obj(record_queryset, 'user_id')

        # 完成的实验和实验平均分
        notes = Note.objects.filter(resource__icontains='.lesson_report').exclude(user__status=User.USER.DELETE)
        note_dicts = self.get_dict_key_to_obj(notes, 'user_id')

        # 完成的课后练习数
        lesson_record_solveds = course_modules.LessonPaperRecord.objects.filter(solved=True)
        lesson_record_dict = self.get_dict_key_to_obj(lesson_record_solveds, 'submit_user_id')

        # 用户权限字典
        user_group_dict = {group.name: group.user_set.all().exclude(status=Status.DELETE) for group in Group.objects.all()}
        user_dict = {}
        for group, users in user_group_dict.items():
            user_dict.update({user.id: group for user in users})

        # 用户上报时间字典
        report_time_dict = {user.id: user.report_time for user in user_queryset if user.report_time}
        group_admin_name = Group.objects.get(id=GroupType.ADMIN).name

        for user in user_list:
            if user['is_superuser']:
                user['group_name'] = group_admin_name
            elif user['id'] in user_dict:
                user['group_name'] = user_dict.get(user['id'])
            else:
                user['group_name'] = _('x_student')

            if user['id'] in report_time_dict.keys():
                critical_time = timezone.now() - timedelta(seconds=auth_api_settings.OFFLINE_TIME)
                if report_time_dict.get(user['id']) >= critical_time:
                    user['online'] = User.Online.ONLINE
                else:
                    user['online'] = User.Online.OFFLINE
            else:
                user['online'] = User.Online.OFFLINE

            if user['id'] in class_records_dict.keys():
                user['complete_lessons'] = len(class_records_dict.get(user['id']))
            else:
                user['complete_lessons'] = 0

            if user['id'] in note_dicts.keys():
                user['complete_experiment'] = len(note_dicts.get(user['id']))
                user['experiment_mark_score'] = float(sum([note.score for note in note_dicts.get(user['id'])])) / \
                                                len([note.score for note in note_dicts.get(user['id'])])
            else:
                user['complete_experiment'] = 0
                user['experiment_mark_score'] = 0

            if user['id'] in lesson_record_dict.keys():
                user['complete_practice'] = len(lesson_record_dict.get(user['id']))
            else:
                user['complete_practice'] = 0

        if sort and order == 'desc':
            user_list = sorted(user_list, key=lambda x: x[sort], reverse=True)
        elif sort and order == 'asc':
            user_list = sorted(user_list, key=lambda x: x[sort])

        return list_view(request, user_list, serializers.UserStatisticsSerializer)


class LessonViewSet(common_mixins.CacheModelMixin,
                    common_mixins.PublicModelMixin,
                    common_mixins.DestroyModelMixin,
                    viewsets.ModelViewSet):
    queryset = course_modules.Lesson.objects.filter(status=Status.NORMAL)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.LessonSerializer
    # filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    filter_backends = (filters.SearchFilter, common_filters.BootstrapOrderFilter)
    related_cache_class = (web_viewsets.LessonViewSet,)
    ordering_fields = ('order', 'id', 'type', 'difficulty', 'public', 'exercise_public', 'lesson_type')
    # ordering = ('order', 'id',)
    ordering = ('-update_time', '-create_time')
    search_fields = ('name',)

    def _add_pdf_watermark(self):
        attach_file = self.request.FILES['pdf']
        full_water_name = os.path.join(settings.MEDIA_ROOT, 'image', 'mark.pdf')

        if not os.path.exists(full_water_name):
            try:
                create_watermark(full_water_name, 'www.cyberpeace.cn')
            except Exception, e:
                pass

        full_pdf_file_name = add_watermark(attach_file.read(), full_water_name)

        with open(full_pdf_file_name, 'rb') as file_object:
            BytesIO = StringIO
            content = file_object.read()
            file = InMemoryUploadedFile(BytesIO(content),
                                        getattr(attach_file, "field_name", "pdf"),
                                        str(uuid.uuid4()) + '.' + 'pdf',
                                        attach_file.content_type,
                                        len(content),
                                        attach_file.charset)

        if os.path.exists(full_pdf_file_name):
            try:
                os.remove(full_pdf_file_name)
            except Exception, e:
                pass
        return file

    def sub_perform_create(self, serializer):
        file_status_flag = False
        knowledges = None
        if self.request.data.getlist('knowledges'):
            knowledges = self.request.data.getlist('knowledges', [])
            knowledges = [x for x in knowledges if x != '']
            knowledges = ",".join(knowledges)

        if serializer.validated_data.has_key('video'):
            video_file = self.request.FILES['video']
            file_status_flag = True
            # if os.path.splitext(video_file.name)[1] not in [".avi", ".mp4"]:
            #     raise exceptions.ValidationError({'video': u'视频格式目前仅限.avi和.mp4'})
            if os.path.splitext(video_file.name)[1] not in [".mp4"]:
                raise exceptions.ValidationError({'video': _('x_only_allow_mp4')})
        if serializer.validated_data.get('pdf'):
            pdf_file = self.request.FILES['pdf']
            if os.path.splitext(pdf_file.name)[1] != ".pdf":
                return False
        # serializer.validated_data['pdf'] = self._add_pdf_watermark()
        if file_status_flag:
            instance = serializer.save(create_user=self.request.user,
                                       video_state=VIDEOSTATE.CHANGEING,
                                       knowledges=knowledges)
            # 异步处理视频转码
            # video_name = os.path.splitext(video_file.name)[0]
            delay_task.new_task(handle_video_cut, 2, (instance,))
        else:
            instance = serializer.save(create_user=self.request.user,
                                       knowledges=knowledges)

        # 增加课时jstree子目录
        # if instance.public:
        lesson_jstree_CURD(Method_Type.LESSON_CREATE, course_modules.LessonJstree, instance)

        if self.request.data.get("capabili_name", False):
            if instance.type in [course_modules.Lesson.Type.PRACTICE, course_modules.Lesson.Type.EXAM]:
                self._handle_lesson_paper(serializer, instance, instance.type)
            else:
                raise exceptions.ValidationError({'capabili_name': CourseResError.LESSON_TYPE_WRONG})
        return True

    def sub_perform_destroy(self, instance):
        instance.status = Status.DELETE
        instance.save()
        return True

    def extra_handle_list_data(self, data):
        # 实验课， 使用实验报告存在的话才显示按钮
        note_lesson_report_rescouce = Note.objects.filter(resource__endswith='.lesson_report').values_list('resource',
                                                                                                           flat=True)
        data_ids = [validated_data.get('id') for validated_data in data]
        # 统计课后练习的数量
        lesson_paper_count = dict(
            course_modules.LessonPaperTask.objects.filter(lesson_id__in=data_ids).values_list('lesson').annotate(
                Count('lesson')))
        for row in data:
            lesson_hash = row.get('hash')
            lesson_id = row.get('id')
            if "".join([lesson_hash, '_report']) in note_lesson_report_rescouce:
                row['has_report'] = True
            else:
                row['has_report'] = False

            count = lesson_paper_count.get(lesson_id, 0)
            row['exercise_count'] = count
        return data

    def perform_batch_destroy(self, queryset):
        ids = list(queryset.values_list("id", flat=True))
        destory_statues = super(LessonViewSet, self).perform_batch_destroy(queryset)
        if destory_statues:
            # 删除课时jstree子目录
            lesson_jstree_CURD(Method_Type.LESSON_DELETE, course_modules.LessonJstree, None, ids=ids)
            return True
        return False
        pass

    def perform_batch_public(self, queryset, public):
        status = super(LessonViewSet, self).perform_batch_public(queryset, public)
        # if status:
        # 更新jstree子节点数据
        lesson_jstree_CURD(Method_Type.PUBLIC, course_modules.LessonJstree, None, queryset=queryset, public=public)
        return True
        # return False
        pass

    def get_queryset(self):
        queryset = self.queryset

        user = self.request.user
        if not user.is_superuser:
            # 课时访问权限
            course_ids = course_modules.Course.objects.filter(status=Status.NORMAL).filter(
                Q(share_teachers__in=[user], share=AuthAndShare.ShareMode.CUSTOM_SHARE_MODE) |
                Q(**{'{create_user_filed}'.format(create_user_filed="create_user"): user}) |
                Q(share=AuthAndShare.ShareMode.ALL_SHARE_MODE)
            ).distinct().values_list('id', flat=True)
            queryset = queryset.filter(course_id__in=course_ids)

        data = RequestData(self.request, is_query=True)
        course_id = data.get('course_id', int)
        if course_id is not None:
            queryset = queryset.filter(course__id=course_id)

        public = data.get('public', int)
        if public:
            queryset = queryset.filter(public=public)

        search_direction = data.get('search_direction', int)
        if search_direction:
            queryset = queryset.filter(course__direction_id=search_direction)

        except_course = data.get('except_course', int)
        if except_course is not None:
            queryset = queryset.exclude(course_id=except_course)

        type = data.get('type', int)
        if type is not None:
            queryset = queryset.filter(type=type)

        difficluty = data.get('difficulty', int)
        if difficluty is not None:
            queryset = queryset.filter(difficulty=difficluty)

        return queryset

    def sub_perform_update(self, serializer):
        file_status_flag = False
        knowledges = None
        if serializer.instance.builtin:
            raise exceptions.ValidationError(CourseResError.BUILTIN_CAN_NOT_EDIT)

        if self.request.data.getlist('knowledges'):
            knowledges = self.request.data.getlist('knowledges', [])
            knowledges = [x for x in knowledges if x != '']
            knowledges = ",".join(knowledges)

        if serializer.validated_data.has_key('video'):
            video_file = self.request.FILES['video']
            file_status_flag = True
            if os.path.splitext(video_file.name)[1] not in [".mp4"]:
                raise exceptions.ValidationError({'video': _('x_only_allow_mp4')})
        if serializer.validated_data.get('pdf'):
            pdf_file = self.request.FILES['pdf']
            if os.path.splitext(pdf_file.name)[1] != ".pdf":
                return False

        # serializer.validated_data['pdf'] = self._add_pdf_watermark()
        if file_status_flag:
            # 异步处理视频转码
            instance = serializer.save(video_state=VIDEOSTATE.CHANGEING, knowledges=knowledges)
            # video_name = os.path.splitext(video_file.name)[0]
            delay_task.new_task(handle_video_cut, 2, (instance,))
        else:
            instance = serializer.save(knowledges=knowledges)

        lesson_jstree_CURD(Method_Type.LESSON_UPDATE, course_modules.LessonJstree, instance)

        if self.request.data.get("capabili_name", False):
            if instance.type in [course_modules.Lesson.Type.PRACTICE, course_modules.Lesson.Type.EXAM]:
                self._handle_lesson_paper(serializer, instance, instance.type, isUpdate=True)
            else:
                raise exceptions.ValidationError({'capabili_name': CourseResError.LESSON_TYPE_WRONG})

        return True

    def _handle_lesson_paper(self, serializer, instance, lessonType, isUpdate=False):
        """
        :param serializer: 序列化对象
        :param instance: 实例对象
        :param lessonType: 课程类型
        :param isUpdate: 更新还是创建
        """
        testPaper = get_object_or_404(TestPaper, pk=self.request.data.get("capabili_name"))
        taskArrary = TestPaperTask.objects.filter(test_paper__id=testPaper.id)
        # 将试卷中的题目复制到课程当中去
        if isUpdate:
            lesson_task_list = course_modules.LessonPaperTask.objects.filter(lesson=instance, type=lessonType)
            if lesson_task_list:
                # 判断原来是否存在初始数据, 批量删除
                try:
                    course_modules.LessonPaperTask.objects.filter(lesson=instance, type=lessonType).delete()
                    course_modules.LessonPaperRecord.objects.filter(lesson=instance).delete()
                except ProtectedError:
                    raise exceptions.ParseError(CourseResError.CANNT_CHANGE_HAS_DONE)

        self._copy_task(taskArrary, instance, lessonType)

    @detail_route(methods=['get', ])
    def ret_testpaper_detail(self, request, pk):
        context = {}
        lesson_id = int(pk)
        lesson_type = request.query_params.get("type", None)
        rows = []
        context['number'] = 0
        context['allScore'] = 0

        if lesson_type:
            taskArrary = course_modules.LessonPaperTask.objects.filter(lesson_id=lesson_id, type=lesson_type)
            context['number'] = taskArrary.count()

            for t in taskArrary:
                task = get_task_object(t.task_hash)
                context['allScore'] += t.score
                rows.append(serializers.Serializer(task, t).data)

        context['tasks'] = rows
        return response.Response({'error_code': 0, 'response_data': context})
        pass

    @detail_route(methods=['get'], )
    def lesson_env_monitor(self, request, pk):
        lesson_id = int(pk)
        lesson_obj = get_object_or_404(course_modules.Lesson, pk=lesson_id)
        lesson_envs = lesson_obj.envs.filter(env__status=env_models.Env.Status.USING)  # 课程对应的环境

        if lesson_envs.count() == 0:
            # 课程场景不存在
            return response.Response(data={'error': CourseResError.LESSON_ENV_NOT_EXIST},
                                     status=status.HTTP_400_BAD_REQUEST)

        env_datas = ActiveEnvSerializer([lesson_env.env for lesson_env in lesson_envs], many=True).data
        monitor_info_ret = ActiveEnvSerializer.get_monitor_info(env_datas, ['monitor'])
        monitor_info = monitor_info_ret['monitor_info']
        shared_monitor_list = []
        for env_id, monitor_list in monitor_info.items():
            shared_monitor_list.extend(monitor_list)

        return response.Response(
            {
                'total': len(shared_monitor_list),
                'rows': shared_monitor_list,
            },
            status=status.HTTP_200_OK)

    @staticmethod
    def get_user_obj(user_id):
        user = User.objects.get(pk=user_id)
        return {
            'user_id': user.id,
            "username": user.first_name,
            "first_name": user.first_name
        }

    @detail_route(methods=['post'], )
    def new_create(self, request, pk):
        old_course_id = int(pk)
        lesson_ids = request.data.getlist('lesson_ids', [])
        if not lesson_ids:
            raise exceptions.ValidationError(CourseResError.NO_LESSON_SELECTED)

        be_copy_lessons = course_modules.Lesson.objects.filter(id__in=lesson_ids)

        for copy_lesson in be_copy_lessons:
            lesson_data = serializers.LessonCopySerializer(copy_lesson).data
            lesson_instance = course_modules.Lesson.objects.create(
                course_id=old_course_id,
                create_user=self.request.user,
                **json.loads(json.dumps(lesson_data))
            )

            # 拷贝文件
            self.copy_lesson_file_as_new(lesson_instance, copy_lesson)

            # 复制场景
            lesson_env = copy_lesson.envs.filter(env__status=Env.Status.TEMPLATE).first()
            if lesson_env:
                lesson_instance.envs.add(lesson_env)

            # 拷贝课后练习
            self.copy_exercise_tasks(copy_lesson, lesson_instance)

            # 增加目录
            lesson_jstree_CURD(Method_Type.LESSON_CREATE, course_modules.LessonJstree, lesson_instance)
        common_mixins.CacheModelMixin.clear_cls_cache(LessonViewSet)
        return response.Response({'status': 'success'}, status=status.HTTP_200_OK)

    def copy_exercise_tasks(self, old_instance, new_instance):
        # 拷贝课后练习
        lesson_paper_tasks = course_modules.LessonPaperTask.objects.filter(
            lesson=old_instance,
            type=course_modules.LessonPaperTask.Type.EXERCISE).values_list('task_hash', 'score')
        lesson_paper_tasks = list(lesson_paper_tasks)
        task_hashs = [lesson_paper_task[0] for lesson_paper_task in lesson_paper_tasks]
        task_copy_hashs = practice_api.copy_task_by_hash(task_hashs)

        gener_exercis_tasks = []
        for hash_index, task_copy_hash in enumerate(task_copy_hashs):
            exercise_instance = course_modules.LessonPaperTask(
                type=course_modules.LessonPaperTask.Type.EXERCISE,
                lesson=new_instance,
                score=lesson_paper_tasks[hash_index][1],
                task_hash=task_copy_hash
            )
            gener_exercis_tasks.append(exercise_instance)
        course_modules.LessonPaperTask.objects.bulk_create(gener_exercis_tasks)

    def copy_lesson_file_as_new(self, new_instance, old_instance):
        new_pdf_path = self._copy_real_file(old_instance.pdf.name)
        new_markdownfile_path = self._copy_real_file(old_instance.markdownfile.name)
        new_video_path = self._copy_real_file(old_instance.video.name)
        new_attachment_path = self._copy_real_file(old_instance.attachment.name)
        new_html_path = self._copy_real_file(old_instance.html.name)

        # trans video copy
        new_video_preview_path = self._copy_real_file(old_instance.video_preview.name)
        new_video_poster_path = self._copy_real_file(old_instance.video_poster.name)
        new_video_change_path = self._copy_real_file(old_instance.video_change.name, old_instance.id, new_instance.id,
                                                     copytree=True)

        new_instance.pdf = new_pdf_path
        new_instance.markdownfile = new_markdownfile_path
        new_instance.video = new_video_path
        new_instance.attachment = new_attachment_path
        new_instance.html = new_html_path
        new_instance.video_preview = new_video_preview_path
        new_instance.video_poster = new_video_poster_path
        new_instance.video_change = new_video_change_path
        new_instance.save()
        pass

    def _copy_real_file(self, old_path, old_id=None, new_id=None, copytree=False):
        # 一个待拷贝文件的路径
        if not old_path:
            return None
        if old_path.startswith('/'):
            old_path = old_path[1:]
        old_file_path = os.path.join(settings.MEDIA_ROOT, old_path)

        if not os.path.exists(old_file_path):
            logger.info('this file is not exists --> {}'.format(old_file_path))
            return None

        old_dirname_path = os.path.dirname(old_file_path)
        old_suffix_name = os.path.splitext(old_file_path)
        new_name = str(uuid.uuid4()) + old_suffix_name[1]
        new_file_path = os.path.join(old_dirname_path, new_name)

        if copytree:
            # 当文件目录存在的时候， copytree方法不起作用 需要copy一个目录
            old_dirname_path = os.path.join(settings.MEDIA_ROOT, 'course/video_trans/video_change',
                                            'copy_{}_to_{}'.format(old_id, new_id),
                                            str(uuid.uuid4()))
            if os.path.exists(old_dirname_path):
                shutil.rmtree(old_dirname_path)

            shutil.copytree(os.path.dirname(old_file_path), old_dirname_path)
            new_file_path = os.path.join(old_dirname_path, 'playlist.m3u8')
        else:
            shutil.copy(old_file_path, new_file_path)
        return new_file_path.replace(settings.MEDIA_ROOT, '')[1:]

    @detail_route(methods=['get', 'post'], )
    def exercises(self, request, pk):
        if request.method == "GET":
            rows = []
            taskArrary = course_modules.LessonPaperTask.objects.filter(lesson__id=int(pk),
                                                                       type=course_modules.LessonPaperTask.Type.EXERCISE)
            for t in taskArrary:
                task = get_task_object(t.task_hash)
                if not task:
                    continue
                data = serializers.SerializerNew(task, t).data
                rows.append(data)

            return response.Response(data=rows, status=status.HTTP_200_OK)

        datas = request.data.get('data', '')
        if not datas or not json.loads(datas):
            raise exceptions.ParseError(CourseResError.NO_LESSON_QUESTIONS)

        datas = json.loads(datas)
        instance = self.get_object()

        taskArrary = course_modules.LessonPaperTask.objects.filter(lesson=instance,
                                                                   type=course_modules.LessonPaperTask.Type.EXERCISE)
        if taskArrary:
            # 判断原来是否存在初始数据, 批量删除
            try:
                taskArrary.delete()
                course_modules.LessonPaperRecord.objects.filter(lesson=instance).delete()
            except ProtectedError:
                raise exceptions.ParseError(CourseResError.EXERCISE_HAS_DONE)

        self._copy_task(datas, instance, course_modules.LessonPaperTask.Type.EXERCISE)
        common_mixins.CacheModelMixin.clear_cls_cache(LessonViewSet)
        return response.Response(data={'type': 'success'}, status=status.HTTP_200_OK)

    def _copy_task(self, taskArrary, instance, lessonpapertask_type):
        task_hashs = []
        for data in taskArrary:
            data_hash = lessonpapertask_type == course_modules.LessonPaperTask.Type.EXERCISE and data[
                'hash'] or data.task_hash
            task_hashs.append(data_hash)
        task_copy_hashs = practice_api.copy_task_by_hash(task_hashs)

        event_task_list = []
        for task in taskArrary:
            task_hash = lessonpapertask_type == course_modules.LessonPaperTask.Type.EXERCISE and task[
                'hash'] or task.task_hash
            task_score = lessonpapertask_type == course_modules.LessonPaperTask.Type.EXERCISE and task[
                'score'] or task.score
            event_task = course_modules.LessonPaperTask(
                lesson=instance,
                task_hash=task_copy_hashs[task_hashs.index(task_hash)],
                score=task_score,
                type=lessonpapertask_type,
            )
            event_task_list.append(event_task)
        course_modules.LessonPaperTask.objects.bulk_create(event_task_list)


class LessonNewViewSet(common_mixins.CacheModelMixin,
                       viewsets.ReadOnlyModelViewSet):
    queryset = course_modules.Lesson.objects.filter(status=Status.NORMAL)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.NewLessonSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)


class LessonJstreeViewSet(common_mixins.CacheModelMixin,
                          common_mixins.DestroyModelMixin,
                          viewsets.ModelViewSet):
    queryset = course_modules.LessonJstree.objects.all().order_by('order')
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.LessonJstreeSerializer
    page_cache = False
    json_type = {
        'default': 0,
        'folder': 1,
        'file': 2
    }

    def get_queryset(self):
        queryset = self.queryset
        course_id = self.request.query_params.get('course_id', None)
        if course_id is not None and course_id.isdigit():
            queryset = queryset.filter(course_id=int(course_id))

        return queryset

    @list_route(methods=['post', ])
    def change_data(self, request):
        strdata = request.data.get('data', None)
        course_id = request.data.get('course_id', None)
        orders = request.data.get('order', None)

        if strdata is None:
            return response.Response({"error": CourseResError.JSTREE_IS_EMPTY}, status=status.HTTP_400_BAD_REQUEST)
        if orders is None:
            return response.Response({"error": CourseResError.NO_ORDER}, status=status.HTTP_400_BAD_REQUEST)

        order_list = orders.split(",")
        datalist = json.loads(strdata)
        # 先清空课程下面所有的课时结构
        course_modules.LessonJstree.objects.filter(course_id=int(course_id)).delete()
        # 再次重新建立课程结构
        list_lessonjstree = self._handle_jstree_data(course_modules.LessonJstree, datalist, order_list, course_id)
        course_modules.LessonJstree.objects.bulk_create(list_lessonjstree)

        common_mixins.CacheModelMixin.clear_cls_cache(web_viewsets.LessonJstreeViewSet)

        return response.Response(data={'data': 'success'}, status=status.HTTP_200_OK)

    def _handle_jstree_data(self, ModelClass, datalist, order_list, course_id):
        list_lessonjstree = []
        for index, data in enumerate(datalist):
            temp_data = {}
            order_index = 9999
            if data['id'] in order_list:
                order_index = order_list.index(data['id'])

            temp_data = {
                "self_id": data["self_id"],
                "course_id": int(course_id),
                "parent": data['parent'],
                "text": data["text"],
                "type": self.json_type[data["type"]],
                "order": order_index,
                "public": data.has_key('public') and data['public'] or True,
                "parents": data["parents"]
            }
            if data.has_key('lesson') and data['lesson'] is not None:
                temp_data['lesson_id'] = int(data['lesson'])

            lessonJstree = ModelClass(**temp_data)
            list_lessonjstree.append(lessonJstree)
        return list_lessonjstree


class CourseScheduleViewSet(common_mixins.RequestDataMixin, common_mixins.CacheModelMixin,
                            common_mixins.DestroyModelMixin, viewsets.ModelViewSet):
    queryset = CourseSchedule.objects.filter(status=Status.NORMAL)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.CourseScheduleSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    ordering_fields = ('id',)
    ordering = ('-id',)

    def get_queryset(self):
        user = self.request.user
        queryset = self.queryset
        faculty = self.query_data.get('faculty', int)
        if faculty:
            queryset = queryset.filter(faculty_id=faculty)

        major = self.query_data.get('major', int)
        if major:
            queryset = queryset.filter(major_id=major)

        classes = self.query_data.get('classes', int)
        if classes:
            queryset = queryset.filter(classes_id=classes)

        create_user = self.query_data.get('create', int)
        if create_user:
            queryset = queryset.filter(create_user_id=create_user)

        if user.is_superuser:
            queryset = queryset
        if user.is_staff and not user.is_superuser:
            queryset = queryset.filter(create_user=user.id)
        if not user.is_staff and not user.is_superuser:
            if user.classes:
                queryset = self.queryset.filter(classes=user.classes)
        return queryset

    def sub_perform_create(self, serializer):
        dow = []
        if serializer.validated_data.get('course') is None:
            raise exceptions.ValidationError(CourseResError.LOST_COURSE)
        if serializer.validated_data.get('lesson') is None:
            raise exceptions.ValidationError(CourseResError.LOST_LESSON)
        classes = serializer.validated_data.get('classes')
        if serializer.validated_data.get('classes') is None:
            raise exceptions.ValidationError(CourseResError.LOST_CLASSES)
        else:
            start_time = serializer.validated_data.get('start')
            end_time = serializer.validated_data.get('end')
            if start_time >= end_time:
                raise exceptions.ValidationError(CourseResError.SCHEDULE_START_TIME_ERROR)
            if end_time.hour > 21:
                raise exceptions.ValidationError(CourseResError.SCHEDULE_TIME_ERROR)
            else:
                # 判断班级在时间短内是否已有课程
                schedules = CourseSchedule.objects.filter(status=Status.NORMAL, classes=classes)
                if not all(map(lambda s: True if end_time <= s.start or start_time >= s.end else False, schedules)):
                    raise exceptions.ValidationError(CourseResError.CLASS_IN_SCHEDULES)

        weekly = int(serializer.validated_data.get('dow'))
        dow.append(weekly)
        serializer.save(
            dow=dow,
            create_user=self.request.user
        )
        # 授权访问当前课程

        course = serializer.validated_data.get('course')
        if course.auth == AuthAndShare.AuthMode.CUSTOM_AUTH_MODE:
            course.auth_classes.add(classes)

        # 添加通知
        lesson = serializer.validated_data.get('lesson')
        start = serializer.validated_data.get("start").strftime("%Y-%m-%d %H:%M:%S")
        end = serializer.validated_data.get("end").strftime("%H:%M:%S")
        content = "~".join([start, end]) + '\n' + lesson.course.name + '/' + lesson.name

        add_sys_notice(user=self.request.user,
                       name=_("x_course_schedule_notice"),
                       content=content,
                       classes=classes,
                       type=SysNotice.Type.SCHEDULEMESSAGE
                       )
        return True

    def sub_perform_update(self, serializer):
        dow = []
        if serializer.validated_data.get('course') is None:
            raise exceptions.ValidationError(CourseResError.LOST_COURSE)
        if serializer.validated_data.get('lesson') is None:
            raise exceptions.ValidationError(CourseResError.LOST_LESSON)
        if serializer.validated_data.get('classes') is None or serializer.validated_data.get(
                'major') is None or serializer.validated_data.get('faculty') is None:
            raise exceptions.ValidationError(CourseResError.LOST_CLASSES)
        else:
            start_time = serializer.validated_data.get('start')
            end_time = serializer.validated_data.get('end')
            if start_time >= end_time:
                raise exceptions.ValidationError(CourseResError.SCHEDULE_START_TIME_ERROR)
            if end_time.hour > 21:
                raise exceptions.ValidationError(CourseResError.SCHEDULE_TIME_ERROR)
            else:
                # 判断班级在时间短内是否已有课程
                classes = serializer.validated_data.get('classes')
                schedules = CourseSchedule.objects.filter(status=Status.NORMAL, classes=classes).exclude(id=int(serializer.instance.id))
                if not all(map(lambda s: True if end_time <= s.start or start_time >= s.end else False, schedules)):
                    raise exceptions.ValidationError(CourseResError.CLASS_IN_SCHEDULES)

        weekly = int(serializer.validated_data.get('dow'))
        dow.append(weekly)

        serializer.save(
            dow=dow,
        )
        return True

    @list_route(methods=['delete'], )
    def batch_destroy(self, request):
        id = request.data.get('id')
        if not id:
            return Response(status=status.HTTP_204_NO_CONTENT)
        schedule = CourseSchedule.objects.get(id=id)
        schedule.status = Status.DELETE
        schedule.save()
        self.clear_cache()
        return Response(status=status.HTTP_200_OK)

    # def sub_perform_destroy(self, instance):
    #     instance.status = Status.DELETE
    #     instance.save()
    #     return True

    @detail_route(methods=['get', ])
    def classesroom_report(self, request, pk):
        # 一个课程下面的所有学生的实验报告, 并且是该班级的
        search_name = request.query_params.get('search', None)
        # 获取班级信息,
        course_schedule_obj = get_object_or_404(course_modules.CourseSchedule, pk=pk)

        # 过滤用户注册 过滤掉自己
        class_user_queryset = User.objects.filter(classes_id=course_schedule_obj.classes_id,
                                                  status__in=[User.USER.NORMAL, User.USER.NEW_REGISTER,
                                                              User.USER.PASS]).exclude(
            id=course_schedule_obj.create_user_id).exclude(groups__in=ADMIN_GROUPS)

        if search_name:
            class_user_queryset = class_user_queryset.filter(first_name__icontains=search_name)

        class_users_list = class_user_queryset.values('id', 'first_name', 'faculty__name', 'major__name',
                                                      'classes__name')  # 班级用户

        users_dict = {class_users_values['id']: class_users_values for class_users_values in class_users_list}
        class_user_note_reports = Note.objects.filter(user_id__in=users_dict.keys(),
                                                      resource=course_schedule_obj.lesson.hash + "_report")

        note_dict = {class_user_note_report.user_id: class_user_note_report for class_user_note_report in
                     class_user_note_reports}

        for class_user in class_users_list:
            class_user_id = class_user['id']
            if class_user_id in note_dict.keys():
                class_user['note'] = NoteSerializer(note_dict[class_user_id]).data

        return list_view(request, class_users_list, serializers.ClassesRoomReportSerializer)

    @detail_route(methods=['get', ])
    def classesroom_monitorl(self, request, pk):
        # 课堂监控
        course_schedule_obj = get_object_or_404(course_modules.CourseSchedule, pk=pk)

        # 该课堂下的所有用户 除了创建者
        class_user_queryset = User.objects.filter(classes_id=course_schedule_obj.classes_id,
                                                  status__in=[User.USER.NORMAL, User.USER.NEW_REGISTER,
                                                              User.USER.PASS]).exclude(
            id=course_schedule_obj.create_user_id).exclude(groups__in=ADMIN_GROUPS)
        class_users_list = class_user_queryset.values('id', 'first_name', 'faculty__name', 'major__name',
                                                      'classes__name')  # 班级用户

        # 签到
        sign_user_list = course_schedule_obj.schedulesign_set.filter(sign_in=True)
        sign_user_dict = {sign_user.user_id: sign_user for sign_user in sign_user_list}

        lesson_envs = course_schedule_obj.lesson.envs.filter(env__status=env_models.Env.Status.USING)
        if lesson_envs.count() == 0:
            # 课程场景不存在
            lesson_envs = []

        assistance_dict = {}
        if lesson_envs:
            env_datas = ActiveEnvSerializer([lesson_env.env for lesson_env in lesson_envs], many=True).data
            monitor_info_ret = ActiveEnvSerializer.get_monitor_info(env_datas, ['assistance'])
            assistance_info = monitor_info_ret['assistance_info']
            for env_id, assistance_list in assistance_info.items():
                for assistance in assistance_list:
                    user_id = assistance['user']['user_id']
                    assistance_dict.setdefault(user_id, []).append(assistance['link'])

        for class_user in class_users_list:
            class_user_id = class_user['id']
            if class_user_id in sign_user_dict.keys():
                class_user['sign_obj'] = serializers.ScheduleSignSerializer(sign_user_dict[class_user_id]).data
            if class_user_id in assistance_dict.keys():
                class_user['assistance_link'] = assistance_dict[class_user_id][0]

        return list_view(request, class_users_list, serializers.ClassesScheduleMonitorSerializer)

    @list_route(methods=['get'])
    def is_help(self, request):
        user_id = request.query_params.get('user_id', None)
        classroom_id = request.query_params.get('id', None)
        if not user_id or not classroom_id:
            return Response({'error': _('x_parameter_error')}, status=status.HTTP_400_BAD_REQUEST)
        course_modules.ScheduleSign.objects.filter(course_schedule_id=int(classroom_id), user_id=user_id) \
            .update(need_help=False)
        return Response({}, status=status.HTTP_200_OK)
        pass

    @list_route(methods=['get'])
    def classroom_statistics(self, request):
        top20 = []
        id = request.query_params.get('id', None)
        course_schedule_obj = get_object_or_404(course_modules.CourseSchedule, pk=int(id))

        # 该课堂下的所有用户 除了创建者
        class_user_queryset = User.objects.filter(classes_id=course_schedule_obj.classes_id,
                                                  status__in=[User.USER.NORMAL, User.USER.NEW_REGISTER,
                                                              User.USER.PASS]).exclude(
            id=course_schedule_obj.create_user_id).exclude(groups__in=ADMIN_GROUPS)

        # 签到
        sign_user_list = course_schedule_obj.schedulesign_set.filter(sign_in=True).exclude(
            user_id=course_schedule_obj.create_user_id).exclude(user__status=User.USER.DELETE)

        # 完成的实验和实验平均分
        notes = Note.objects.filter(resource__icontains=course_schedule_obj.lesson.hash + "_report").filter(
            user__classes_id=course_schedule_obj.classes_id).exclude(
            user_id=course_schedule_obj.create_user_id).exclude(
            user__status=User.USER.DELETE).exclude(user__groups__in=ADMIN_GROUPS)

        group_obj = Group.objects.filter(id=GroupType.USER).first()
        if not group_obj:
            raise exceptions.NotFound()

        class_complete_json = {
            "faculty": course_schedule_obj.faculty.name,
            "major": course_schedule_obj.major.name,
            "class": course_schedule_obj.classes.name,
            "total_users": class_user_queryset.count(),
            "sign_users": sign_user_list.count(),
            "complete_users": notes.filter(ispass=ReportStatus.PASS).count(),
            "group_name": group_obj.name
        }

        mark_json = {
            "not_pass": notes.filter(ispass=ReportStatus.NOT_PASS).count(),
            "pass": notes.filter(ispass=ReportStatus.PASS).filter(Q(score__gte=60.0) & Q(score__lt=80.0)).count(),
            "good": notes.filter(ispass=ReportStatus.PASS).filter(Q(score__gte=80.0) & Q(score__lt=90.0)).count(),
            "excellent": notes.filter(ispass=ReportStatus.PASS).filter(Q(score__gte=90.0) & Q(score__lt=100.0)).count(),
            "full_score": notes.filter(ispass=ReportStatus.PASS).filter(score=100.0).count()
        }

        pie_chart = [{"name": _('x_not_sign'), "value": class_user_queryset.count() - sign_user_list.count()},
                     {"name": _('x_sign'), "value": sign_user_list.count()}]

        top20_list = notes.values('user__first_name', 'score').order_by('-score')[:20:1]

        for t in top20_list:
            top20.append(dict(
                first_name=t['user__first_name'],
                score=t['score']
            ))

        rows = {
            "class_complete_json": class_complete_json,
            "mark_json": mark_json,
            "pie_chart": pie_chart,
            "top20": top20
        }

        return Response(data=rows, status=status.HTTP_200_OK)


class ClassroomGroupInfoViewSet(common_mixins.RequestDataMixin,
                                common_mixins.CacheModelMixin,
                                common_mixins.DestroyModelMixin,
                                viewsets.ModelViewSet):
    queryset = ClassroomGroupInfo.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.ClassroomGroupInfoSerializer

    def get_queryset(self):
        queryset = self.queryset

        classroom = self.query_data.get('classroom', int)
        if classroom is not None:
            queryset = queryset.filter(classroom=classroom)
        else:
            raise exceptions.PermissionDenied()

        return queryset

    @list_route(methods=['patch'])
    def update_group_info(self, request):
        try:
            schedule_id = int(request.data['schedule'])
            groups = json.loads(request.data['groups'])
        except Exception as e:
            raise exceptions.PermissionDenied()

        class_room_group_info = self.queryset.filter(classroom=schedule_id).first()
        if not class_room_group_info:
            raise exceptions.PermissionDenied()

        update_class_group_info(class_room_group_info, groups)

        return Response({})

    @list_route(methods=['get'])
    def get_class_envs(self, request):
        try:
            schedule_id = int(request.query_params['schedule'])
        except Exception as e:
            raise exceptions.PermissionDenied()

        class_room_group_info = self.queryset.filter(classroom=schedule_id).first()
        if not class_room_group_info:
            try:
                schedule = CourseSchedule.objects.get(pk=schedule_id)
            except CourseSchedule.DoesNotExist as e:
                raise exceptions.PermissionDenied()
            class_room_group_info = create_default_class_group_info(schedule)

        class_group_env_info = get_class_group_env_info(class_room_group_info)

        return Response(class_group_env_info)

    @list_route(methods=['post'])
    def create_class_envs(self, request):
        try:
            schedule_id = int(request.data['schedule'])
        except Exception as e:
            raise exceptions.PermissionDenied()

        class_room_group_info = self.queryset.filter(classroom=schedule_id).first()
        if not class_room_group_info:
            raise exceptions.PermissionDenied()

        if not class_room_group_info.classroom.lesson.envs.filter(env__status=Env.Status.TEMPLATE).exists():
            raise exceptions.ValidationError(error.NO_ENV_CONFIG)

        exs = []
        wait_info = {}
        groups = json.loads(class_room_group_info.groups)
        for group in groups:
            key = group['key']
            try:
                create_group_env(request.user.id, class_room_group_info.id, key)
            except PoolFullException as e:
                wait_info[key] = e.executor_info
            except Exception as e:
                exs.append(e)
                logger.error('create group env error: %s', e)
                continue

        data = {
            'hint': None,
            'wait_info': wait_info,
        }
        if exs:
            data['hint'] = exs[0].message or getattr(exs[0], 'detail', '')
        return Response(data)

    @list_route(methods=['post'])
    def create_group_env(self, request):
        try:
            schedule_id = int(request.data['schedule'])
            group_key = request.data['group_key']
        except Exception as e:
            raise exceptions.PermissionDenied()

        class_room_group_info = self.queryset.filter(classroom=schedule_id).first()
        if not class_room_group_info:
            raise exceptions.PermissionDenied()

        if not class_room_group_info.classroom.lesson.envs.filter(env__status=Env.Status.TEMPLATE).exists():
            raise exceptions.ValidationError(error.NO_ENV_CONFIG)

        wait_info = {}
        try:
            create_group_env(request.user.id, class_room_group_info.id, group_key)
        except PoolFullException as e:
            wait_info[group_key] = e.executor_info
        except Exception as e:
            pass

        return Response(wait_info)

    @list_route(methods=['delete'])
    def delete_class_envs(self, request):
        try:
            schedule_id = int(request.data['schedule'])
        except Exception as e:
            raise exceptions.PermissionDenied()

        class_room_group_info = self.queryset.filter(classroom=schedule_id).first()
        if not class_room_group_info:
            raise exceptions.PermissionDenied()

        groups = json.loads(class_room_group_info.groups)
        for group in groups:
            key = group['key']
            try:
                delete_group_env(class_room_group_info, key)
            except Exception as e:
                continue

        return Response({})

    @list_route(methods=['delete'])
    def delete_group_env(self, request):
        try:
            schedule_id = int(request.data['schedule'])
            group_key = request.data['group_key']
        except Exception as e:
            raise exceptions.PermissionDenied()

        class_room_group_info = self.queryset.filter(classroom=schedule_id).first()
        if not class_room_group_info:
            raise exceptions.PermissionDenied()

        delete_group_env(class_room_group_info, group_key)

        return Response({})

    @list_route(methods=['post'])
    def transfer_group_user(self, request):
        try:
            schedule_id = int(request.data['schedule'])
            user_id = int(request.data['user_id'])
            from_group_key = request.data['from_group_key']
            to_group_key = request.data['to_group_key']
        except Exception as e:
            raise exceptions.PermissionDenied()

        class_room_group_info = self.queryset.filter(classroom=schedule_id).first()
        if not class_room_group_info:
            raise exceptions.PermissionDenied()

        transfer_group_user(class_room_group_info, user_id, from_group_key, to_group_key)

        return Response({})


class ClassroomGroupTemplateViewSet(common_mixins.RequestDataMixin,
                                    common_mixins.CacheModelMixin,
                                    common_mixins.DestroyModelMixin,
                                    viewsets.ModelViewSet):
    queryset = ClassroomGroupTemplate.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.ClassroomGroupTemplateSerializer
    unlimit_pagination = True

    def get_queryset(self):
        queryset = self.queryset.filter(status=Status.NORMAL)

        classes = self.query_data.get('classes', int)
        if classes is not None:
            queryset = queryset.filter(classes=classes)

        return queryset

    def sub_perform_destroy(self, instance):
        instance.status = Status.DELETE
        instance.save()
        return True
