# -*-coding: utf-8 -*-
import collections
import copy
import json

from django.utils import timezone

import random
from django.db.models import Sum
from django.http import Http404
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from rest_framework import filters, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import list_route, detail_route
from rest_framework.response import Response
from rest_framework import status

from common_auth.api import oj_auth_class
from common_auth.models import User
from common_framework.utils.constant import Status
from common_framework.utils.rest import mixins as common_mixins
from common_framework.utils.rest.request import RequestData
from common_calendar import api as calendar_api
from course.models import CourseSchedule, ScheduleSign

from course.web import serializers
from course import models as course_modles
from course_occupation.models import OccupationCourse


from practice import api as practice_api


class Serializer:
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
            option = collections.OrderedDict(sorted(json.loads(raw.option).items(), key=lambda t: t[0]))
            self.data['options'] = option
            self.data['is_choice_question'] = 1
            self.data['is_multiple_choice'] = raw.multiple
        else:
            if raw.file and raw.file.url:
                file_attach = {
                    'name': raw.file.name,
                    'url': raw.file.url,
                }

                self.data['file_url'] = file_attach
            self.data['url'] = raw.url
            self.data['is_dynamic_env'] = raw.is_dynamic_env


class DirectionViewSet(common_mixins.CacheModelMixin,
                       viewsets.ReadOnlyModelViewSet):
    queryset = course_modles.Direction.objects.filter(status=Status.NORMAL)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.DirectionSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    ordering_fields = ('id', 'en_name')
    ordering = ('en_name',)


class CourseViewSet(common_mixins.CacheModelMixin,
                    viewsets.ReadOnlyModelViewSet):
    queryset = course_modles.Course.objects.filter(status=Status.NORMAL).filter(public=True)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.CourseSerializer

    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    ordering_fields = ('update_time', 'lock')
    ordering = ('lock', '-update_time',)
    search_fields = ('name',)

    @oj_auth_class
    def get_queryset(self):
        queryset = self.queryset
        data = RequestData(self.request, is_query=True)

        direction = data.get('search_direction', int)
        if direction is not None:
            queryset = queryset.filter(direction=direction)

        sub_direction = data.get('search_sub_direction', int)
        if sub_direction is not None:
            queryset = queryset.filter(sub_direction=sub_direction)

        difficulty = data.get('search_difficulty')
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)

        # occupation = data.get('search_occupation')
        # if occupation:
        #     # 职业下的所有课程
        #     course_ids = OccupationCourse.objects.filter(occupation_system_id=occupation).values('course_id')
        #     queryset = queryset.filter(id__in=course_ids)

        # lesson_count = '''
        #     SELECT COUNT(*) FROM course_lesson WHERE course_lesson.course_id = course_course.id AND course_lesson.status=1 AND course_lesson.public=1
        #                        '''
        #
        # queryset = queryset.extra(
        #     select={'lesson_count': lesson_count}
        # )
        # 过滤课时都为隐藏的课程
        queryset = queryset.extra(
            where=['''
            EXISTS (SELECT * FROM course_lesson
            WHERE course_lesson.course_id = course_course.id
            AND course_lesson.status=1
            AND course_lesson.public=1
            HAVING (SELECT count(*) lc
			FROM course_lesson
			WHERE course_lesson.course_id = course_course.id
				AND course_lesson.status=1
				AND course_lesson.public=1)>0)
            ''']
        )
        # rows = queryset
        # for i in range(len(queryset)):
        #     if queryset[i].lesson_count == 0:
        #
        return queryset

    def extra_handle_list_data(self, data):
        course_ids = [row['id'] for row in data]
        sum_course_lesson_duration = course_modles.Lesson.objects.filter(status=Status.NORMAL, public=True,
                                                                         course__id__in=course_ids).values(
            'course__id').annotate(Sum('duration'))
        for row in data:
            row['duration_sum'] = 0
            for k, v in enumerate(sum_course_lesson_duration):
                if v['course__id'] == row['id']:
                    row['duration_sum'] = v['duration__sum']
                    break

        return data

    @list_route(methods=['get'])
    def recommend(self, request):
        course_ids = list(OccupationCourse.objects.filter(occupation_system__occupation_choice__user=request.user,
                                                          status=Status.NORMAL).values_list('course', flat=True))[:6]
        queryset = self.queryset.filter(id__in=course_ids)
        coures_serializer_data = self.serializer_class(queryset, many=True).data
        data = self.extra_handle_list_data(coures_serializer_data)
        return Response(data=data, status=status.HTTP_200_OK)


