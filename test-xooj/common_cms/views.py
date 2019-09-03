# -*- coding: utf-8 -*-

import os
import uuid

from django.contrib.admin.views.decorators import staff_member_required
from django.http.response import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.views.static import serve
from rest_framework import permissions, status, response, exceptions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from common_auth import api as auth_api
from common_cms.decorators import file_filter
from common_framework.utils.request import is_en
from common_framework.views import find_menu
from common_web.decorators import login_required
from common_web.x_markdown import MarkdownZip
from oj import settings
from oj.config import ORGANIZATION_EN, ORGANIZATION_CN


@require_http_methods(['GET'])
@login_required
@staff_member_required(login_url='/login/')
@find_menu(cms=True)
def index(request, **kwargs):
    context = kwargs.get('menu')
    return render(request, 'cms/index.html', context=context)


@api_view(['GET'])
@permission_classes((permissions.AllowAny,))
def media(request, path):
    return serve(request, path, document_root=settings.MEDIA_ROOT)


@api_view(['POST'])
@login_required
def upload_logo(request):
    if request.method == 'POST':
        file = request.FILES.get("file", None)
        logo_dir = 'tmp'

        dir_path = os.path.join(settings.MEDIA_ROOT, logo_dir)
        filename = str(uuid.uuid4()) + '.png'
        if not os.path.exists(dir_path):
            os.mkdir(dir_path)
        full_file_name = os.path.join(dir_path, filename)
        try:
            chunk = file.read()
            fileobj = open(full_file_name, 'wb')
            fileobj.write(chunk)
        except IOError:
            raise IOError
        finally:
            fileobj.close()

        # tmp_filename = os.path.join(logo_dir, filename)
        result = {
            'savepath': full_file_name
        }
        return Response(data=result, status=status.HTTP_200_OK)


def handle_uploaded_file(f, name, sub_folder=None):
    sub_path = getattr(settings, 'MEDIA_ROOT')
    return_path = getattr(settings, 'MEDIA_URL')
    if sub_folder:
        sub_path = os.path.join(sub_path, sub_folder)
        return_path = os.path.join(return_path, sub_folder)
        if not os.path.exists(sub_path):
            os.makedirs(sub_path)
    file_path = os.path.join(sub_path, name)
    return_path = os.path.join(return_path, name)
    with open(file_path, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

    return return_path


@api_view(['POST'])
@login_required
@file_filter(field_name='image_file')
def upload_image(request):
    image_file = request.FILES['image_file']
    suffix = image_file.name.split('.')[-1]
    if suffix == 'blob':
        suffix = 'png'
    img_name = str(uuid.uuid4()) + '.' + suffix
    img_path = handle_uploaded_file(image_file, img_name, "image")
    result = {
        'url': img_path
    }
    return JsonResponse(result, status=200)


@api_view(['POST'])
@login_required
def remove_image(request):
    if 'url' in request.POST:
        img_path = request.POST['url'].split(settings.MEDIA_URL)[1]
        img_path = os.path.join(getattr(settings, 'MEDIA_ROOT'), "image", img_path)
        # TODO: Delete file

    return HttpResponse(None, status=200)


def auth_class(request, context):
    if is_en(request):
        ORGANIZATION = ORGANIZATION_EN
    else:
        ORGANIZATION = ORGANIZATION_CN
    if context:
        context['facultys'] = auth_api.get_faculty()
        context['majors'] = auth_api.get_major()
        context['ORGANIZATION'] = ORGANIZATION

    return render(request, 'cms/auths.html', context)


def share_teacher(request, context):
    if context:
        context['teachers'] = auth_api.get_all_teachers()

    return render(request, 'cms/share.html', context)


def validate_example(request):
    return render(request, 'cms/validate_example.html')


@api_view(['POST'])
@login_required
def upload_markdown(request):
    zipfile = request.FILES.get("file", None)
    if not zipfile:
        raise exceptions.NotAcceptable(_('markdown_only_zip'))

    file_name = zipfile.name
    if os.path.splitext(file_name)[1] != ".zip":
        raise exceptions.NotAcceptable(_('markdown_only_zip'))

    md = MarkdownZip(zipfile)

    content = md.handle_markdown_zip()

    return response.Response({'error': 0, 'md': content})
