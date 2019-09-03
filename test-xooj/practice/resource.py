# -*- coding: utf-8 -*-

from django.db.models import Q


class TaskEventMeta(object):
    check = [{
        'get_conflict_obj': lambda resource: resource.model.objects.filter(name=resource.obj.name).first(),
        'conflict_consistency_check': lambda obj, conflict_obj: obj.type == conflict_obj.type
    }]
    subsidiary = [{
        'force': {
            'last_edit_user_id': None,
            'creater_id': None,
        },
    }]


class BaseTaskMeta(object):
    check = [{
        'get_conflict_obj': lambda resource: resource.model.objects.filter(
            hash=resource.obj.hash,
        ).first(),
        'conflict_consistency_check': lambda obj, conflict_obj: \
                obj.title == conflict_obj.title
            and obj.event == conflict_obj.event
    }, {
        'root': 'practice.models.TaskEvent',
        'get_conflict_obj': lambda resource: resource.model.objects.filter(
            title=resource.obj.title,
            event=resource.obj.event,
            is_copy=False
        ).first(),
    }]
    belong_to = [{
        'root': 'practice.models.TaskEvent',
        'parent': 'practice.models.TaskEvent',
        'get': lambda self_model, event: self_model.objects.filter(is_copy=False, event=event),
        'set': lambda self, event: setattr(self, 'event', event),
    }]


class SolvedBaseTask(BaseTaskMeta):
    pass


class TaskEnvMeta(object):
    @staticmethod
    def _get_conflict_obj(resource):
        from practice.base_models import SolvedBaseTask
        # 获得多对多关系的所有题目表
        task_models = []
        for rel in resource.model._meta.related_objects:
            if issubclass(rel.related_model, SolvedBaseTask):
                task_models.append(rel.related_model)

        owner_tasks = [resrc.obj for resrc in resource.owner_resources if isinstance(resrc.obj, tuple(task_models))]

        same_taskenvs = resource.model.objects.filter(env=resource.obj.env)
        for taskenv in same_taskenvs:
            # 如果已经被拥有者引用 返回本身
            for owner_task in owner_tasks:
                if owner_task.envs.filter(pk=taskenv.pk).exists():
                    return taskenv

            # 遍历所有题目表查询场景是否已被引用（未被引用则是可被利用的冲突对象）
            is_referenced = False
            for task_model in task_models:
                if task_model.objects.filter(envs=taskenv).exists():
                    is_referenced = True
                    break

            if not is_referenced:
                return taskenv

        return None

    check = [{
        'get_conflict_obj': _get_conflict_obj.__func__,
    }]
    subsidiary = [{
        'subsidiary': {
            'env': {
                'get': lambda self: self.env,
                'set': lambda self, env: setattr(self, 'env', env),
            },
        },
    }]


class TaskCategoryMeta(object):
    check = [{
        'get_conflict_obj': lambda resource: resource.model.objects.filter(
            Q(cn_name=resource.obj.cn_name) |
            Q(en_name=resource.obj.en_name)).first(),
    }]