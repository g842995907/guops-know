# -*- coding: utf-8 -*-
__version__ = '1.1.1'

def get_ignored_using_env_count(user):
    from django.db.models import Q
    from common_env.models import Env
    from .base_models import TaskEnv

    using_status = Env.ActiveStatusList
    my_ignored_envs = TaskEnv.objects.filter(
        env__user=user,
        env__status__in=using_status
    ).filter(
        Q(type=TaskEnv.Type.SHARED) | (Q(type=TaskEnv.Type.PRIVATE) & ~Q(env__team=None))
    )

    return my_ignored_envs.count()