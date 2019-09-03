# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.templatetags.static import static
from django.utils.translation import ugettext as _

__version__ = '1.1.1'


def get_env_target_task(env):
    from .models import PracticeAttackDefenseTask

    task = PracticeAttackDefenseTask.objects.filter(is_copy=False, envs__env=env).first()
    if not task:
        return None

    return {
        'app': _('x_practice'),
        'type': _('x_ad_mode'),
        'name': task.title,
    }