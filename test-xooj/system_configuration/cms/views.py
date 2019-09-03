# -*- coding: utf-8 -*-
from __future__ import print_function

import cStringIO
import collections
import logging
import os
import random
import string
import time

import paramiko
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from django.http.response import HttpResponse
from django.utils.translation import gettext
from django.utils.translation import ugettext_lazy as _
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common_auth.models import Classes, Faculty
from common_framework.utils import views as default_views, license
from common_framework.utils.constant import Status
from common_framework.utils.request import is_en
from common_framework.utils.rest.permission import IsStaffPermission
from common_framework.utils.shortcuts import AppRender
from common_framework.utils.x_http.response import MultipleFileResponse
from common_scene.clients import nova_client, zun_client
from common_scene.setting import api_settings as common_scene_api_settings
from oj import settings
from oj.config import ORGANIZATION_EN, ORGANIZATION_CN
from system_configuration.models import SystemConfiguration, SysNotice
from system_configuration.setting import api_settings
from system_configuration.utils.loger import logset
from . import serializers as mserializers

render = AppRender('system_configuration', 'cms').render

logger = logging.getLogger(__name__)


def get_groups():
    groups = collections.OrderedDict()
    groups[gettext('x_all_user')] = 0
    groups[gettext('x_teacher_group')] = 1
    groups[gettext('x_student_group')] = 2
    groups[gettext('x_choose_class')] = 3

    return groups


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def system_configuration(request):
    context = {
        'system_name': license.get_system_config('system_name') or '',
        'copyright': license.get_system_config('copyright') or '',
        'person_env_count': license.get_system_config('person_env_count') or '',
        'public_register': license.get_system_config('public_register') or '',
        'audit': license.get_system_config('audit') or '',
        'version': license.get_system_config('version') or license.get_version("system_configuration"),
        'answer_prefix': license.get_system_config('answer_prefix') or '',
        'desktop_transmission_quality': license.get_system_config(
            'desktop_transmission_quality') or SystemConfiguration.DesktopTransmissionQuality.MIDDLE,
    }

    logo = license.get_system_config('logo')
    if logo:
        system_logo_path = os.path.join(settings.MEDIA_URL, 'system_logo')
        context['logo'] = os.path.join(system_logo_path, logo)
    else:
        context['logo'] = ''

    return render(request, 'system_configuration.html', context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def get_license(request):
    context = {}

    terminal_node_number = license.get_system_config('terminal_node_number')
    if terminal_node_number is not None:
        context['terminal_node_number'] = _("x_not_limited") if terminal_node_number == 0 else terminal_node_number
    else:
        context['terminal_node_number'] = 2

    context['all_env_count'] = license.get_system_config('all_env_count') or '0'
    context['deadline_time'] = license.get_system_config('deadline_time') or ''
    context['version'] = license.get_system_config('version') or license.get_version("system_configuration")

    return render(request, 'license.html', context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def backup_list(request):
    return render(request, 'backup_list.html')


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def factory_reset(request):
    return render(request, 'factory_reset.html')


def captcha(request):
    width = 147
    height = 49
    im = Image.new('RGB', (width, height), (255, 255, 255))

    def get_random_color():
        return random.randint(20, 100), random.randint(20, 100), random.randint(20, 100)

    def get_random_xy():
        x = random.randint(0, int(width))
        y = random.randint(0, int(height))
        return (x, y)

    fontstyle = os.path.join(settings.BASE_DIR, 'system_configuration/static/fonts/Arial.ttf')
    font = ImageFont.truetype(fontstyle, 47)

    rand_str_list = [random.choice(string.letters + string.digits) for _ in range(4)]

    # draw digits
    for i in range(4):
        ImageDraw.Draw(im).text(((i+1)*max(im.size)/6, 0), rand_str_list[i], font=font, fill=get_random_color())

    # draw noise
    for _ in range(random.randint(200, 1000)):
        ImageDraw.Draw(im).point((random.randint(0, width), random.randint(0, height)), fill=get_random_color())

    # draw line
    for i in range(6):
        ImageDraw.Draw(im).line([get_random_xy(), get_random_xy()], get_random_color())

    request.session['captcha'] = ''.join(rand_str_list).lower()
    im = im.filter(ImageFilter.BLUR)
    buf = cStringIO.StringIO()
    im.save(buf, 'jpeg')
    return HttpResponse(buf.getvalue(), 'image/jpeg')


class Hypervisor(object):
    _attrs = ['cpu_info', 'host_ip', 'human_id', 'hypervisor_hostname',
              'hypervisor_type', 'id', 'memory_mb', 'memory_mb_used',
              'running_vms', 'state', 'status', 'vcpus', 'vcpus_used',
              'local_gb', 'local_gb_used']
    _hypervisor = None

    def __init__(self, hypervisor):
        self._hypervisor = hypervisor

    def to_dict(self):
        obj = {}
        for key in self._attrs:
            obj[key] = getattr(self._hypervisor, key, None)
        return obj


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def operation_services(request):
    context = {}
    # 添加虚拟比例
    cpu_allocation_ratio = common_scene_api_settings.COMPLEX_MISC.get("cpu_allocation_ratio", 16.0)
    ram_allocation_ratio = common_scene_api_settings.COMPLEX_MISC.get("ram_allocation_ratio", 1.5)
    disk_allocation_ratio = common_scene_api_settings.COMPLEX_MISC.get("disk_allocation_ratio", 1.0)
    context['cpu_allocation_ratio'] = cpu_allocation_ratio
    context['ram_allocation_ratio'] = ram_allocation_ratio
    context['disk_allocation_ratio'] = disk_allocation_ratio
    zn_client = zun_client.Client()
    # 获取所有容器
    container_list = zn_client.container_list()
    # openstack hypervisor
    hyperv_list = []
    try:
        instance_count = 0
        vcpu_percent = 0.0
        ram_percent = 0.0
        disk_percent = 0.0
        instance_max = 100
        nv_client = nova_client.Client(project_name="admin")
        hypers = nv_client.hypervisor_list()
        for hyper in hypers:
            container_count = 0
            local_containers_count = 0
            instance_count += hyper.running_vms
            hyper.vcpus = hyper.vcpus * cpu_allocation_ratio
            vcpu_percent += float(hyper.vcpus_used) / float(hyper.vcpus)
            hyper.memory_mb = hyper.memory_mb * ram_allocation_ratio
            ram_percent += float(hyper.memory_mb_used) / float(hyper.memory_mb)
            hyper.local_gb = hyper.local_gb * disk_allocation_ratio
            disk_percent += float(hyper.local_gb_used) / float(hyper.local_gb)

            for container in container_list:
                if container.host == hyper.hypervisor_hostname:
                    container_count = container_count + 1
            if hyper.hypervisor_hostname.startswith("controller"):
                from common_scene.cms.views import get_local_dockers
                local_containers_count = len(get_local_dockers())

            hyper_dict = Hypervisor(hyper).to_dict()
            hyper_dict['container_count'] = container_count + local_containers_count
            hyperv_list.append(hyper_dict)

        hyper_count = len(hypers)
        context.update({"cluster_state": {
            "vms": instance_count,
            "vm_max": instance_max,
            "vcpu": vcpu_percent / hyper_count * 100,
            "ram": ram_percent / hyper_count * 100,
            "disk": disk_percent / hyper_count * 100,
        }})

    except Exception as e:
        pass
    context.update({"hypervisors": hyperv_list})
    return render(request, 'dashboard_services.html', context=context)


@api_view(['POST'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def hander_services_ssh(request):
    logger.info("Start operation and maintenance services ！！！ ")
    cmd = []  # 执行的命令
    ip = request.POST['ip']
    status = request.POST['status']
    clearall = request.POST['clearall']

    GetNumber = {
        'close': '1',
        'start': '2',
        'restart': '3',
        'clearall_restart': 'csan'
    }
    if ip:
        status = request.POST['status']
        cmd.append(ip)
        cmd.append(status)
    else:
        if clearall == 'true' and status == 'restart':
            cmd.append(GetNumber['clearall_restart'])
        elif GetNumber.has_key(status):
            cmd.append(GetNumber[status])
        else:
            logger.info('parameter error, ip, status, clearall not right')
            raise Exception('x_parameter_error')

    # cmd = ['10.10.52.32', 'close']
    # cmd = ['4']
    data = {}
    host_ip = api_settings.SSH_HOST_IP
    username = api_settings.SSH_USERNAME
    status = connect_ssh(host_ip, username, cmd)
    data['status'] = status
    logger.info("return web data about status[%s]", status)

    # return HttpResponse(json.dumps(data), content_type="application/json")
    return Response(data)


def connect_ssh(ip, username, cmd):
    try:
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        pkey_path = os.path.join(BASE_DIR, 'utils/id_rsa')
        logger.info('get pkey_path from utils id_rsa: pkey_path[%s]', pkey_path)
        pkey = paramiko.RSAKey.from_private_key_file(pkey_path)
        # paramiko.util.log_to_file('paramiko.log')  # 记录日志文件
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        logger.info('go to connect ssh')
        ssh.connect(hostname=ip,
                    port=22,
                    username=username,
                    pkey=pkey, timeout=5)
        logger.info("connect ssh success, ip[%s] username[%s], cmd[%s]", ip, username, cmd)
        # 执行命令
        stdin, stdout, stderr = ssh.exec_command('abc')  # 随便输入
        time.sleep(4)
        for m in range(len(cmd)):
            logger.info("get and exec cmd[%s]", cmd)
            stdin.write(cmd[m] + '\n')
            if (m + 1) != len(cmd):
                time.sleep(2)
        # 关闭连接
        ssh.close()
        return 'success'
    except Exception as e:
        return 'faile'


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def run_log(request):
    context = {'log_level': 2, 'log_size': 20, 'log_count': 5}

    log_level = SystemConfiguration.objects.filter(key='log_level').first()
    log_size = SystemConfiguration.objects.filter(key='log_size').first()
    log_count = SystemConfiguration.objects.filter(key='log_count').first()

    if log_level:
        context['log_level'] = int(log_level.value)

    if log_size:
        context['log_size'] = int(log_size.value)

    if log_count:
        context['log_count'] = int(log_count.value)

    return render(request, 'run_log.html', context=context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def down_log(request):
    sz_file = request.query_params.get('file')
    file_list = []
    log_parent_path = logset.get_log_parent_path()
    if sz_file:
        file_list = sz_file.split(',')

    file_list = [os.path.join(log_parent_path, a) for a in file_list]

    response = MultipleFileResponse(file_list,
                                    password=api_settings.LOG_ZIP_PASSWORD,
                                    content_type='application/x-zip-compressed')
    response['content-Disposition'] = 'attachment; filename=log.zip'
    return response


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def log(request):
    context = {}
    return render(request, 'log.html', context=context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def module(request):
    from common_product.module import get_all_module
    context = get_all_module()
    return Response(context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def sys_notice_list(request):
    context = {}
    return render(request, 'sys_notice_list.html', context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def sys_notice_detail(request, pk):
    if is_en(request):
        ORGANIZATION = ORGANIZATION_EN
    else:
        ORGANIZATION = ORGANIZATION_CN
    context = {
        'classes_list': Classes.objects.filter(status=Status.NORMAL),
        'faculty_list': Faculty.objects.filter(status=Status.NORMAL),
        'groups': get_groups(),
        'select': 3,
        'ORGANIZATION': ORGANIZATION,
    }
    pk = int(pk)
    if pk == 0:
        context['mode'] = 0
    else:
        try:
            sysNotice = SysNotice.objects.get(pk=pk)
        except SysNotice.DoesNotExist as e:
            return default_views.Http404Page(request, e)
        sysNotice = mserializers.SysNoticeSerializer(sysNotice).data
        context['mode'] = 1
        context['sysNotice'] = sysNotice

    return render(request, 'sys_notice_detail.html', context)
