# -*- coding: utf-8 -*-
import json
import os

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.urls import reverse
from django.utils.translation import ugettext
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from rest_framework import status, response
from common_framework.utils import views as default_views
from common_framework.utils.rest.permission import IsStaffPermission
from common_framework.utils.shortcuts import AppRender
from common_scene.setting import api_settings as scene_api_settings

from .. import models as env_models
from ..handlers.config import EnvConfigHandler
from ..setting import api_settings
from . import serializers as mserializers

import logging
from oj import settings

import xlwt
from collections import Counter

render = AppRender('common_env', 'cms').render
LOG = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def active_env_list(request):
    context = {'DEBUG': settings.DEBUG}
    return render(request, 'active_env_list.html', context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def env_list(request):
    context = {'DEBUG': settings.DEBUG}
    return render(request, 'env_list.html', context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def env_detail(request, pk):
    context = {
        'DEBUG': settings.DEBUG,
        'server_number_limit': EnvConfigHandler.get_terminal_number_limit(),
    }
    pk = int(pk)
    if pk == 0:
        context['mode'] = 0
    else:
        try:
            env = env_models.Env.objects.get(pk=pk)
        except env_models.Env.DoesNotExist as e:
            return default_views.Http404Page(request, e)

        if env.builtin == 1:
            return default_views.Http404Page(request, Exception())

        context['mode'] = 1
        env_data = mserializers.EnvSerializer(env).data
        dumped_attacker_list = json.dumps(env_data['attacker_list'])
        context['env'] = env_data
        context['dumped_attacker_list'] = dumped_attacker_list

    server_number_limit = EnvConfigHandler.get_terminal_number_limit()
    sence_terminator_tip = ugettext('x_sence_terminator_count') % {'count':server_number_limit}
    context['sence_terminator_tip'] = sence_terminator_tip
    return render(request, 'env_detail.html', context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def env_attacker_list(request):
    context = {}
    return render(request, 'env_attacker_list.html', context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def env_attacker_detail(request, pk):
    context = {}
    pk = int(pk)
    if pk == 0:
        context['mode'] = 0
    else:
        try:
            envattacker = env_models.EnvAttacker.objects.get(pk=pk)
        except env_models.EnvAttacker.DoesNotExist as e:
            return default_views.Http404Page(request, e)

        if envattacker.builtin == 1:
            return default_views.Http404Page(request, Exception())

        context['mode'] = 1
        context['envattacker'] = mserializers.EnvAttackerSerializer(envattacker).data

    return render(request, 'env_attacker_detail.html', context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def standard_device_list(request):
    context = {}
    flavor_map = {flavor: text for flavor, text in api_settings.FLAVOR_INFO}
    context['flavor_map'] = json.dumps(flavor_map, cls=DjangoJSONEncoder)
    return render(request, 'standard_device_list.html', context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def standard_device_detail(request, pk):
    context = {
        'DEBUG': settings.DEBUG,
        'image_ftp_address': settings.SERVER_INTERNET_IP,
        'image_ftp_port': scene_api_settings.COMPLEX_MISC['ftp_proxy_port'],
        'disk_format_info': api_settings.DISK_FORMAT_INFO,
        'disk_controller_info': api_settings.DISK_CONTROLLER_INFO,
        'virtual_network_interface_device_info': api_settings.VIRTUAL_NETWORK_INTERFACE_DEVICE_INFO,
        'video_image_driver_info': api_settings.VIDEO_IMAGE_DRIVER_INFO,
    }
    pk = int(pk)
    if pk == 0:
        context['mode'] = 0
    else:
        try:
            standard_device = env_models.StandardDevice.objects.get(pk=pk)
        except env_models.StandardDevice.DoesNotExist as e:
            return default_views.Http404Page(request, e)

        if standard_device.builtin == 1:
            return default_views.Http404Page(request, Exception())

        context['mode'] = 1
        context['standard_device'] = mserializers.StandardDeviceSerializer(standard_device).data

    default_logos = []
    for logo_name in os.listdir(api_settings.FULL_DEFAULT_DEVICE_LOGO_DIR):
        default_logos.append(
            (logo_name, os.path.join(settings.MEDIA_URL, api_settings.DEFAULT_DEVICE_LOGO_DIR, logo_name)))
    context['default_logos'] = default_logos

    return render(request, 'standard_device_detail.html', context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def share_teacher(request, event_id):
    from common_cms import views as cms_views
    context = {
        'url_list_url': reverse("cms_common_env:env_list"),
        'query_share_url': reverse("cms_common_env:api:env-get-shares", kwargs={'pk': event_id}),
        'modify_share_url': reverse("cms_common_env:api:env-set-shares", kwargs={'pk': event_id}),
    }

    return cms_views.share_teacher(request, context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def share_standard_device_teacher(request, event_id):
    from common_cms import views as cms_views
    context = {
        'url_list_url': reverse("cms_common_env:standard_device_list"),
        'query_share_url': reverse("cms_common_env:api:standard-device-get-shares", kwargs={'pk': event_id}),
        'modify_share_url': reverse("cms_common_env:api:standard-device-set-shares", kwargs={'pk': event_id}),
    }

    return cms_views.share_teacher(request, context)


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def dump_env_data(request):
    queryset = env_models.Env.objects.all().extra(select={'date': "DATE_FORMAT(create_time,'%%Y%%m%%d')"})
    fail_envs = queryset.exclude(Q(error__isnull=True) | Q(error='')).order_by('create_time')
    # 所有场景按天统计
    env_statistics = [('日期', '成功场景数', '失败场景数', '失败率')]

    full_dates = list(queryset.values_list('date', flat=True))
    fail_dates = list(fail_envs.values_list('date', flat=True))
    full_times_perday = Counter(full_dates)
    fail_times_perday = Counter(fail_dates)
    dates = list(set(full_dates))
    dates.sort(key=full_dates.index)
    for date in dates:
        full_time = full_times_perday[date]
        fail_time = fail_times_perday[date]
        fail_rate = float(fail_time) / full_time
        env_statistics.append((date, full_time - fail_time, fail_time, '%.2f%%' % (fail_rate * 100)))

    fail_sum = len(fail_dates)
    success_sum = len(full_dates) - fail_sum
    fail_rate = float(fail_sum) / len(full_dates)
    env_statistics.append(('统计', success_sum, fail_sum, '%.2f%%' % (fail_rate * 100)))

    # 所有失败场景数据分析
    fail_env_statistics = [('日期', '失败场景名', '场景归属', '失败信息')]
    for env in fail_envs:
        for func in api_settings.GET_ENV_TARGET_FUNCS:
            belong_target = func(env.id)
            if belong_target:
                break
        env_belongto = '{}/{}/{}'.format(belong_target['app'], belong_target['type'], belong_target['name']) if belong_target else ''
        fail_env_statistics.append((str(env.create_time), env.name, env_belongto, env.error))

    # 失败场景各自失败的次数
    fail_env_rate = [('失败场景名', '失败次数', '失败率')]
    fail_env_counter = Counter(fail_envs.values_list('name', flat=True))
    full_env_counter = Counter(queryset.values_list('name', flat=True))
    for key, value in full_env_counter.items():
        failed_rate = float(fail_env_counter[key]) / value
        if float(failed_rate) > 0:
            fail_env_rate.append((key, fail_env_counter[key], '%.2f%%' % (failed_rate * 100)))

    # 将数据写进表格
    file = xlwt.Workbook(encoding='utf-8', style_compression=0)
    signcondition = 'str(word).upper()==str(word) and str(word).endswith("%") and float(str(word).replace("%",""))>=50'
    write_sheet_data(file=file, sheetname='场景统计', datalist=env_statistics, signcondition=signcondition)
    write_sheet_data(file=file, sheetname='失败场景详情', datalist=fail_env_statistics)
    write_sheet_data(file=file, sheetname='失败场景统计', datalist=fail_env_rate, signcondition=signcondition)

    path = 'media/word/envs.xls'
    file.save(path)

    return response.Response({'status': status.HTTP_200_OK, 'url': path})


def write_sheet_data(file, sheetname='sheet', datalist=[], signcondition='1 > 2'):
    import xlwt
    style = xlwt.XFStyle()
    font = xlwt.Font()
    font.colour_index = 2
    style.font = font
    if hasattr(file, 'add_sheet'):
        sheet = file.add_sheet(sheetname, cell_overwrite_ok=True)
        for col, data in enumerate(datalist):
            for row, word in enumerate(data):
                if eval(signcondition):
                    sheet.write(col, row, word, style)
                else:
                    sheet.write(col, row, word)
    else:
        raise Exception('file is not an excel')



