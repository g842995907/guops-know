import requests
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.html import escape
from rest_framework import response
from rest_framework import serializers
from rest_framework.decorators import permission_classes, api_view
from rest_framework.permissions import AllowAny

from common_cloud.models import UpdateInfo
from common_cloud.setting import api_settings
from common_framework.utils.constant import Status


def post_comment(request):
    params = request.POST
    post_url = "http://{}/x_comment/api/comments/".format(api_settings.CLOUD_CENTER)
    try:
        logo = request.user.logo.url
    except:
        logo = ""

    hash = params.get("hash")
    theme_name = None

    category = hash.split(".")[1]
    if category in ["course", 'lesson'] and settings.PLATFORM_TYPE != 'AD':
        from course.models import Course, Lesson
        cls_model = category == 'course' and Course or Lesson
        result = cls_model.objects.filter(hash=hash)
        if result != None:
            for task in result:
                theme_name = task.name
    elif category == "tool" and settings.PLATFORM_TYPE != 'OJ':
        from x_tools.models import Tool
        result = Tool.objects.filter(hash=hash)
        if result != None:
            for task in result:
                theme_name = task.name
    else:
        if settings.PLATFORM_TYPE != "AD":
            from practice_real_vuln.models import RealVulnTask
            from practice_exercise.models import PracticeExerciseTask
            if len(RealVulnTask.objects.filter(hash=hash)) != 0:
                result = RealVulnTask.objects.filter(hash=hash)
                for task in result:
                    theme_name = task.title
            elif len(PracticeExerciseTask.objects.filter(hash=hash)) != 0:
                result = PracticeExerciseTask.objects.filter(hash=hash)
                for task in result:
                    theme_name = task.title

    data = {
        "tenant": api_settings.TENANT,
        "username": request.user.username,
        "nickname": params.get('respondent'),
        "avatar": logo,
        "resource": params.get("hash"),
        "comment": escape(params.get("content")),
        "parent": params.get("parent"),
        "public": True,
        "theme_name": theme_name,
    }
    comment = requests.post(post_url, data=data)
    return JsonResponse(comment.json())


def delete_comment(request):
    pass


def list_comment(request):
    params = request.GET
    get_url = "http://{}/x_comment/api/comments/".format(api_settings.CLOUD_CENTER)

    comments = requests.get(get_url, params=params)
    comment_tree = {}
    comment_dict = {}
    comment_request = {}
    for value in comments.json()["rows"]:
        if value['parent'] != None:
            parent_id = value['parent']
            comment_tree.setdefault(parent_id, []).append(value)
        else:
            parent_id = value['id']
            comment_dict[parent_id] = value
    for k, v in comment_dict.items():
        comment_request.setdefault(k, []).append(v)
    for k, v in comment_tree.items():
        comment_request.setdefault(k, []).append(v)
    return JsonResponse(comment_request)


def like_list(request):
    params = request.POST
    post_url = "http://{}/x_comment/api/comment_likes/".format(api_settings.CLOUD_CENTER)
    data = {
        "comment": params.get('comment_id'),
        "username": request.user.username,
        "username_id": request.user.id,
        "resource": params.get('resource'),
    }
    comments = requests.post(post_url, data=data)
    return JsonResponse(comments.json())


def like_status(request):
    params = request.GET
    get_url = "http://{}/x_comment/api/comment_likes/".format(api_settings.CLOUD_CENTER)
    data = {
        "resource": params.get("resource"),
        "username_id": request.user.id,
    }
    comments = requests.get(get_url, data=data)
    return JsonResponse(comments.json())


def update_list(request):
    context = {}
    uis = UpdateInfo.objects.filter(status=Status.NORMAL)
    ret_list = []
    for u in uis:
        u.change_log = u.change_log.split("\n")
        ret_list.append(u)

    context['uis'] = ret_list

    return render(request, 'common_cloud/web/update_list.html', context=context)


@api_view(['GET', ])
@permission_classes((AllowAny,))
def rest_update_list(request):
    context = {}
    uis = UpdateInfo.objects.filter(status=Status.NORMAL)
    ret_list = []
    for u in uis:
        u.change_log = u.change_log.split("\n")
        ret_list.append(u)

    class UpdateSerializer(serializers.ModelSerializer):
        class Meta:
            model = UpdateInfo
            fields = '__all__'

    ret = [UpdateSerializer(u).data for u in uis]
    return response.Response(ret)