# -*- coding: utf-8 -*-
from django.db.models import Q
from rest_framework.decorators import api_view

from common_framework.utils import views as default_views
from common_framework.utils.shortcuts import AppRender
from practice.api import get_task_event_by_type, PRACTICE_TYPE_MAN_MACHINE
from practice.constant import TaskEventStatus
from practice.models import TaskEvent
from practice_man_machine.cms.serializers import PracticeExerciseTaskSerializerForEdit
from practice_man_machine import models as task_models

render = AppRender('practice_man_machine', 'cms').render


@api_view(['GET',])
def task_list(request):
    if request.user.is_superuser:
        event_list = TaskEvent.objects.filter(type=int(PRACTICE_TYPE_MAN_MACHINE))
    else:
        event_list = TaskEvent.objects.filter(type=int(PRACTICE_TYPE_MAN_MACHINE)).filter(
            Q(share_teachers__in=[request.user]) | Q(create_user=request.user)).distinct()
    category_list = task_models.ManMachineCategory.objects.all()
    context = {
        'category_list': category_list,
        'event_list': event_list
    }
    return render(request, 'task_list.html', context)


def task_detail(request, pk):
    category_list = task_models.ManMachineCategory.objects.all()
    if request.user.is_superuser:
        event_list = TaskEvent.objects.filter(type=int(PRACTICE_TYPE_MAN_MACHINE))
    else:
        event_list = TaskEvent.objects.filter(type=int(PRACTICE_TYPE_MAN_MACHINE)).filter(
            Q(share_teachers__in=[request.user]) | Q(create_user=request.user)).distinct()
    context = {
        'category_list': category_list,
        'event_list': event_list
    }

    pk = int(pk)
    if pk == 0:
        context['mode'] = 0
    else:
        try:
            task = task_models.ManMachineTask.objects.get(pk=pk)
        except task_models.ManMachineTask.DoesNotExist as e:
            return default_views.Http404Page(request, e)

        context['mode'] = 1
        context['task'] = PracticeExerciseTaskSerializerForEdit(task).data

    return render(request, 'task_detail.html', context)


def category_list(request):
    return render(request, 'category_list.html')


def category_create(request, **kwargs):
    if request.method == 'GET':
        return render(request, 'category_detail.html')


def category_detail(request, category_id):
    category = task_models.ManMachineCategory.objects.get(id=category_id)
    return render(request, 'category_detail.html',
                  {"category": category})
