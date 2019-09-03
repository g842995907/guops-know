# -*- coding: utf-8 -*-
import collections

from django.http import HttpResponse, JsonResponse
from django.http import QueryDict
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext

from common_framework.utils.constant import Status
from common_auth import api as auth_api
from common_cms import views as cms_views

from practice.api import get_category_by_type
from practice_experiment.models import Direction, Experiment


def get_difficulty():
    difficulty = collections.OrderedDict()
    difficulty[gettext('x_easy')] = 0
    difficulty[gettext('x_normal')] = 1
    difficulty[gettext('x_hard')] = 2

    return difficulty


def direction(request):
    return render(request, 'experiment/cms/directions.html')


def experiments(request):
    context = {
        'difficulty': get_difficulty(),
        'directions': Direction.objects.filter(status=Status.NORMAL)
    }
    return render(request, 'experiment/cms/experiments.html', context)


def direction_detail(request, direction_id):
    context = {
        'mode': 1
    }

    direction_id = int(direction_id)
    if direction_id == 0:
        context['mode'] = 0
    else:
        context['direction'] = Direction.objects.get(id=direction_id)

    return render(request, 'experiment/cms/direction_detail.html', context)


def experiment_detail(request, experiments_id):
    context = {
        'mode': 1,
        'directions': Direction.objects.filter(status=Status.NORMAL)
    }

    experiments_id = int(experiments_id)
    if experiments_id == 0:
        context['mode'] = 0
    else:
        context['experiment'] = Experiment.objects.get(id=experiments_id)

    context['difficulty'] = get_difficulty()

    return render(request, 'experiment/cms/experiment_detail.html', context)


def custom_experiment_detail(request, experiment_id):
    if request.method == 'PUT':
        params = QueryDict(request.body)
        experiment = Experiment.objects.get(id=experiment_id)
        if "pdf" in params:
            if experiment.pdf:
                experiment.pdf.delete()
            experiment.save()
        if "video" in params:
            if experiment.video:
                experiment.video.delete()
            experiment.save()
    return HttpResponse(None, status=200)


def auth_class(request, course_id):

    context = {
        'course_id':course_id,
        'facultys' : auth_api.get_faculty(),
        'majors' : auth_api.get_major(),
        'url_list_url': reverse("cms_course:course"),
        'query_auth_url': reverse("cms_course:api:course-get-auths", kwargs={'pk':course_id}),
        'query_all_auth_url': reverse("cms_course:api:course-get-all-auth", kwargs={'pk':course_id}),
        'modify_auth_url': reverse("cms_course:api:course-set-auths", kwargs={'pk':course_id}),
    }

    return cms_views.auth_class(request, context)


def practice_categories(request, type_id):
    try:
        type_id = int(type_id)
        categorys = get_category_by_type(type_id)
    except Exception, e:
        categorys = []
    return JsonResponse({"data": categorys})
