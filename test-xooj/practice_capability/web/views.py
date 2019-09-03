# -*- coding: utf-8 -*-
import logging

from django.shortcuts import render

from common_framework.utils import views as default_views
from common_framework.views import find_menu
from common_web.decorators import login_required as web_login_required
from practice_capability.models import TestPaper
from practice_theory.setting import api_settings

logger = logging.getLogger()
slug = api_settings.SLUG


@web_login_required
@find_menu(slug)
def exam(request, **kwargs):
    context = kwargs.get('menu')
    return render(request, 'practice_capability/web/exam.html', context)


@web_login_required
@find_menu(slug)
def exam_detail(request, **kwargs):
    testpaper_id = kwargs.get('testpaper_id')
    context = kwargs.get('menu')
    try:
        testpaper = TestPaper.objects.get(id=testpaper_id)
    except Exception, e:
        return default_views.Http404Page(request, e)

    context["testpaper"] = testpaper

    return render(request, 'practice_capability/web/exam_detail.html', context)
