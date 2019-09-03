# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.templatetags.static import static
from django.utils.translation import ugettext as _

__version__ = '1.1.1'
def get_using_env_tasks(user):
    from practice.widgets.env import get_using_env_tasks as base_get_using_env_tasks
    from practice.api import PRACTICE_TYPE_MAN_MACHINE
    from .models import ManMachineTask
    return base_get_using_env_tasks(
        user,
        ManMachineTask,
        PRACTICE_TYPE_MAN_MACHINE,
        _('人机攻防'),
        static('practice/img/man_machine_default_cover.png'),
        'oj-icon oj-icon-E903',
    )


def get_env_target_task(env):
    from .models import ManMachineTask

    task = ManMachineTask.original_objects.filter(is_copy=False, envs__env=env).first()
    if not task:
        return None

    return {
        'app': _('x_practice'),
        'type': _('x_man_machine'),
        'name': task.title,
    }
