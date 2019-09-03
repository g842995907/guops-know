from __future__ import unicode_literals

import logging
import os
import uuid

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.http import QueryDict
from django.shortcuts import render, redirect, reverse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from common_auth.models import User
from common_framework.utils import views as default_views
from common_framework.utils.image import save_image
from common_framework.utils.rest.permission import IsStaffPermission
from x_tools.file_utils import handle_uploaded_file
from x_tools.models import Tool, ToolCategory, ToolComment
from x_tools.setting import api_settings

LOG = logging.getLogger(__name__)
slug = api_settings.SLUG


# @find_menu(slug)
@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def tool_list(request):
    categories = ToolCategory.objects.all()
    return render(request, 'x_tools/cms/tool_list.html', {"categories": categories})


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def tool_detail(request, tool_id):
    tool = Tool.objects.get(id=tool_id)
    knowledges_list = None

    if tool is None or tool.builtin == 1:
        return default_views.Http404Page(request, Exception())

    if tool.knowledges:
        knowledges_list = tool.knowledges.split(",")

    categories = ToolCategory.objects.all()
    return render(request, 'x_tools/cms/tool_detail.html',
                  {"tool": tool, "categories": categories,
                   "knowledges_list":knowledges_list})


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def tool_create(request, **kwargs):
    categories = ToolCategory.objects.all()
    return render(request, 'x_tools/cms/tool_detail.html',
                  {"categories": categories})


@api_view(['PUT', 'POST'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def custom_tool_detail(request, tool_id):
    if request.method == 'PUT':
        params = QueryDict(request.body)
        if "cover" in params:
            tool = Tool.objects.get(id=tool_id)
            if tool.cover:
                tool.cover.delete()
            tool.save()
        if "save_path" in params:
            tool = Tool.objects.get(id=tool_id)
            if tool.save_path:
                tool.save_path.delete()
            tool.save()
        return HttpResponse(None, status=200)
    elif request.method == 'POST':
        try:
            tool = Tool.objects.get(id=tool_id)

            name = request.POST.get("name")
            if name is not None:
                tool.name = name
            category = request.POST.get('category')
            if category is not None:
                tool.category = ",".join(request.POST.getlist('category'))
            cover = request.POST.get("cover")
            if cover is not None:
                tool.cover = save_image(cover)
            save_path = request.FILES.get("save_path")
            if save_path is not None:
                tool.save_path = save_path
            homepage = request.POST.get("homepage")
            if homepage is not None:
                tool.homepage = homepage
            size = request.POST.get("size")
            if size is not None:
                tool.size = size
            version = request.POST.get("version")
            if version is not None:
                tool.version = version
            language = request.POST.get('language')
            if language is not None:
                tool.language = ",".join(request.POST.getlist('language'))
            license_model = request.POST.get("license_model")
            if license_model is not None:
                tool.license_model = license_model
            introduction = request.POST.get("introduction")
            if introduction is not None:
                tool.introduction = introduction
            tool.public = True if request.POST.get("public") else False
            tool.online = True if request.POST.get("online") else False
            if tool.online:
                tool.platforms = "online"
            else:
                platforms = request.POST.get('platforms')
                if platforms is not None:
                    tool.platforms = ",".join(request.POST.getlist('platforms'))
            tool.save()
        except Exception, e:
            pass
        return HttpResponse(None, status=200)
    return HttpResponse(None, status=400)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def category_list(request):
    return render(request, 'x_tools/cms/category_list.html')


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def category_detail(request, category_id):
    category = ToolCategory.objects.get(id=category_id)
    return render(request, 'x_tools/cms/category_detail.html',
                  {"category": category})


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def category_create(request, **kwargs):
    if request.method == 'GET':
        return render(request, 'x_tools/cms/category_detail.html')


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def category_delete(request, category_id):
    ToolCategory.objects.get(id=category_id).delete()
    return redirect(reverse('cms_x_tools:category_list'))


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def comment_list(request):
    return render(request, 'x_tools/cms/comment_list.html')


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def comment_detail(request, comment_id):
    comment = ToolComment.objects.get(id=comment_id)
    users = User.objects.filter()
    tools = Tool.objects.filter()
    comments = ToolComment.objects.exclude(id=comment_id)
    return render(request, 'x_tools/cms/comment_detail.html',
                  {"parents": comments, "comment": comment, "tools": tools, "users": users})


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def comment_create(request, **kwargs):
    if request.method == 'GET':
        users = User.objects.filter()
        tools = Tool.objects.filter()
        comments = ToolComment.objects.filter()
        return render(request, 'x_tools/cms/comment_detail.html',
                  {"parents": comments, "tools": tools, "users": users})


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def comment_delete(request, comment_id):
    ToolComment.objects.get(id=comment_id).delete()
    return redirect(reverse('cms_x_tools:comment_list'))


def upload_image(request):
    image_file = request.FILES['image_file']
    img_name = str(uuid.uuid4()) + '.' + image_file.name.split('.')[-1]
    img_path = handle_uploaded_file(image_file, img_name, "tools")
    result = {
        'url': img_path
    }
    return JsonResponse(result, status=200)


def remove_image(request):
    if 'url' in request.POST:
        img_path = request.POST['url'].split(settings.MEDIA_URL)[1]
        img_path = os.path.join(getattr(settings, 'MEDIA_ROOT'), "tools", img_path)
        # TODO: Delete file

    return HttpResponse(None, status=200)

