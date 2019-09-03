# -*- coding: utf-8 -*-
import logging
from datetime import timedelta
from datetime import datetime
from itertools import groupby

from django.db import connection
from django.contrib.auth import get_user_model
from django.db.models import Count, Sum, Avg
from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import exceptions, status

from common_framework.utils.constant import Status
from common_framework.utils.rest.permission import IsStaffPermission
from common_framework.views import find_menu
from common_web.decorators import login_required as web_login_required
from common_auth.constant import TeamUserStatus

from x_note.models import Note
from course.models import Lesson, Record
from course_occupation.models import OccupationIsChoice, OccupationCourse
from course_occupation.response import OccupationError
from event.models import EventUserSubmitLog
from practice.models import PracticeSubmitSolved
from x_person.response import bubbleOption_data_30
from x_person.utils.course_occupation_data import get_30day_CompleteData
from x_person.utils.product_type import get_edition

logger = logging.getLogger(__name__)

User = get_user_model()


@web_login_required
@find_menu()
def index_occupation(request, **kwargs):
    context = kwargs.get('menu')
    user_sort = '--'
    user_practice_score = '--'
    occupation_name = OccupationError.OCCUPATION_ONT_CHOICE
    occupation_id = ''
    occupation_status = False
    # 是否选择职业
    occupation_ischoice = OccupationIsChoice.objects.filter(user_id=request.user.id)
    logging.info('In the index_occupation function we get %s of occupationsystem' % occupation_ischoice.count())
    if occupation_ischoice:
        occupation_ischoice = occupation_ischoice[0]
        occupation_name = occupation_ischoice.occupation.name
        occupation_id = occupation_ischoice.occupation.id
        occupation_status = True
        context['occupation_ischoice_id'] = occupation_ischoice.id
    course_count = Record.objects.filter(user=request.user).exclude(lesson__course=None).values('lesson__course').annotate(
            aa=Count('lesson__course')).count()
    context['course_count'] = course_count
    context['occupation_name'] = occupation_name
    context['occupation_id'] = occupation_id
    context['occupation_status'] = occupation_status

    # 练习提交回答正确分数
    practice_sorces = PracticeSubmitSolved.objects.filter(is_solved=True).values(
        'submit_user').annotate(score_sum=Sum('score')).order_by('score_sum')
    logging.info('from PracticeSubmitSolved model get information about %s' % practice_sorces[:1])
    practice_sorces = list(practice_sorces)
    practice_sorces.sort(key=lambda s: s['score_sum'], reverse=True)  # 对list里面的dict进行排序
    first_practice_score_and_sort = {'score': None, 'sort': 1}
    for k, v in enumerate(practice_sorces):
        if request.user.id == v['submit_user']:
            user_practice_score = v['score_sum']
            if first_practice_score_and_sort['score'] == user_practice_score:
                user_sort = first_practice_score_and_sort['sort']
            else:
                user_sort = k + 1
            break
        else:
            if first_practice_score_and_sort['score'] != v['score_sum']:
                first_practice_score_and_sort['score'] = v['score_sum']
                first_practice_score_and_sort['sort'] = k + 1

    context['user_practice_score'] = user_practice_score
    context['user_sort'] = user_sort
    # 学习时长 ...
    # 版本信息
    context['edition'] = get_edition()
    return render(request, 'course_occupation/web/index_new.html', context=context)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def get_occuption_data(request):
    occupation_id = request.GET.get('occupation_id', None)
    if occupation_id is None or occupation_id == "":
        logging.info('we don\'t get occupation_id in this get_occuption_data() function')
        return Response(status=status.HTTP_400_BAD_REQUEST)
    course_stage_list = OccupationCourse.objects.filter(occupation_system__id=occupation_id).values(
        'course_id', 'course__name', 'obligatory', 'stage').order_by('stage')
    # 基础， 进阶， 高级
    course_id_list = []
    occupation_courses = []
    stage_list = []
    for row in course_stage_list:
        if row['course_id'] not in course_id_list:
            course_id_list.append(row['course_id'])
    for row in course_stage_list:
        if row['stage'] not in stage_list:
            stage_list.append(row['stage'])
    for course in course_stage_list:
        occupation_courses.append(course)
    # 根据级别对课程进行分组
    occupation_course_list = groupby(occupation_courses, key=lambda x: x['stage'])
    occupation_course_list = dict([(key, [a for a in group]) for key, group in occupation_course_list])
    lesson_list_queryset = Lesson.objects.filter(status=Status.NORMAL).filter(course__id__in=course_id_list)
    lesson_list = lesson_list_queryset.values('course_id').annotate(lesson_count=Count('course_id'))
    # 用户已经学习的课程记录/ 已学习-正在学
    lesson_recde = lesson_list_queryset.filter(record__user=request.user).values('course_id').annotate(
        recode_count=Count('course_id'))

    # 获取每个课程的id
    lesson_list = {row['course_id']: row for row in lesson_list}
    # 用户已经学习的课程数
    lesson_recde = {row['course_id']: row for row in lesson_recde}
    data = {}
    for stage in stage_list:
        # 遍历每个级别下的所有课程
        child_data = []
        for occupation_course in occupation_course_list.get(stage):
            sm_data = {}
            sm_data['lesson_count'] = 0
            sm_data['has_recde_percent'] = 0
            course_id = occupation_course['course_id']
            obligatory = occupation_course['obligatory']
            sm_data['course_id'] = course_id  # 课程id
            sm_data['obligatory'] = obligatory  # 是否必修
            if course_id in lesson_list:
                sm_data['lesson_count'] = lesson_list.get(course_id)['lesson_count']  # 有的课程没有课时
                if course_id in lesson_recde:
                    sm_data['has_recde_percent'] = int(
                        float(lesson_recde.get(course_id)['recode_count']) / float(sm_data['lesson_count']) * 100)

            sm_data['course_name'] = occupation_course['course__name']
            child_data.append(sm_data)
        data[stage] = child_data

    return Response(data=data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
def bubblechar(request):
    """
    计算 学习/比赛记录
    """
    data = {}
    dataCourse = []
    dataPratice = []
    dataMatch = []
    # 获取最近30天的数据：
    thirty_days = [(datetime.now() - timedelta(days=i)).strftime("%m-%d") for i in range(30)][::-1]
    before_30_time = datetime.now() - timedelta(days=29)

    select_start_time = {'day': connection.ops.date_trunc_sql('day', 'start_time')}
    select_time = {'day': connection.ops.date_trunc_sql('day', 'time')}
    select_submit_time = {'day': connection.ops.date_trunc_sql('day', 'submit_time')}

    dict_start_time = {'user': request.user, 'start_time__gte': before_30_time}
    dict_time = {'user': request.user, 'time__gte': before_30_time}
    dict_submit_time = {'submit_user': request.user, 'submit_time__gte': before_30_time}

    # 计算本月每天学习课程数量
    records = Record.objects.filter(**dict_start_time).extra(select=select_start_time).values('day').annotate(
        number=Count('id'))
    for record in records:
        # 生成数据格式[[1,2,3],[]]
        try:
            get_record_index = thirty_days.index(record['day'].strftime('%m-%d'))
        except ValueError:
            logging.info(
                'get_record_index Don\'t get the time index in thirty_days, that %s is not in list' % record[
                    'day'].strftime('%m-%d'))
            raise exceptions.NotAcceptable(OccupationError.TIME_INDEX_ERROR)
        dataCourse.append([get_record_index, record['number'], record['number'] + 10])

    # ad 版本没有练习模块
    # 计算本月每天练习分数 真实漏洞,夺旗解题,夺旗攻防
    practice_sorces = PracticeSubmitSolved.objects.filter(**dict_submit_time).filter(is_solved=True).extra(
        select=select_submit_time).values('day').annotate(score_sum=Sum('score'))
    for practice_sorce in practice_sorces:
        try:
            get_practice_index = thirty_days.index(practice_sorce['day'].strftime('%m-%d'))
        except ValueError:
            logging.info(
                'get_record_index Don\'t get the time index in thirty_days, that %s is not in list' % practice_sorce[
                    'day'].strftime('%m-%d'))
            raise exceptions.NotAcceptable(OccupationError.TIME_INDEX_ERROR)
        dataPratice.append([get_practice_index, practice_sorce['score_sum'], practice_sorce['score_sum']+10])

    # 计算本月每天比赛记录 考试,解题赛
    event_sorces = EventUserSubmitLog.objects.filter(**dict_time).filter(is_solved=True).extra(
        select=select_time).values('day').annotate(score_sum=Sum('score'))
    # jeopardy_sorces = EventUserAnswer.objects.filter(**dict_time).filter(status=Status.NORMAL).extra(
    #     select=select_time).values('day').annotate(score_sum=Sum('score'))
    for event_sorce in event_sorces:
        try:
            get_event_sorce_index = thirty_days.index(event_sorce['day'].strftime('%m-%d'))
        except ValueError:
            logging.info(
                'get_record_index Don\'t get the time index in thirty_days, that %s is not in list' % event_sorce[
                    'day'].strftime('%m-%d'))
            raise exceptions.NotAcceptable(OccupationError.TIME_INDEX_ERROR)
        dataMatch.append([get_event_sorce_index, event_sorce['score_sum'], event_sorce['score_sum'] + 10])
    # for jeopardy_sorce in jeopardy_sorces:
    #     dataMatch.append([jeopardy_sorce['day'].day, jeopardy_sorce['score_sum'], jeopardy_sorce['score_sum']])
    # 合并生成30天数据
    data_thirty_days = get_30day_CompleteData(bubbleOption_data_30, dataCourse, dataPratice, dataMatch)
    if data_thirty_days.has_key('dataCourse'):
        dataCourse = data_thirty_days['dataCourse']
    if data_thirty_days.has_key('dataPratice'):
        dataPratice = data_thirty_days['dataPratice']
    if data_thirty_days.has_key('dataMatch'):
        dataMatch = data_thirty_days['dataMatch']

    data['dataCourse'] = dataCourse
    data['dataPratice'] = dataPratice
    data['dataMatch'] = dataMatch
    data['thirty_days'] = thirty_days

    return Response(data=data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated, ))