class LessonViewSet(common_mixins.CacheModelMixin,
                    viewsets.ReadOnlyModelViewSet):
    queryset = course_modles.Lesson.objects.filter(status=Status.NORMAL).filter(public=True)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.LessonSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    ordering_fields = ('order', 'id')
    ordering = ('order', 'id')
    search_fields = ('name',)
    page_cache = False

    def get_queryset(self):
        queryset = self.queryset

        data = RequestData(self.request, is_query=True)
        course_id = data.get('course_id', int)
        if course_id is not None:
            queryset = queryset.filter(course__id=course_id)
            course_obj = course_modles.Course.objects.filter(id=course_id).first()
            if course_obj:
                # 增加个人日历
                calendar_api.add_calendar(_("x_learning_course"), course_obj.name.encode("utf-8"), calendar_api.CALENDAR_COURSE,
                                          reverse("course:detail", kwargs={"course_id": course_id}), False,
                                          user=self.request.user)
        else:
            queryset = queryset.filter(id__in=[])

        return queryset

    @detail_route(methods=['get', ])
    def need_help(self, request, pk):
        from course.utils.lesson import ws_message as lesson_message
        from rest_framework.generics import get_object_or_404
        from common_env.cms.serializers import ActiveEnvSerializer
        from common_env import models as env_models
        from course.models import CourseSchedule, ScheduleSign

        user = self.request.user
        # lesson = get_object_or_404(course_modles.Lesson, pk=pk)
        teacher_users_ids = CourseSchedule.objects.filter(lesson_id=pk, classes_id=user.classes_id,
                                                      status=Status.NORMAL).values_list('id', flat=True)
        # 修改请求帮助状态
        ScheduleSign.objects.filter(course_schedule__in=teacher_users_ids, user=user)\
                            .update(need_help=True)

        # connectionId = self.request.query_params.get('connectionId', None)
        # if connectionId is None:
        #     return Response({})
        #
        # user = self.request.user
        # lesson = get_object_or_404(course_modles.Lesson, pk=pk)
        # teacher_user = CourseSchedule.objects.filter(lesson=lesson, classes_id=user.classes_id, status=Status.NORMAL)
        # if not teacher_user:
        #     return Response({})
        # # 查询结果不唯一有多个老师
        # teacher_user = teacher_user[0]
        # lesson_envs = lesson.envs.filter(env__status=env_models.Env.Status.USING)
        # if not lesson_envs:
        #     return Response({})
        #
        # assistance_dict = {}
        # env_datas = ActiveEnvSerializer([lesson_env.env for lesson_env in lesson_envs], many=True).data
        # monitor_info_ret = ActiveEnvSerializer.get_monitor_info(env_datas, ['assistance'])
        # assistance_info = monitor_info_ret['assistance_info']
        # for env_id, assistance_list in assistance_info.items():
        #     for assistance in assistance_list:
        #         user_id = assistance['user']['user_id']
        #         assistance_dict.setdefault(user_id, []).append(assistance['link'])
        #
        # connection_link = assistance_dict.get(user.id, [''])[0]
        #
        # data = {"help": True, 'help_user': user.id, 'lesson_id': lesson.id, 'connections_ids': connection_link}
        #
        # lesson_message.send_lesson_user_data(lesson, teacher_user, lesson_message.MESSAGE_CODE.HELP, data)
        return Response({})

    @detail_route(methods=['get',])
    def exampaper_task(self, request, pk):
        exercise = self.request.query_params.get('exercise', None)
        try:
            lesson_obj = course_modles.Lesson.objects.get(pk=pk)
        except:
            raise Http404()

        lesson_paper_task_type = course_modles.LessonPaperTask.Type.EXERCISE if exercise else lesson_obj.type
        taskArrary = course_modles.LessonPaperTask.objects.filter(lesson=lesson_obj, type=lesson_paper_task_type)

        rows = []
        done = False
        score = 0
        all_score = 0
        myAnswer = []
        tprs = course_modles.LessonPaperRecord.objects.filter(lesson=pk, submit_user=request.user)
        if tprs.exists():
            done = True
            for tpr in tprs:
                right_answer = practice_api.get_task_answer(tpr.task_hash, request.user)
                tmp = {
                    'taskId': tpr.task_hash,
                    'answer': tpr.answer,
                    'rightAnswer': right_answer
                }
                score = score + tpr.score
                myAnswer.append(tmp)

        for t in taskArrary:
            task = practice_api.get_task_object(t.task_hash)
            rows.append(Serializer(task, t).data)

            all_score = all_score + t.score

        return Response(
            {
                'response_data':
                    {
                        'tasks': rows, 'done': done,
                        'myAnswer': myAnswer, 'score': score,
                        'all_score': all_score
                    },
                'error_code': 0
            })

    @detail_route(methods=['POST'], )
    def submit_testpaper(self, request, pk):
        lesson_obj = course_modles.Lesson.objects.filter(id=int(pk)).first()
        if not lesson_obj:
            return Response({'error_code': 1})

        if course_modles.LessonPaperRecord.objects.filter(submit_user=request.user, lesson=lesson_obj).exists():
            return Response({'error_code': 3})

        exercise_status = request.data.get('exercise', None)
        lesson_type = exercise_status == 'true' and course_modles.LessonPaperTask.Type.EXERCISE or lesson_obj.type

        taskArrary = course_modles.LessonPaperTask.objects.filter(lesson=lesson_obj, type=lesson_type)
        task_dict = {}
        for task in taskArrary:
            task_dict[task.task_hash] = task.score

        taskhashs = str(request.data.get('taskids'))
        answers = str(request.data.get('answers').encode('utf-8'))

        task_hash = taskhashs.split(',')
        answer = answers.split(',')

        task_count = len(taskArrary)
        submit_task_count = len(taskArrary)
        if task_count != submit_task_count:
            return Response({'error_code': 2})

        get_score = 0
        for i in range(0, task_count):
            # 判断题目是否正确
            # right = practice_api.validate_answer(task_hash[i], answer[i], request.user)
            right, score, specific_score = practice_api.validate_answer(task_hash[i], answer[i], request.user)
            if right:
                score = task_dict.get(task_hash[i])
                if score:
                    get_score += score
            else:
                score = 0
            course_modles.LessonPaperRecord.objects.create(
                lesson=lesson_obj,
                score=score,
                task_hash=task_hash[i],
                answer=answer[i],
                solved=True,
                submit_user=request.user,
            )
        self.clear_cache()
        return Response({'response_data': {'allScore': get_score}, 'error_code': 0})


