from django.shortcuts import render

from rest_framework import generics

from common_framework.utils.constant import Status
from common_framework.views import find_menu

from common_web.decorators import login_required

from practice_experiment.setting import api_settings

from practice_experiment.models import Direction, Experiment
from practice_experiment.cms.serializers import ExperimentSerializer

slug = api_settings.SLUG


@login_required
@find_menu(slug)
def list(request, **kwargs):
    context = kwargs.get('menu')
    directions = Direction.objects.filter(status=Status.NORMAL)

    language = getattr(request, 'LANGUAGE_CODE', u'zh-hans')
    rows = []
    if language == 'zh-hans':
        for row in directions:
                rows.append({'id': row.id, "name": row.cn_name})
    else:
        for row in directions:
            rows.append({'id': row.id, "name": row.en_name})
    context.update({"directions": rows})
    return render(request, 'experiment/web/list.html', context)


@login_required
@find_menu(slug)
def learn(request, **kwargs):
    context = kwargs.get('menu')
    context.update({"experiment_id": kwargs.get("experiment_id")})
    return render(request, 'experiment/web/learn.html', context)


@login_required
@find_menu(slug)
def task(request, **kwargs):
    context = kwargs.get('menu')
    task_hash = request.GET.get("task_hash")
    try:
        _, type_id = task_hash.split(".")
        context.update({"task_hash": task_hash,
                        "type_id": type_id})
        if int(type_id) == 0:
            template = "course/web/do_task.html"
        else:
            template = "course/web/do_task2.html"
    except Exception, e:
        template = 'course/web/task.html'
    return render(request, template, context)


@login_required
@find_menu(slug)
def video(request, **kwargs):
    context = kwargs.get('menu')
    video_url = request.GET.get("video_url")
    if video_url:
        context.update({"video_url": video_url})
    return render(request, 'course/web/video.html', context)


@login_required
@find_menu(slug)
def note(request, **kwargs):
    context = kwargs.get('menu')
    experiment_id = request.GET.get("experiment_id")
    if experiment_id:
        context.update({"experiment_id": experiment_id})
    return render(request, 'experiment/web/note.html', context)
