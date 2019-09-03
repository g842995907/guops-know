# -*- coding: utf-8 -*-
import json

import itertools
import xlrd
from django.contrib.auth.models import Group, Permission
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.html import escape
from django.utils.translation import ugettext_lazy as _
from rest_framework import status

from common_auth.constant import TeamUserStatus, GroupType
from common_auth.models import Faculty, Major, Classes, User
from common_framework.utils.request import is_en
from common_framework.utils.rest.permission import IsStaffPermission
from common_framework.utils.shortcuts import AppRender
from common_framework.utils import views as default_views
from common_auth import models as auth_model
from oj.config import ORGANIZATION_EN, ORGANIZATION_CN
from x_person.utils.product_type import get_product_type, get_edition
from . import serializers as m_serializers
from system_configuration.models import SystemConfiguration

render = AppRender('x_person', 'cms').render

@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def user_list(request):
    if is_en(request):
        ORGANIZATION = ORGANIZATION_EN
    else:
        ORGANIZATION = ORGANIZATION_CN
    product_type = get_product_type()
    faculty_list = Faculty.objects.all()
    major_list = Major.objects.all()
    classes_list = Classes.objects.all()
    superuser = 1 if request.user.is_superuser else 0
    staff = 1 if request.user.is_staff else 0
    context = {
        'ORGANIZATION': ORGANIZATION,
        'product_type': product_type,
        'faculty_list': faculty_list,
        'major_list': major_list,
        'classes_list': classes_list,
        'superuser': superuser,
        'staff': staff
    }
    return render(request, 'user_list.html', context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def user_detail(request, pk):
    def check_authority(user, allow_self=False):
        operate_user = request.user
        if user.id == operate_user.id:
            return True if allow_self else False
        if user.groups.filter(id=GroupType.ADMIN) or user.is_superuser:
            return False
        else:
            if user.groups.filter(id=GroupType.TEACHER):
                return True if operate_user.is_superuser or operate_user.groups.filter(id=GroupType.ADMIN) else False
            if user.groups.filter(id=GroupType.USER):
                return True if not operate_user.groups.filter(id=GroupType.USER) else False
        return False

    if is_en(request):
        ORGANIZATION = ORGANIZATION_EN
    else:
        ORGANIZATION = ORGANIZATION_CN

    product_type = get_product_type()
    faculty_list = Faculty.objects.all()
    major_list = Major.objects.all()
    classes_list = Classes.objects.all()

    edit_user = request.user
    # 如果操作人是超级管理员
    if edit_user.is_superuser:
        group_list = Group.objects.all()
    # 如果管理员操作自己
    elif edit_user.id == int(pk) and edit_user.groups.filter(id=GroupType.ADMIN):
        group_list = Group.objects.all()
    # 如果操作人是教员
    elif edit_user.is_staff:
        ids = [2, 3]
        group_list = Group.objects.all().filter(id__in=ids)
    # 如果操作人是学员
    else:
        ids = [3]
        group_list = Group.objects.all().filter(id__in=ids)

    # fan yi
    for g in group_list:
        g.name = _(g.name)
    context = {
        'product_type': product_type,
        'faculty_list': faculty_list,
        'major_list': major_list,
        'classes_list': classes_list,
        'group_list': group_list,
        'ORGANIZATION': ORGANIZATION,
    }

    if int(pk) == 0:
        # 如果是新增
        context['mode'] = 0
        context['default_group'] = _('x_student')
    else:
        try:
            user = auth_model.User.objects.get(pk=pk)
            if user.status == 0:
                return default_views.Http404Page(request, '')
            if not check_authority(user, True):
                return default_views.Http404Page(request, '')
            context['user'] = user
            context['majorId'] = user.major_id if user.major_id else -1
            context['classesId'] = user.classes_id if user.classes_id else -1
            if context['majorId'] != -1:
                context['major'] = Major.objects.filter(id=user.major_id).first().name
            if context['classesId'] != -1:
                context['classes'] = Classes.objects.filter(id=user.classes_id).first().name

        except auth_model.User.DoesNotExist as e:
            return default_views.Http404Page(request, e)
        context['mode'] = 1

        user_info = m_serializers.UserSerializer(user).data
        user_info['group_name'] = _(user_info['group_name'])
        context['userinfo'] = user_info

    return render(request, 'user_detail.html', context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def user_audit(request, pk):
    if is_en(request):
        ORGANIZATION = ORGANIZATION_EN
    else:
        ORGANIZATION = ORGANIZATION_CN
    product_type = get_product_type()
    faculty_list = Faculty.objects.all()
    major_list = Major.objects.all()
    classes_list = Classes.objects.all()
    group_list = Group.objects.all()

    for g in group_list:
        g.name = _(g.name)

    context = {
        'product_type': product_type,
        'faculty_list': faculty_list,
        'major_list': major_list,
        'classes_list': classes_list,
        'group_list': group_list,
        'ORGANIZATION': ORGANIZATION,
    }
    if int(pk) == 0:
        context['mode'] = 0
    else:
        try:
            user = auth_model.User.objects.get(pk=pk)
            context['user'] = user
            context['majorId'] = user.major_id if user.major_id else -1
            context['classesId'] = user.classes_id if user.classes_id else -1
            if context['majorId'] != -1:
                context['major'] = Major.objects.filter(id=user.major_id).first().name
            if context['classesId'] != -1:
                context['classes'] = Classes.objects.filter(id=user.classes_id).first().name

        except auth_model.User.DoesNotExist as e:
            return default_views.Http404Page(request, e)
        context['mode'] = 1
        context['userinfo'] = m_serializers.UserSerializer(user).data
    return render(request, 'audit_detail.html', context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def organization(request):
    product_type = get_edition()

    if is_en(request):
        ORGANIZATION = ORGANIZATION_EN
    else:
        ORGANIZATION = ORGANIZATION_CN

    context = {
        'product_type': product_type,
        'ORGANIZATION': ORGANIZATION,
    }
    system_configuration_list = SystemConfiguration.objects.filter(key="organization")
    if system_configuration_list:
        system_configuration = system_configuration_list.first()
        organization = system_configuration.value
    else:
        organization = "OJ Platform"
    Faculties = Faculty.objects.all()

    data = []
    row = {
        'id': "rootnode",
        'parent': '#',
        'text': organization,
        'type': 'root'
    }
    data.append(row)
    for faculty in Faculties:
        row = {
            'id': str(faculty.id),
            'parent': 'rootnode',
            'text': escape(faculty.name),
            'type': 'faculty'
        }
        data.append(row)

    majors = Major.objects.all()
    for major in majors:
        row = {
            'id': str(major.faculty.id) + ':' + str(major.id),
            'parent': str(major.faculty.id),
            'text': escape(major.name),
            'type': 'major'
        }

        data.append(row)

    classlist = Classes.objects.all()
    for classes in classlist:
        row = {
            'id': str(classes.major.faculty.id) + ':' + str(classes.major.id) + ':' + str(classes.id),
            'parent': str(classes.major.faculty.id) + ':' + str(classes.major.id),
            'text': escape(classes.name),
            'type': 'class'
        }
        data.append(row)
    # userlist=User.objects.all()
    # for user in userlist:
    #     row = {
    #         'id': str(user.classes.major.faculty.id) + ':' + str(user.classes.major.id) + ':' + str(user.classes.id) + str(user.id),
    #         'parent': str(user.classes.major.faculty.id) + ':' + str(user.classes.major.id)+ ':' + str(user.classes.id),
    #         'text': user.student_id,
    #         'type': 'studentID'
    #     }
    #     data.append(row)


    context['jstree'] = json.dumps(data)
    return render(request, 'organization.html', context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def team_list(request):
    return render(request, 'team_list.html')


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def team_detail(request, pk):
    context = {}
    if int(pk) == 0:
        context['mode'] = 0
        user = User.objects.filter(team=None).exclude(status=User.USER.DELETE)
        context['users'] = user
    else:
        try:
            team = auth_model.Team.objects.get(pk=pk)
        except auth_model.Team.DoesNotExist as e:
            return default_views.Http404Page(request, e)
        context['team'] = m_serializers.TeamSerializer(team).data
        team_user = auth_model.TeamUser.objects.filter(team=team, status=TeamUserStatus.JOIN)
        context['team_user'] = m_serializers.TeamUserSerializer(team_user, many=True).data
        context['mode'] = 1
    return render(request, 'team_detail.html', context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def group_list(request):
    return render(request, 'group_list.html')


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def group_detail(request, pk):
    permissions = Permission.objects.all()
    permissions = m_serializers.PermissionSerializer(permissions, many=True).data
    groups = itertools.groupby(permissions, lambda x: x['content_type'])
    permissions = []

    for m, n in groups:
        permissions.append(list(n))
    max_group_length = max(map(lambda x: len(x), permissions))
    context = {
        'permission_col_range': range(max_group_length),
        'permissions': permissions,
    }

    try:
        group = Group.objects.get(pk=pk)
    except Group.DoesNotExist as e:
        return default_views.Http404Page(request, e)
    context['group'] = m_serializers.GroupSerializer(group).data
    return render(request, 'group_detail.html', context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def multi_users(request):
    context = {}
    return render(request, 'multi_users.html', context)
