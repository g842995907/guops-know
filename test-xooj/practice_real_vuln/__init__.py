# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.templatetags.static import static
from django.utils.translation import ugettext_lazy as _

__version__ = '1.1.1'


def get_using_env_tasks(user):
    from practice.widgets.env import get_using_env_tasks as base_get_using_env_tasks
    from practice.api import PRACTICE_TYPE_REAL_VULN
    from .models import RealVulnTask
    return base_get_using_env_tasks(
        user,
        RealVulnTask,
        PRACTICE_TYPE_REAL_VULN,
        _('x_real_vuln'),
        static('practice/img/real_vuln_default_cover.png'),
        'oj-icon oj-icon-E901',
    )


def get_env_target_task(env):
    from .models import RealVulnTask

    task = RealVulnTask.original_objects.filter(is_copy=False, envs__env=env).first()
    if not task:
        return None

    return {
        'app': _('x_practice'),
        'type': _('x_real_vuln'),
        'name': task.title,
    }
