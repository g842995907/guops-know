# -*- coding: utf-8 -*-
from rest_framework.decorators import api_view

from common_framework.utils import views as default_views
from common_framework.utils.request import is_en
from common_framework.utils.shortcuts import AppRender
from common_framework.views import find_menu

from common_web.decorators import login_required
from event_exam.utils.user_action import ua
from event import models as event_models
from event_exam.setting import api_settings
from event_exam.models import ExamUserState, SolvedRecord
from event_exam.utils.exam_auth import exam_auth_class
from common_auth.models import User
from rest_framework.response import Response
from rest_framework import status
import time

from oj.config import ORGANIZATION_EN, ORGANIZATION_CN

base_render = AppRender('event', 'web').render
app_render = AppRender('event_exam', 'web').render

slug = api_settings.SLUG


@login_required
@find_menu(slug)
def exam(request, **kwargs):
    context = kwargs.get('menu')
    return app_render(request, 'exam.html', context)


@login_required
@find_menu(slug)
def list(request, **kwargs):
    context = kwargs.get('menu')
    context['type'] = api_settings.EVENT_TYPE
    return base_render(request, 'list.html', context)

@login_required
@find_menu(slug)
def list_new(request, **kwargs):
    context = kwargs.get('menu')
    context['type'] = api_settings.EVENT_TYPE
    return base_render(request, 'list_new.html', context)


@login_required
@find_menu(slug)
@exam_auth_class
def detail(request, pk, **kwargs):
    context = kwargs.get('menu')
    if is_en(request):
        ORGANIZATION = ORGANIZATION_EN
    else:
        ORGANIZATION = ORGANIZATION_CN
    try:
        exam = event_models.Event.objects.get(pk=pk)
        ua.event_exam(
            request.user,
            testpaper=exam.name
        )
        ######
        # score = event_models.Score.objects.get(pk=pk)
        ######
    except Exception, e:
        return default_views.Http404Page(request, e)

    context['pk'] = pk
    context['event'] = exam
    context['ORGANIZATION'] = ORGANIZATION
    ######
    # context['score'] = score
    ######
    # if exam.start_time < timezone.now():

    return app_render(request, 'detail.html', context)

@login_required
@find_menu(slug)
@exam_auth_class
def review(request, pk, **kwargs):
    context = kwargs.get('menu')
    if is_en(request):
        ORGANIZATION = ORGANIZATION_EN
    else:
        ORGANIZATION = ORGANIZATION_CN
    try:
        exam = event_models.Event.objects.get(pk=pk)
        ######
        # score = event_models.Score.objects.get(pk=pk)
        ######
    except Exception, e:
        return default_views.Http404Page(request, e)

    context['pk'] = pk
    context['event'] = exam
    context['ORGANIZATION'] = ORGANIZATION
    return app_render(request, 'review.html', context)


# 更新考试进行中表
@login_required
@api_view(['POST'])
@exam_auth_class
def update_status(request, pk):
    user_id = request.POST.get('user_id', int)
    event_id = pk
    state_list = ExamUserState.objects.filter(user__id=user_id).filter(event__id=event_id)
    # 从试卷中任取一个题目
    submit_log = SolvedRecord.objects.filter(user__id=user_id).filter(event__id=event_id)
    # 如果这个人这套题目已有答题记录，则不更新表
    if not submit_log:
        if state_list:
            ExamUserState.objects.filter(user__id=user_id).filter(event__id=event_id).delete()

        event = event_models.Event.objects.get(pk=pk)
        user = User.objects.get(pk=user_id)
        user_state = ExamUserState.objects.create(
            user=user,
            event=event,
        )
        user_state.save()
    return Response(data={'res': 'success'}, status=status.HTTP_200_OK)
