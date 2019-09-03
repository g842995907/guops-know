# -*- coding: utf-8 -*-
import json
import urllib

from django.conf import settings

from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.reverse import reverse

from common_framework.utils.delay_task import new_task

from .managers import RemoteManager, GuacamoleServer
from .models import RecordingConvertTask
from .setting import api_settings


@api_view(['GET'])
@permission_classes([IsAuthenticated,])
def connection_info(request, connection_id):
    data = {
        'is_enable_recording': RemoteManager().is_enable_recording(connection_id),
    }
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated,])
def enable_recording(request, connection_id):
    RemoteManager().enable_recording(connection_id)
    return Response({})


@api_view(['POST'])
@permission_classes([IsAuthenticated,])
def disable_recording(request, connection_id):
    remote_manager = RemoteManager()
    recording_name = remote_manager.get_recording_name(connection_id)
    remote_manager.disable_recording(connection_id)
    return Response({'recording_name': recording_name})


def delay_convert_callback(recording_name, screen_size, convert_func, convert_params):
    video_names = GuacamoleServer.scan_recording(recording_name)
    convert_func(video_names, screen_size, **convert_params)


@api_view(['POST'])
@permission_classes([IsAuthenticated,])
def recording_convert(request):
    host_ip = request.data.get('host_ip')
    convert_key = request.data.get('convert_key')
    convert_params = json.loads(request.data.get('convert_params', '{}'))
    recording_name = request.data.get('recording_name')
    screen_size = request.data.get('screen_size') or '1366x768'
    if not convert_key or not recording_name or not isinstance(convert_params, dict):
        raise PermissionDenied()

    convert_func = api_settings.RECORDING_CONVERT_CALLBACK.get(convert_key)
    if not convert_func:
        raise PermissionDenied()

    def tmp_task():
        remote_manager = RemoteManager(host=host_ip)
        callback_script = ''
        if host_ip and host_ip != api_settings.OJ_SERVER['host_ip']:
            executor = {
                'func': delay_convert_callback,
                'params': {
                    'recording_name': recording_name,
                    'screen_size': screen_size,
                    'convert_func': convert_func,
                    'convert_params': convert_params,
                }
            }
            condition = RecordingConvertTask.dump_executor(executor)
            task = RecordingConvertTask.objects.filter(**condition).first()
            if not task:
                task = RecordingConvertTask.objects.create(extra=executor.get('extra', ''), **condition)
            callback_url = settings.SERVER_HOST + reverse('common_remote:recording_convert_over', (task.id,))
            callback_script = 'curl {callback_url}'.format(callback_url=callback_url)
        video_names = remote_manager.convert_recording(recording_name, screen_size=screen_size, callback_script=callback_script)
        convert_func(video_names, screen_size, **convert_params)
    new_task(tmp_task, 0, ())

    return Response({})


@api_view(['GET'])
@permission_classes([AllowAny,])
def recording_convert_over(request, task_id):
    try:
        task = RecordingConvertTask.objects.get(pk=task_id)
    except RecordingConvertTask.DoesNotExist as e:
        raise PermissionDenied()

    task.execute()

    return Response({})


@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def login_guacamoles(request):
    login_res = {}
    for server in api_settings.GUACAMOLE_SERVERS:
        content = RemoteManager(request.user, server=server['server']).login_guacamole()
        login_res[server['public_server']] = urllib.quote(content) if content else None
    return Response(login_res)
