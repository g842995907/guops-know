# -*- coding: utf-8 -*-
from rest_framework.reverse import reverse

from common_env.models import Env
from practice.base_models import TaskEnv


def get_using_task_envs(user):
    using_status = Env.ActiveStatusList
    using_task_envs = TaskEnv.objects.filter(
        env__status__in=using_status,
        env__user=user,
    )
    return using_task_envs


def get_using_env_tasks(user, task_model, task_type, task_type_desc, task_default_logo, task_default_icon=None):
    using_env_tasks = {}
    task_env_map = {}
    using_task_envs = get_using_task_envs(user)
    for task_env in using_task_envs:
        task_set_name = '%s_set' % task_model.__name__.lower()
        tasks = getattr(task_env, task_set_name).filter(is_copy=False)
        using_env_tasks.update({task.pk: task for task in tasks})
        task_env_map.update({task.pk: task_env for task in tasks})

    using_env_task_infos = []
    for task in using_env_tasks.values():
        task_env = task_env_map[task.pk]
        if task.envs.first().type == TaskEnv.Type.SHARED:
            continue
        env_task_info = {
            'id': '%s:%s' % (task.hash, task_env.env.id),
            'logo': task_default_logo,
            'icon': task_default_icon,
            'title': task_type_desc,
            'detail': task.title,
            'url': reverse('practice:defensetraintask', (task_type, task.hash)),
            'delete_url': reverse('cms_practice:widgets:task_env:task_env'),
            'delete_data': {
                'task_hash': task.hash,
            }
        }

        using_env_task_infos.append(env_task_info)
    return using_env_task_infos

