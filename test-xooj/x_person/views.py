# -*- coding: utf-8 -*-
import logging
import traceback
from datetime import datetime, timedelta
from random import Random
from urlparse import urljoin

from django.core.mail import send_mail
from django.db import connection
from django.db.models import Sum
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from rest_framework import status, permissions, exceptions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common_framework.utils.request import is_en

from common_auth.constant import TeamUserStatus
from common_auth.models import Faculty, Major, Classes
from common_auth.models import User
from common_framework.views import find_menu
from common_web.decorators import login_required as web_login_required
from event.models import EventUserSubmitLog
from oj.settings import DEFAULT_FROM_EMAIL
from oj.config import ORGANIZATION_EN, ORGANIZATION_CN
from system_configuration.models import SystemConfiguration
from x_person.response import OccupationError, bubbleOption_data_30
from x_person.setting import api_settings
from x_person.utils.course_occupation_data import get_30day_CompleteData

slug = api_settings.SLUG


def one_user_one_team_required(view_function):
    def decorated_function(*args, **kwargs):
        request = args[0]
        if request.user.team:
            return team(*args, **kwargs)
        else:
            return view_function(*args, **kwargs)

    return decorated_function


def team_leader_required(view_function):
    def decorated_function(*args, **kwargs):
        request = args[0]
        team_id = int(kwargs['pk'])
        t_u = request.user.teamuser_set.all().filter(status=TeamUserStatus.JOIN).first()
        if request.user.team and request.user.team.id == team_id and t_u.team_leader:
            return view_function(*args, **kwargs)
        else:
            return team(*args, **kwargs)

    return decorated_function


def teamuser_exit_user(view_function):
    def decorated_function(*args, **kwargs):
        # teamuser表中status是exit， 强制清空user表中team未None,
        # 如果是teamleader 则解散队伍
        request = args[0]
        user = request.user
        if user.team:
            user_last = user.teamuser_set.last()
            if user_last and user_last.status == TeamUserStatus.EXIT:
                user.team = None
                user.save()

        return view_function(*args, **kwargs)
    return decorated_function


@web_login_required
@find_menu(slug)
def info(request, **kwargs):
    if is_en(request):
        ORGANIZATION = ORGANIZATION_EN
    else:
        ORGANIZATION = ORGANIZATION_CN
    context = kwargs.get('menu')
    s_c = SystemConfiguration.objects.filter(key='organization')
    if s_c.exists():
        s_c = s_c.first()
        school = s_c.value
    else:
        school = "OJ Platform"
    context['school_name'] = school
    context['user'] = request.user
    faculty_name, major_name, classes_name, audit = ['', '', '', '']
    if (Faculty.objects.filter(id=request.user.faculty_id).exists()):
        faculty_object = Faculty.objects.filter(id=request.user.faculty_id)
        faculty_name = faculty_object[0].name
    if (Major.objects.filter(id=request.user.major_id).exists()):
        major_object = Major.objects.filter(id=request.user.major_id)
        major_name = major_object[0].name
    if (Classes.objects.filter(id=request.user.classes_id).exists()):
        classes_object = Classes.objects.filter(id=request.user.classes_id)
        classes_name = classes_object[0].name
    if SystemConfiguration.objects.filter(key='audit').exists():
        audit = SystemConfiguration.objects.filter(key='audit').first().value

    context['audit'] = audit
    context['faculty'] = faculty_name
    context['major'] = major_name
    context['classes'] = classes_name
    context['ORGANIZATION'] = ORGANIZATION

    return render(request, 'x_person/web/info.html', context)


@web_login_required
@find_menu(slug)
@teamuser_exit_user
def team(request, **kwargs):
    context = kwargs.get('menu')
    team_user = request.user.teamuser_set.filter(status=TeamUserStatus.JOIN).first()
    if team_user and request.user.team:
        t_id = request.user.team.id
        context['teamid'] = t_id
        context['recordid'] = team_user.id
        context['teamleader'] = team_user.team_leader
        return render(request, 'x_person/web/team.html', context)
    else:
        return join_team(request, **kwargs)


@web_login_required
@find_menu(slug)
def collect(request, **kwargs):
    context = kwargs.get('menu')
    return render(request, 'x_person/web/collect.html', context)


@web_login_required
@find_menu(slug)
def rank(request, **kwargs):
    context = kwargs.get('menu')
    if is_en(request):
        ORGANIZATION = ORGANIZATION_EN
    else:
        ORGANIZATION = ORGANIZATION_CN
    context['ORGANIZATION'] = ORGANIZATION
    return render(request, 'x_person/web/rank.html', context)


@web_login_required
@find_menu(slug)
@teamuser_exit_user
@team_leader_required
def team_edit(request, pk, **kwargs):
    context = kwargs.get('menu')
    team_user = request.user.teamuser_set.first()
    if not team_user:
        raise exceptions.NotAcceptable(OccupationError.NOT_FOUND_TEAM)
    context['teamid'] = int(pk)
    context['teamleader'] = team_user.team_leader
    return render(request, 'x_person/web/team_edit.html', context)


