# -*- coding: utf-8 -*-
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from common_framework.utils import views as default_views
from common_framework.utils.rest.permission import IsStaffPermission
from common_framework.utils.shortcuts import AppRender
from practice.api import get_task_event_by_type, PRACTICE_TYPE_EXCRISE
from practice.constant import TaskEventStatus
from practice.models import TaskEvent
from practice_exercise.cms.serializers import PracticeExerciseTaskSerializerForEdit
from practice_exercise import models as task_models

render = AppRender('practice_exercise', 'cms').render


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def task_list(request):
    category_list = task_models.PracticeExerciseCategory.objects.all()
    if request.user.is_superuser:
        event_list = TaskEvent.objects.filter(type=int(PRACTICE_TYPE_EXCRISE))
    else:
        event_list = TaskEvent.objects.filter(type=int(PRACTICE_TYPE_EXCRISE)).filter(
            Q(share_teachers__in=[request.user]) | Q(create_user=request.user)).distinct()
    context = {
        'category_list': category_list,
        'event_list': event_list
    }
    return render(request, 'task_list.html', context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def task_detail(request, pk):
    category_list = task_models.PracticeExerciseCategory.objects.all()
    if request.user.is_superuser:
        event_list = TaskEvent.objects.filter(type=int(PRACTICE_TYPE_EXCRISE))
    else:
        event_list = TaskEvent.objects.filter(type=int(PRACTICE_TYPE_EXCRISE)).filter(
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
            task = task_models.PracticeExerciseTask.objects.get(pk=pk)
        except task_models.PracticeExerciseTask.DoesNotExist as e:
            return default_views.Http404Page(request, e)

        if task.builtin == 1:
            return default_views.Http404Page(request, Exception())

        context['mode'] = 1
        context['task'] = PracticeExerciseTaskSerializerForEdit(task).data

    return render(request, 'task_detail.html', context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def category_list(request):
    return render(request, 'category_list.html')


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def category_create(request, **kwargs):
    if request.method == 'GET':
        return render(request, 'category_detail.html')


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def category_detail(request, category_id):
    category = task_models.PracticeExerciseCategory.objects.get(id=category_id)
    return render(request, 'category_detail.html',
                  {"category": category})
