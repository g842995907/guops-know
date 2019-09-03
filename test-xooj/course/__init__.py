# -*- coding: utf-8 -*-
from django.utils.translation import ugettext as _

__version__ = '1.1.1'


def get_using_env_lessons(user):
    from .widgets.env import get_using_env_lessons as base_get_using_env_lessons
    return base_get_using_env_lessons(user)


def get_ignored_using_env_count(user):
    from django.db.models import Q
    from common_env.models import Env
    from .models import LessonEnv

    using_status = Env.ActiveStatusList
    my_ignored_envs = LessonEnv.objects.filter(
        env__user=user,
        env__status__in=using_status,
    ).filter(
        Q(type=LessonEnv.Type.GROUP) | Q(type=LessonEnv.Type.SHARED) | (Q(type=LessonEnv.Type.PRIVATE) & ~Q(env__team=None))
    )

    return my_ignored_envs.count()


def get_env_target_lesson(env):
    from .models import Lesson

    lesson = Lesson.objects.filter(envs__env=env).first()
    if not lesson:
        return None

    return {
        'app': _('课程'),
        'type': lesson.course.name,
        'name': lesson.name,
    }
