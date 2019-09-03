# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.templatetags.static import static
from django.utils.translation import ugettext as _

__version__ = '1.1.1'


def get_using_env_tasks(user):
    from practice.widgets.env import get_using_env_tasks as base_get_using_env_tasks
    from practice.api import PRACTICE_TYPE_EXCRISE
    from .models import PracticeExerciseTask
    return base_get_using_env_tasks(
        user,
        PracticeExerciseTask,
        PRACTICE_TYPE_EXCRISE,
        _('x_exercise'),
        static('practice/img/exercise_default_cover.png'),
        'oj-icon oj-icon-E921',
    )



def get_env_target_task(env):
    from .models import PracticeExerciseTask

    task = PracticeExerciseTask.original_objects.filter(is_copy=False, envs__env=env).first()
    if not task:
        return None

    return {
        'app': _('x_practice'),
        'type': _('x_exercise'),
        'name': task.title,
    }


