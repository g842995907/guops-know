# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django.http import HttpResponse
from django.shortcuts import render
from rest_framework.decorators import permission_classes, api_view
from rest_framework.permissions import IsAuthenticated

from common_framework.utils.rest.permission import IsStaffPermission
from x_note.models import Note
from x_note.models import RecordLoads
from x_note.setting import api_settings

LOG = logging.getLogger(__name__)
slug = api_settings.SLUG


# @find_menu(slug)
@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def note_list(request):
    return render(request, 'x_note/cms/note_list.html')


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def note_detail(request, note_id):
    note = Note.objects.get(id=note_id)
    context = {"note": note}
    return render(request, 'x_note/cms/note_detail.html', context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def getRecordLoadsStatus(request):
    slug = request.query_params.get('slug', None)
    if slug is None:
        raise ValueError(
            'slug must be need'
        )
    record_load_obj = RecordLoads.objects.filter(slug=slug).first()
    # 没有找到就是正在进行中
    if not record_load_obj:
        return HttpResponse(None, status=200)
    # 找到了只有成功和失败两个
    status = record_load_obj.status
    return HttpResponse(status, status=200)