@web_login_required
@find_menu()
def index(request, **kwargs):
    context = kwargs.get('menu')
    try:
        practice_task_record = reverse('practice:get_personal_task_record')
    except:
        practice_task_record = None

    try:
        practice_task_radar = reverse('practice:task_radar_data')
    except:
        practice_task_radar = None

    context['practice_task_record'] = practice_task_record
    context['practice_task_radar'] = practice_task_radar

    return render(request, 'x_person/web/index.html', context=context)


@web_login_required
@find_menu(slug)
@one_user_one_team_required
def join_team(request, **kwargs):
    import json
    context = kwargs.get('menu')
    context['joined_team'] = json.dumps(
        [team_user.team_id for team_user in
         request.user.teamuser_set.all().filter(status=TeamUserStatus.NEED_JOIN, has_handle=False)])
    return render(request, 'x_person/web/join_team.html', context)


@web_login_required
@find_menu(slug)
@one_user_one_team_required
def create_team(request, **kwargs):
    context = kwargs.get('menu')
    return render(request, 'x_person/web/create_team.html', context)


@web_login_required
# @find_menu(slug)
@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def send_validate_email(request, user_id):
    user = User.objects.filter(id=user_id).first()
    if not user:
        raise exceptions.NotAcceptable(OccupationError.NOT_FOUND_USER)
    to_email = user.email
    code = random_str(16)
    email_title = "邮箱激活链接"
    url = request.build_absolute_uri(reverse('x_person:email_validate', kwargs={'user_id': user_id}))
    email_url = urljoin(url, code)

    email_body = "请点击下面的链接激活你的邮箱:" + email_url
    try:
        send_mail(email_title, email_body, DEFAULT_FROM_EMAIL, [to_email])
        return Response(status=status.HTTP_200_OK)

    except Exception as e:
        logger = logging.getLogger()
        logger.info(traceback.format_exc())
        logger.info(str(e))
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def random_str(randomlength):
    str = ''
    chars = '0123456789'
    length = len(chars) - 1
    random = Random()
    for i in range(randomlength):
        str += chars[random.randint(0, length)]
    return str


def email_validate(request, user_id):
    user = User.objects.get(id=user_id)
    user.email_validate = True
    user.save()
    return HttpResponseRedirect(reverse('x_person:info'))


@web_login_required
@find_menu()
@teamuser_exit_user
def index_new(request, **kwargs):
    context = kwargs.get('menu')
    return redirect(reverse('course_occupation:index_occupation'))
    # return render(request, 'x_person/web/index_new.html', context=context)


# 处理ad版本
@web_login_required
@find_menu()
@teamuser_exit_user
def index_ad(request, **kwargs):
    context = kwargs.get('menu')

    try:
        practice_task_record = reverse('practice:get_personal_task_record')
    except:
        practice_task_record = None

    try:
        practice_task_radar = reverse('practice:task_radar_data')
    except:
        practice_task_radar = None

    context['practice_task_record'] = practice_task_record
    context['practice_task_radar'] = practice_task_radar

    team_user = request.user.teamuser_set.filter(status=TeamUserStatus.JOIN).first()
    if team_user and request.user.team:
        context['teamid'] = request.user.team.id
        context['recordid'] = team_user.id
        context['teamleader'] = team_user.team_leader
    return render(request, 'x_person/web/index_ad.html', context=context)


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

    select_time = {'day': connection.ops.date_trunc_sql('day', 'time')}
    dict_time = {'user': request.user, 'time__gte': before_30_time}

    # 计算本月每天比赛记录 考试,解题赛
    event_sorces = EventUserSubmitLog.objects.filter(**dict_time).filter(is_solved=True).extra(
        select=select_time).values('day').annotate(score_sum=Sum('score'))
    for event_sorce in event_sorces:
        try:
            get_event_sorce_index = thirty_days.index(event_sorce['day'].strftime('%m-%d'))
        except ValueError:
            logging.info(
                'get_record_index Don\'t get the time index in thirty_days, that %s is not in list' % event_sorce[
                    'day'].strftime('%m-%d'))
            raise exceptions.NotAcceptable(OccupationError.TIME_INDEX_ERROR)
        dataMatch.append([get_event_sorce_index, event_sorce['score_sum'], event_sorce['score_sum'] + 200])

    data_thirty_days = get_30day_CompleteData(bubbleOption_data_30, dataCourse, dataPratice, dataMatch)
    if data_thirty_days.has_key('dataMatch'):
        dataMatch = data_thirty_days['dataMatch']

    data['dataCourse'] = dataCourse
    data['dataPratice'] = dataPratice
    data['dataMatch'] = dataMatch
    data['thirty_days'] = thirty_days

    return Response(data=data, status=status.HTTP_200_OK)