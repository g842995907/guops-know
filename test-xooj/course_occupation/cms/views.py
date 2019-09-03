# -*- coding: utf-8 -*-
import collections
import json
import logging

from django.core.cache import cache
from django.shortcuts import render, get_object_or_404
from django.utils.translation import gettext
from django.utils.translation import ugettext_lazy as _
from rest_framework import exceptions
from rest_framework.response import Response

from common_framework.utils.shortcuts import AppRender
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from common_framework.utils.rest.permission import IsStaffPermission
from course_occupation.cms.response import OCCUPATION_ERROR
from course_occupation.cms.serializers import OccupationSerializer

from course_occupation.models import OccupationSystem, OccupationCourse, OccupationLink
from course.models import Direction, Course
from common_framework.utils.constant import Status

app_render = AppRender('course_occupation', 'cms').render

logger = logging.getLogger(__name__)


def get_difficulty():
    difficulty = collections.OrderedDict()
    difficulty[_('x_primary')] = 1
    difficulty[_('x_intermediate')] = 2
    difficulty[gettext('x_senior')] = 3
    difficulty[gettext('x_hard')] = 4

    return difficulty


def course_get_difficulty():
    difficulty = collections.OrderedDict()
    difficulty[gettext('x_easy')] = 0
    difficulty[gettext('x_normal')] = 1
    difficulty[gettext('x_hard')] = 2

    return difficulty


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def occupation_list(request):
    """
    职位列表
    """
    context = {
        'difficulty': get_difficulty()
    }
    return render(request, 'course_occupation/cms/occupation_list.html', context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def occupation_detail(request, occupation_id):
    """
    职位详情
    :param occupation_id: 职位id
    """
    context = {
        'mode': 1,
    }
    occupation_id = int(occupation_id)
    if occupation_id == 0:
        context['mode'] = 0
    else:
        occupation_systemx = get_object_or_404(OccupationSystem, pk=occupation_id)
        context['OccupationSystem'] = occupation_systemx
        # 显示选中的进阶职位, related_name
        occupation_link = occupation_systemx.occupation.all()
        occupation_link_list = []

        for occ_link in occupation_link:
            occupation_link_list.append(occ_link.advanced.id)
        context['occupation_link_list'] = json.dumps(occupation_link_list)

    context['difficulty'] = get_difficulty()
    return render(request, 'course_occupation/cms/occupation_detail.html', context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def occupation_difficult(request):
    """
    职位详情中难度级别选择操作 进一步关联进阶职位
    """
    # 获取不同难度的进阶职位；
    occupation_id = request.GET.get('occupation_id', None)  # 新建还是编辑
    difficlut_id = request.GET.get('difficulty', None)  # 选择的难度
    queryset = OccupationSystem.objects.all()
    data = []
    if difficlut_id:
        data = OccupationSerializer(queryset.filter(difficulty__gt=int(difficlut_id)), many=True).data

    return Response(data=data)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def occupation_course_list(request, occupation_id):
    """
    职位课程管理--课程列表
    :param occupation_id:职位id
    :return:
    """
    occupation_id = int(occupation_id)
    occupationsystem_obj = OccupationSystem.objects.get(pk=occupation_id)
    # 模态框中的课程
    occupation_courses_ids = OccupationCourse.objects.values_list('course', flat=False).distinct()
    occupation_courses = Course.objects.filter(id__in=occupation_courses_ids)
    direction_ids = list(occupation_courses.values_list('direction', flat=True).distinct())
    sub_direction_ids = list(occupation_courses.values_list('sub_direction', flat=True).distinct())
    all_ids = direction_ids + sub_direction_ids
    all_directions = Direction.objects.filter(id__in=all_ids,status=Status.NORMAL)
    # all_directions = Direction.objects.filter(status=Status.NORMAL)

    context = {
        'occupation_id': occupation_id,
        'occupationsystem_obj': occupationsystem_obj,

        'difficulty': course_get_difficulty(),
        'directions': all_directions.filter(parent__isnull=True),
        'sub_directions': all_directions.filter(parent__isnull=False)
    }
    return render(request, 'course_occupation/cms/occupation_course_list.html', context)


@api_view(['POST'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def add_occupation_course(request, occupation_id):
    """
    职位课程管理---新增课程
    :param occupation_id: 职位id
    """
    occupation_id = int(occupation_id)
    course_ids = request.data.get('course_ids')
    logger.info('====> course_ids: {}'.format(course_ids))
    # occupation_system_obj = get_object_or_404(OccupationSystem, pk=occupation_id)
    # 获取所有已经存在的职业课程
    exist_course = OccupationCourse.objects.filter(occupation_system_id=occupation_id).values('course_id')
    copy_course_ids = []
    exist_course_id_list = []
    if exist_course:
        exist_course_id_list = [unicode(icourse['course_id']) for icourse in exist_course]
        logger.info('====> exist_course_id_list: {}'.format(exist_course_id_list))
        # 处理已经存在的课程
        for ids in course_ids:
            if ids not in exist_course_id_list:
                copy_course_ids.append(ids)
            else:
                raise exceptions.ValidationError(OCCUPATION_ERROR.REPEAT_ADDITION)
    else:
        copy_course_ids = course_ids
    logger.info('====> copy_course_ids: {}'.format(copy_course_ids))
    cache.clear()
    # 进行外键添加
    course_list = []
    for k, v in enumerate(copy_course_ids):
        occ_course_obj = OccupationCourse(
            occupation_system_id=occupation_id,
            course_id=int(v)
        )
        course_list.append(occ_course_obj)

    OccupationCourse.objects.bulk_create(course_list)
    return Response(data={'state', 'success'})