# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext as _

__version__ = '1.1.1'


def get_env_target_task(env):
    from practice_exercise.models import PracticeExerciseTask
    from practice_real_vuln.models import RealVulnTask
    from practice_man_machine.models import ManMachineTask
    from practice_attack_defense.models import PracticeAttackDefenseTask
    from practice_infiltration.models import PracticeInfiltrationTask

    from event.models import Event, EventTask

    task = PracticeExerciseTask.original_objects.filter(is_copy=True, envs__env=env).first()
    if not task:
        task = RealVulnTask.original_objects.filter(is_copy=True, envs__env=env).first()
    if not task:
        task = ManMachineTask.original_objects.filter(is_copy=True, envs__env=env).first()
    if not task:
        task = PracticeAttackDefenseTask.original_objects.filter(is_copy=True, envs__env=env).first()
    if not task:
        task = PracticeInfiltrationTask.original_objects.filter(is_copy=True, envs__env=env).first()

    if not task:
        return None

    event_task = EventTask.original_objects.filter(task_hash=task.hash).first()
    if not event_task:
        return None

    event = event_task.event

    event_type_app = {
        Event.Type.EXAM: _('x_exam'),
        Event.Type.JEOPARDY: _('x_jeopardy'),
        Event.Type.SHARE: _('分享赛'),
        Event.Type.TRIAL: _('x_trial_game'),
        Event.Type.ATTACK_DEFENSE: _('x_ad_game'),
        Event.Type.INFILTRATION: _('x_event_infiltration'),
    }

    return {
        'app': event_type_app[event.type],
        'type': event.name,
        'name': task.title,
    }
