from django.shortcuts import render

from common_framework.views import find_menu

from common_web.decorators import login_required

from common_message.setting import api_settings


slug = api_settings.SLUG


@login_required
@find_menu(slug)
def list(request, **kwargs):
    context = kwargs.get('menu')
    return render(request, 'message/web/list.html', context)
