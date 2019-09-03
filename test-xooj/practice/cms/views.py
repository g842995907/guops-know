# -*- coding: utf-8 -*-
import json

from django.db.models import Q
from django.http.response import JsonResponse
from django.urls import reverse
from rest_framework.decorators import permission_classes, api_view
from rest_framework.permissions import IsAuthenticated

from common_auth.constant import GroupType
from common_auth.models import User
from common_framework.utils import views as default_views
from common_framework.utils.rest.permission import IsStaffPermission
from common_framework.utils.shortcuts import AppRender
from practice import setting as api_settings
from practice import models as event_models
from practice.api import get_type_list, practice_types, get_category_by_type, OJ_PRACTICE_TYPE_LIST
from practice.cms.serializers import TaskEventSerializer
from django.conf import settings

render = AppRender('practice', 'cms').render


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def event_list(request):
    type_list = practice_types
    if settings.PLATFORM_TYPE == 'OJ':
        type_list = {key: type_list.get(key) for key in OJ_PRACTICE_TYPE_LIST}
    context = {
        'type_list': type_list,
        'debug': settings.DEBUG
    }
    return render(request, 'event_list.html', context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def event_detail(request, pk):
    type_list = practice_types
    if settings.PLATFORM_TYPE == 'OJ':
        type_list = {key: type_list.get(key) for key in OJ_PRACTICE_TYPE_LIST}
    context = {
        'type_list': type_list,
    }

    pk = int(pk)
    if pk == 0:
        context['mode'] = 0
    else:
        try:
            taskevent = event_models.TaskEvent.objects.get(pk=pk)
        except event_models.TaskEvent.DoesNotExist as e:
            return default_views.Http404Page(request, e)

        context['mode'] = 1
        context['event'] = TaskEventSerializer(taskevent).data
        context['event_object'] = taskevent

        if taskevent.builtin == 1:
            return default_views.Http404Page(request, Exception())

    return render(request, 'event_detail.html', context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def auth_class(request, event_id):
    from common_cms import views as cms_views
    context = {
        'url_list_url': reverse("cms_practice:event_list"),
        'query_auth_url': reverse("cms_practice:cms_api:task-event-get-auths", kwargs={'pk': event_id}),
        'query_all_auth_url': reverse("cms_practice:cms_api:task-event-get-all-auth", kwargs={'pk': event_id}),
        'modify_auth_url': reverse("cms_practice:cms_api:task-event-set-auths", kwargs={'pk': event_id}),
    }

    return cms_views.auth_class(request, context)



@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def share_teacher(request, event_id):
    from common_cms import views as cms_views
    context = {
        'url_list_url': reverse("cms_practice:event_list"),
        'query_share_url': reverse("cms_practice:cms_api:task-event-get-shares", kwargs={'pk': event_id}),
        'modify_share_url': reverse("cms_practice:cms_api:task-event-set-shares", kwargs={'pk': event_id}),
    }

    return cms_views.share_teacher(request, context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def practice_categories(request, type_id):
    try:
        type_id = int(type_id)
        categorys = get_category_by_type(type_id)
    except Exception, e:
        categorys = []
    return JsonResponse({"data": categorys})