from django.shortcuts import render

from common_framework.utils.app_url import get_home_module_urls
from common_framework.views import find_menu

from common_web.decorators import login_required

from event.setting import api_settings

slug = api_settings.SLUG


@login_required
@find_menu(slug)
def list(request, **kwargs):
    context = kwargs.get('menu')
    context = get_home_module_urls(context)
    return render(request, 'event/web/list_new.html', context)


@login_required
@find_menu(slug)
def detail(request, **kwargs):
    context = kwargs.get('menu')
    return render(request, 'event/web/detail.html', context)
