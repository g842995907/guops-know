# -*- coding: utf-8 -*-
import hashlib
import uuid
import pyminizip as pyminizip

import os
from django.conf import settings
from django.http import StreamingHttpResponse
from rest_framework.decorators import permission_classes, api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework import response

from common_framework.utils.enum import Enum
from common_framework.utils.zip import Ziper
from common_framework.utils.http import HttpClient
from common_framework.utils.rest.permission import IsStaffPermission
from common_framework.utils.x_http.response import MultipleFileResponse
from common_framework.utils.x_logger import get_x_logger
from event.models import EventWriteup

from event.setting import api_settings

vis_request_url = Enum(
    QUERY='http://{}/api/channel_started'.format(settings.CHECK_VIS_HOST),
    START='http://{}/api/create_start_channel'.format(settings.CHECK_VIS_HOST),
    STOP='http://{}/api/stop_delete_channel'.format(settings.CHECK_VIS_HOST),
)

vis_request_type = Enum(
    START=1,
    STOP=2,
)

vis_status = Enum(
    STARTED=1,
    STOPED=2,
    ERROR=3,
)

logger = get_x_logger(__name__)


@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def vis_control(request):
    try:
        if request.method == "GET":
            event_id = request.query_params.get("event_id")
            channel_id = 'AD3_{}_LIVE'.format(event_id)
            res = http_vis_request(vis_request_url.QUERY, channel_id=channel_id)

        elif request.method == "POST":
            event_id = request.POST.get("event_id")
            channel_id = 'AD3_{}_LIVE'.format(event_id)
            action = int(request.POST.get("action", -1))

            res = {"error": 'default'}

            if action == vis_request_type.START:
                res = http_vis_request(vis_request_url.START, channel_id=channel_id)
            elif action == vis_request_type.STOP:
                res = http_vis_request(vis_request_url.STOP, channel_id=channel_id)

            logger.info("vis server respon [%s]", res)

        return response.Response(res)
    except Exception as e:
        logger.error("vis server error %s", e)
        return response.Response({"vis_status": "error"})


def query_vis_status(event_id):
    try:
        channel_id = 'AD3_{}_LIVE'.format(event_id)
        res = http_vis_request(vis_request_url.QUERY, channel_id=channel_id)
        if res.get('status', -1) == 0 and res.get('data', False):
            return vis_status.STARTED
        return vis_status.STOPED
    except Exception as e:
        logger.error("vis server error %s", e)
        return vis_status.ERROR


def http_vis_request(url, **kwargs):
    vis_user = api_settings.VIS_USER
    vis_password = api_settings.VIS_PASSWORD

    api_key = '{user}:{key}'.format(
        user=vis_user,
        key=hashlib.md5(vis_password).hexdigest()
    )

    json = {
        'api_key': api_key,
    }

    for p in kwargs:
        json[p] = kwargs[p]

    http = HttpClient(settings.VIS_HOST, timeout=5)
    res = http.mpost(url, json=json)
    res_data = http.result(res, True)
    return res_data


def stop_vis(event):
    try:
        res = http_vis_request(vis_request_url.STOP, channel_id=event.id)
        return res
    except Exception as e:
        logger.error("stop vis error msg[%s]", str(e))
        return {'status': 'ok'}


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def download_ap(request, pk, **kwargs):
    import shutil
    wps = EventWriteup.objects.filter(event=pk)
    file_list = []
    dir_path = "/tmp/{}".format(uuid.uuid4())
    os.mkdir(dir_path)

    for wp in wps:
        if wp.user.first_name:
            user_file_name = str(wp.user.first_name + '-' + wp.writeup.name.split('/')[1])
        else:
            user_file_name = str(wp.user.username + '-' + wp.writeup.name.split('/')[1])

        shutil.copyfile(os.path.join(settings.MEDIA_ROOT, wp.writeup.name), os.path.join(dir_path, user_file_name))
        file_list.append(os.path.join(settings.MEDIA_ROOT, wp.writeup.name))

    tmp_name = "/tmp/{}".format(str(uuid.uuid4()))
    if len(file_list) == 0:
        _zip_o = Ziper()
        content = _zip_o.read()
    else:
        shutil.make_archive(tmp_name, 'zip', dir_path)
        shutil.rmtree(dir_path)

    response = StreamingHttpResponse(file_iterator(tmp_name + '.zip'))
    response['content_type'] = 'application/x-zip-compressed'
    response['content-Disposition'] = 'attachment; filename=wp.zip'
    return response


def file_iterator(file_name, chunk_size=512):
    with open(file_name) as f:
        while True:
            c = f.read(chunk_size)
            if c:
                yield c
            else:
                break
        os.remove(file_name)