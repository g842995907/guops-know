# -*- coding: utf-8 -*-
import os
import pyminizip
import uuid

from django.utils.translation import ugettext as _
from rest_framework import exceptions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from base.utils import license
from base_scene import setting
from base_cloud.compute.views import InstanceAction
from base_scene.models import SceneTerminal
from system.cms.serializers import InstanceListSerializer
from system.models import SystemConfiguration
from system.utils import logset
from base.utils.response import TmpFileResponse
from system.utils.list_view import list_view
from base_auth.utils.rest.permissions import IsAdmin
from system import settings as api_settings


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsAdmin))
def get_license(request):
    context = {}

    terminal_node_number = license.get_system_config('terminal_node_number')
    if terminal_node_number is not None:
        context['terminal_node_number'] = _("x_not_limited") if terminal_node_number == 0 else terminal_node_number
    else:
        context['terminal_node_number'] = 2

    context['all_env_count'] = license.get_system_config('all_env_count') or '0'
    context['deadline_time'] = license.get_system_config('deadline_time') or ''
    context['version'] = license.get_system_config('version') or license.get_version("system")

    return Response(data=context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsAdmin))
def run_log_level(request):
    context = {'log_level': 2, 'log_size': 10, 'log_count': 10}

    log_level = SystemConfiguration.objects.filter(key='log_level').first()
    log_size = SystemConfiguration.objects.filter(key='log_size').first()
    log_count = SystemConfiguration.objects.filter(key='log_count').first()

    if log_level:
        context['log_level'] = int(log_level.value)

    if log_size:
        context['log_size'] = int(log_size.value)

    if log_count:
        context['log_count'] = int(log_count.value)

    return Response(data=context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsAdmin))
def down_log(request):
    sz_file = request.query_params.get('file')
    if not sz_file:
        raise exceptions.ValidationError({"file not none"})

    file_list = []
    log_parent_path = logset.get_log_parent_path()
    if sz_file:
        file_list = sz_file.split(',')

    file_list = [os.path.join(log_parent_path, a) for a in file_list]

    # 创建加密文件路径
    tmp_name = "/tmp/{}.zip".format(str(uuid.uuid4()))
    pyminizip.compress_multiple(file_list, [], tmp_name, api_settings.LOG_ZIP_PASSWORD, 4)
    response = TmpFileResponse(tmp_name)
    response['content-Disposition'] = 'attachment; filename=log.zip'
    return response


# 计算实例
@api_view(['GET'])
@permission_classes((IsAuthenticated, IsAdmin))
def get_instance_list(request):
    try:
        data = InstanceAction().get_instance_list_by_name(setting.BASE_GROUP_NAME)
        res_list = []

        if not len(data) == 0:
            for instance in data:
                scene_instance = SceneTerminal.objects.filter(scene_id=instance.id).first()
                if scene_instance:
                    create_user = scene_instance.scene.user.first_name
                else:
                    create_user = ''

                networks_contain = hasattr(instance, 'networks')
                address = ''
                if networks_contain:
                    network_list = instance.networks
                    if network_list:
                        for key in network_list:
                            address = "&nbsp;".join(instance.networks.get(key, None))
                    else:
                        address = ''
                else:
                    address = ''

                node = instance._info.get('OS-EXT-SRV-ATTR:host', 'None')
                res_dict = {
                    'id': instance.id,
                    'status': instance.status,
                    'name': instance.name,
                    'server_ip': address,
                    'create_time': instance.created,
                    'node': node,
                    'create_user': create_user,

                }
                image_id = instance.image.get('id', None)
                if image_id:
                    image_name = None
                else:
                    image_name = None
                res_dict['server_image'] = image_name
                res_list.append(res_dict)
    except Exception as e:
        raise e
    return list_view(request, res_list, InstanceListSerializer)