class LessonNewViewSet(common_mixins.CacheModelMixin,
                       viewsets.ReadOnlyModelViewSet):
    queryset = course_modles.Lesson.objects.filter(status=Status.NORMAL).filter(public=True)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.NewLessonSerializer
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)

        course_obj = course_modles.Course.objects.filter(id=instance.course_id).first()
        if course_obj:
            # 增加个人日历
            calendar_api.add_calendar(_("x_learning_course"), course_obj.name.encode("utf-8"),
                                      calendar_api.CALENDAR_COURSE,
                                      reverse("course:detail", kwargs={"course_id": instance.course_id}), False,
                                      user=self.request.user)

        return Response(serializer.data)


class LessonScheduleViewSet(common_mixins.CacheModelMixin,
                       viewsets.ReadOnlyModelViewSet):
    queryset = course_modles.Record.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.RecordSerializer

    @detail_route(methods=['post'])
    #makrdown 进度处理
    def progress_rate(self, request, pk):
        times = float(request.data["times"])
        scrollpercent = float(request.data["scrollpercent"])

        progress, total_schedule = self.calculation_status(pk, times, scrollpercent, request)

        if times < 1:
            return Response("")
        pss = course_modles.Record.objects.filter(lesson_id=pk, user=request.user).first()
        if pss:
            studyed_time = pss.study_time
            times = times + float(studyed_time)
            pss.study_time = times

            old_schedule = pss.markdown_schedule
            if total_schedule > old_schedule:
                pss.markdown_schedule = total_schedule
            pss.progress =progress
            pss.save()
        else:
            course_modles.Record.objects.create(lesson_id = pk,
                                                user=request.user,
                                                study_time = times,
                                                progress = progress,
                                                markdown_schedule = total_schedule,
                                                )
        # self.calculation_record(request.user, pk)
        return Response("")

    #markdown进度处理相关函数
    def calculation_status(self, pk, times, scrollpercent, request):
        record = course_modles.Record.objects.filter(lesson_id=pk, user=request.user).first()
        if record:
            times =float(record.study_time) + times
            if float(record.markdown_schedule) > scrollpercent:
                scrollpercent = float(record.markdown_schedule)

        pss = course_modles.Lesson.objects.filter(id=pk).first()
        if pss:
            study_total = pss.duration
            study_total = study_total * 60

            times_percent = float(times / study_total) * 100
            schedule= float(times_percent/2) + float(scrollpercent/2)
            if schedule < 10:
                progress = 0
            elif 10 <= schedule <= 90:
                progress = 1
            elif schedule > 90:
                progress = 2
            return progress, round(schedule, 2)
        else:
            return "0", "0"

    @detail_route(methods=['post'])
    #pdf进度处理
    def pdf_progress(self, request, pk):
        times = float(request.data["times"])
        progress, schedule = self.calculation(times, pk, request.user)
        pss = course_modles.Record.objects.filter(lesson_id=pk, user=request.user).first()
        if pss:
            studyed_time = pss.study_time
            times = times + float(studyed_time)
            pss.study_time = times
            pss.progress =progress
            pss.pdf_progress = schedule
            pss.save()
        else:
            course_modles.Record.objects.create(lesson_id = pk,
                                                user=request.user,
                                                study_time = times,
                                                progress = progress,
                                                pdf_progress = schedule)
        # self.calculation_record(request.user, pk)
        return Response("")

    #pdf进度处理相关函数
    def calculation(self, times, pk, user):
        record = course_modles.Record.objects.filter(lesson_id=pk, user=user).first()
        if record:
            times = float(record.study_time) + times

        pss = course_modles.Lesson.objects.filter(id=pk).first()
        if pss:
            schedule = round((times/(pss.duration * 60) *100),2)
            if schedule > 100:
                schedule = 100
            if schedule < 10:
                progress = 0
            elif 10 <= schedule <= 90:
                progress = 1
            elif schedule > 90:
                progress = 2
        return progress, schedule

    #视频处理函数
    @detail_route(methods=['post'])
    def video_progress(self, request, pk):
        is_end = int(request.data["loadtime"])
        play_time = float(request.data["play_time"])
        total_time = float(request.data["total_time"])

        if is_end == 0:
            schedule = round(total_time/play_time*100,2)
        #由于无法在为播放完情况下获取总长度，所以这里是随机进度
        else:
            if total_time <= 5:
                schedule = random.randint(11,40)
            elif 5 < total_time <= 60:
                schedule = random.randint(40, 60)
            else:
                schedule = random.randint(60, 85)

        pss = course_modles.Record.objects.filter(lesson_id=pk, user=request.user).first()
        if pss:
            old_schedule = pss.video_progress
            if old_schedule > schedule:
                schedule = old_schedule

        if  schedule < 10:
            progress = 0
        elif 10 <= schedule <= 90:
            progress = 1
        else:
            progress = 2

        if pss:
            pss.progress =progress
            pss.video_progress = schedule
            pss.save()
        else:
            course_modles.Record.objects.create(lesson_id = pk,
                                                user=request.user,
                                                progress = progress,
                                                video_progress=schedule,
                                                )
        # self.calculation_record(request.user, pk)
        return Response("")

    # def calculation_record(self, user, pk):
    #     user_class = course_modles.Classes.objects.filter(user=user).first()
    #     if user_class:
    #         tasks = tech_models.Syllabus.objects.filter(auth_classes=user_class, auth_lesson=pk)
    #         for task in tasks:
    #             self.clear_cache()
    #             users = User.objects.filter(classes_id=user_class)
    #             for user in users:
    #                 user_progress, user_schedule = self.calculation_progress(user, pk)
    #
    #                 # 获取课时的hash
    #                 lesson_hash = course_modles.Lesson.objects.filter(id=pk).first()
    #                 progress_record = tech_models.SyllabusRecord.objects.filter(user=user,
    #                                                                             task_hash=lesson_hash.hash).first()
    #
    #                 # 是创建还是更新
    #                 record = self.progress_create if progress_record == None else self.progress_updata
    #
    #                 record(task, lesson_hash.hash, user, user_schedule, user_progress)


    def calculation_progress(self, user, pk):
        """
        :param user: 用户名
        :param lesson: 课时
        :return: 学习的状态、学习进度、学习时间百分比
        """

        record = course_modles.Record.objects.filter(user=user.id).filter(lesson__id=pk).first()
        if record:
            video_progress = record.video_progress
            pdf_schedule = record.pdf_progress
            markdown_schedule = record.markdown_schedule
            schedule = 0

            if video_progress > 0.0:
                if pdf_schedule > 0:
                    schedule = (pdf_schedule + video_progress) / 2
                elif markdown_schedule > 0:
                    schedule = (markdown_schedule + video_progress) / 2
                else:
                    schedule = video_progress
            elif pdf_schedule > 0:
                schedule = pdf_schedule
            elif markdown_schedule > 0:
                schedule = markdown_schedule

            return record.progress, schedule
        return 0, 0

    #创建数据
    # def progress_create(self, task, task_hash, user, progress, schedule_type):
    #     tech_models.SyllabusRecord.objects.create(
    #         task_detail_id = task.id,
    #         task_hash = task_hash,
    #         user = user,
    #         progress = progress,
    #         schedule_type = schedule_type
    #     )

    #更新数据
    # def progress_updata(self, task_detail, task_hash, user, progress, schedule_type):
    #     pss = tech_models.SyllabusRecord.objects.filter(user=user, task_hash=task_hash).first()
    #     if not pss:
    #         return
    #     pss.progress = progress
    #     pss.schedule_type = schedule_type
    #
    #     pss.save()