def line_chart(request):
    data = {}
    dataCourse = []
    dataExperiment = []
    dataScore = []
    user_id = request.user.id
    user_obj = User.objects.filter(id=user_id).first()
    # 获取最近30天的数据：
    thirty_days = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30)][::-1]

    # 每天学习的课程
    records = Record.objects.filter(progress=Record.Progress.LEARED, user=user_obj)
    for day in thirty_days:
        course_record = records.filter(start_time__icontains=day)
        dataCourse.append(course_record.count()) if course_record.exists() else dataCourse.append(0)

    # 每天通过的实验与实验平均分
    notes = Note.objects.filter(resource__icontains='.lesson_report', ispass=1, user=user_obj)
    for day in thirty_days:
        range_time = (datetime.strptime(day, '%Y-%m-%d'), datetime.strptime(day, '%Y-%m-%d') + timedelta(days=1))
        experiment_record = notes.filter(update_time__range=range_time)
        dataExperiment.append(experiment_record.count()) if experiment_record.exists() else dataExperiment.append(0)

        score_record = notes.filter(update_time__range=range_time)
        if score_record.exists():
            dataScore.append(round(score_record.aggregate(avg=Avg('score'))['avg'], 1))
        else:
            dataScore.append(0)

    data['dataCourse'] = dataCourse
    data['dataExperiment'] = dataExperiment
    data['dataScore'] = dataScore
    data['thirty_days'] = [(datetime.now() - timedelta(days=i)).strftime("%m-%d") for i in range(30)][::-1]

    return Response(data=data, status=status.HTTP_200_OK)


# 处理ad版本
@web_login_required
@find_menu()
def index_ad(request, **kwargs):
    context = kwargs.get('menu')
    if request.user.team:
        t_id = request.user.team.id
        t_u = request.user.teamuser_set.all().filter(status=TeamUserStatus.JOIN).first()
        context['teamid'] = t_id
        context['recordid'] = t_u.id
        context['teamleader'] = t_u.team_leader
    return render(request, 'course_occupation/web/index_ad.html', context=context)
