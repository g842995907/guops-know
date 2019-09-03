# -*- coding: utf-8 -*-
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from common_framework.utils import views as default_views
from common_framework.utils.rest.permission import IsStaffPermission
from common_framework.utils.shortcuts import AppRender
from practice.api import PRACTICE_TYPE_ATTACK_DEFENSE
from practice.models import TaskEvent
from practice_attack_defense import models as task_models
from practice_attack_defense.cms.serializers import PracticeAttackDefenseTaskSerializerForEdit

render = AppRender('practice_attack_defense', 'cms').render


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def task_list(request):
    category_list = task_models.PracticeAttackDefenseCategory.objects.all()
    if request.user.is_superuser:
        event_list = TaskEvent.objects.filter(type=int(PRACTICE_TYPE_ATTACK_DEFENSE))
    else:
        event_list = TaskEvent.objects.filter(type=int(PRACTICE_TYPE_ATTACK_DEFENSE)).filter(
            Q(share_teachers__in=[request.user]) | Q(create_user=request.user)).distinct()
    context = {
        'category_list': category_list,
        'event_list': event_list
    }
    return render(request, 'task_list.html', context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def task_detail(request, pk):
    category_list = task_models.PracticeAttackDefenseCategory.objects.all()
    if request.user.is_superuser:
        event_list = TaskEvent.objects.filter(type=int(PRACTICE_TYPE_ATTACK_DEFENSE))
    else:
        event_list = TaskEvent.objects.filter(type=int(PRACTICE_TYPE_ATTACK_DEFENSE)).filter(
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
            task = task_models.PracticeAttackDefenseTask.objects.get(pk=pk)
        except task_models.PracticeAttackDefenseTask.DoesNotExist as e:
            return default_views.Http404Page(request, e)

        context['mode'] = 1
        context['task'] = PracticeAttackDefenseTaskSerializerForEdit(task).data

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
    category = task_models.PracticeAttackDefenseCategory.objects.get(id=category_id)
    return render(request, 'category_detail.html',
                  {"category": category})