class LessonJstreeViewSet(common_mixins.CacheModelMixin,
                       viewsets.ReadOnlyModelViewSet):
    queryset = course_modles.LessonJstree.original_objects.all().order_by('order')
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.LessonJstreeSerializer

    def get_queryset(self):
        queryset = self.queryset
        course_id = self.request.query_params.get('course_id', None)
        filter_type = self.request.query_params.get('filter_type', None)
        if course_id is not None and course_id.isdigit():
            queryset = queryset.filter(course_id=int(course_id))
            empty_self_id_list = self._filter_empty_folder(queryset)
            queryset = queryset.exclude(self_id__in=empty_self_id_list)
            if filter_type and filter_type == 'file':
                queryset = queryset.filter(type=course_modles.LessonJstree.Type.FILE).order_by('order')

        return queryset

    def _filter_empty_folder(self, queryset):
        """
        :param queryset:
        :return: 返回所有空文件夹的id
        """
        all_folder_id_list = queryset.exclude(type=course_modles.LessonJstree.Type.FILE).values('self_id')
        file_parent_list = queryset.filter(type=course_modles.LessonJstree.Type.FILE).values_list('parents', flat=True)

        from functools import reduce
        file_parent_list = filter(None,
                                  list(set(reduce(lambda x, y: x + ',' + y + ',', list(file_parent_list)).split(','))))

        empty_folder = [folder_id['self_id']
                        for folder_id in all_folder_id_list
                        if folder_id['self_id'] not in file_parent_list and not folder_id['self_id'].startswith('course')]

        return empty_folder


class CourseScheduleViewSet(common_mixins.RequestDataMixin, common_mixins.CacheModelMixin,
                                common_mixins.DestroyModelMixin, viewsets.ModelViewSet):
    queryset = CourseSchedule.objects.filter(status=Status.NORMAL)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.CourseScheduleSerializer
    ordering_fields = ('id',)
    ordering = ('-id',)

    def get_queryset(self):
        user = self.request.user
        queryset = self.queryset
        if user.is_staff:
            queryset = queryset.filter(create_user=user.id)
        if not user.is_staff and not user.is_superuser:
            if user.classes:
                queryset = self.queryset.filter(classes=user.classes)

        return queryset

    @detail_route(methods=['POST', ])
    def add_sign_in(self, request, pk):
        from django.shortcuts import get_object_or_404

        courseschedule_obj = get_object_or_404(CourseSchedule, pk=pk)
        instance, falg = ScheduleSign.objects.get_or_create(
            course_schedule=courseschedule_obj,
            user=request.user,
            sign_in=True,
        )
        if falg:
            instance.sign_in_time = timezone.now()
            instance.save()

        return Response("")
