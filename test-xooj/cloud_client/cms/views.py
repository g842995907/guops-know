# -*- coding: utf-8 -*-

import operator
import os
import re
from datetime import datetime

import requests
from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from cloud_client.setting import api_settings
from common_framework.utils.rest.permission import IsStaffPermission
from common_framework.utils.x_logger import get_x_logger
from system_configuration.models import SystemConfiguration

logger = get_x_logger(__name__)


def get_can_update_info(ret_list, current_version):
    update_version = None
    current_version_num = version_num(current_version)


    for i in ret_list:
        version = i.get('name')
        if version:
            _version_num = version_num(version)
            if _version_num > current_version_num:
                update_version = i
            else:
                break

    return update_version


def sorted_by_time(ret_list):
    ret_list.sort(key=operator.itemgetter('create_time'), cmp=cmp_datetime)
    return ret_list

def cmp_datetime(a, b):
    a_datetime = datetime.strptime(a, '%Y-%m-%d %H:%M:%S')
    b_datetime = datetime.strptime(b, '%Y-%m-%d %H:%M:%S')

    if a_datetime > b_datetime:
        return -1
    elif a_datetime < b_datetime:
        return 1
    else:
        return 0

def version_num(version):
    version_split = version.split('.')
    ret = 0
    for n in version_split:
        ret = ret * 100 + int(n)
    return ret


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def update(request):
    current_version = get_version()

    context = {'version': current_version}
    #version_url = "http://127.0.0.1:8000/common_cloud/api/updates/"
    version_url = "http://%s/common_cloud/api/updates/" % api_settings.version_host
    version_host_net =  True

    try:
        comment = requests.get(version_url)
        data = comment.json()
    except Exception as e:
        logger.info("get_info_error msg[%s]", str(e))
        version_host_net = False
        data = []

    ret_list = []
    for u in data:
        u['change_log'] = u.get('change_log').split("\n")
        ret_list.append(u)

    need_update = 0
    update_info = None

    # 判断是否是要更新
    if len(ret_list) > 0:
        ret_list = sorted_by_time(ret_list)
        update_info = get_can_update_info(ret_list, current_version)
        if update_info:
            need_update = 1

    context['uis'] = ret_list
    context['current_update'] = update_info
    context['need_update'] = need_update
    context['version_host_net'] = version_host_net

    return render(request, 'cloud_client/cms/update_new.html', context)


def get_version():
    version = SystemConfiguration.objects.filter(key='version').first()
    if version:
        return version.value

    package = "system_configuration"
    init_py = open(os.path.join(package, '__init__.py')).read()
    version = re.search("__version__ = ['\"]([^'\"]+)['\"]", init_py).group(1)
    SystemConfiguration.objects.create(key='version', value=version)
    return version


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def update_detail(request, update_id):
    context = {'mode': 0}
    return render(request, 'cloud_client/cms/update_detail.html', context)
