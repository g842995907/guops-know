from __future__ import unicode_literals
import logging
import os

from django.http import StreamingHttpResponse
from django.shortcuts import render
from django.utils.http import urlquote

from rest_framework import generics

from common_framework.views import find_menu

from common_web.decorators import login_required
from common_framework.utils.constant import Status

from x_tools.models import Tool, ToolCategory, ToolComment
from x_tools.serializers import ToolSerializer
from x_tools.setting import api_settings


LOG = logging.getLogger(__name__)
slug = api_settings.SLUG


@login_required
@find_menu(slug)
def tool_list(request, **kwargs):
    context = kwargs.get('menu')
    categories = ToolCategory.objects.all()
    language = getattr(request, 'LANGUAGE_CODE', u'zh-hans')
    rows = []
    if language == 'zh-hans':
        for row in categories:
                rows.append({'id': row.id, "name": row.cn_name})
    else:
        for row in categories:
            rows.append({'id': row.id, "name": row.en_name})
    context.update({"categories": rows})
    return render(request, 'x_tools/web/tool_list.html', context)


@login_required
@find_menu(slug)
def tool_detail(request, **kwargs):
    context = kwargs.get('menu')
    tool_id = kwargs.get('tool_id')
    tool = Tool.objects.get(id=tool_id)
    serializer_data = ToolSerializer(tool).data
    context.update({"tool_id": tool_id,
                    'knowledges_list': serializer_data.get('knowledges_list')
                    })
    return render(request, 'x_tools/web/tool_detail.html', context)


@login_required
def tool_download(request, tool_id):
    tool = Tool.objects.get(id=tool_id)

    tool_file = tool.save_path.file
    ext = os.path.splitext(tool_file.name)[1]
    tool_name = "{}_{}{}".format(tool.name, tool.version, ext)
    response = StreamingHttpResponse(tool_file)
    response['Content-Type'] = 'application/octet-stream'
    response['Content-Disposition'] = 'attachment;filename="{}"'.format(urlquote(tool_name))
    return response


class ToolRecommandView(generics.ListAPIView):
    serializer_class = ToolSerializer

    def get_queryset(self):
        queryset = Tool.objects.filter(status=Status.NORMAL)
        # TODO: filter by category
        if len(queryset) > 2:
            return queryset[:2]
        return queryset

