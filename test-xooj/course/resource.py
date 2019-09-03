# -*- coding: utf-8 -*-


from django.db.models import Q

from common_env.models import Env
from common_framework.utils.constant import Status
from practice.api import get_task_object


class CourseMeta(object):
    check = [{
        'get_conflict_obj': lambda resource: resource.model.objects.filter(
            hash=resource.obj.hash,
            status=Status.NORMAL).first(),
        'conflict_consistency_check': lambda obj, conflict_obj: \
                obj.name == conflict_obj.name
            and obj.direction == conflict_obj.direction
            and obj.sub_direction == conflict_obj.sub_direction
    }]
    subsidiary = [{
        'subsidiary': {
            'direction': {
                'get': lambda self: self.direction,
                'set': lambda self, direction: setattr(self, 'direction', direction),
            },
            'sub_direction': {
                'get': lambda self: self.sub_direction,
                'set': lambda self, sub_direction: setattr(self, 'sub_direction', sub_direction),
            },
        },
        'force': {
            'last_edit_user_id': None,
            'creater_id': None,
        },
    }]


class DirectionMeta(object):
    check = [{
        'get_conflict_obj': lambda resource: resource.model.objects.filter(
            Q(cn_name=resource.obj.cn_name) |
            Q(en_name=resource.obj.en_name), Q(status=Status.NORMAL), Q(parent=resource.obj.parent)).first(),
    }]
    subsidiary = [{
        'subsidiary': {
            'parent': {
                'get': lambda self: self.parent,
                'set': lambda self, parent: setattr(self, 'parent', parent),
            },
        },
    }]


class LessonMeta(object):
    check = [{
        'get_conflict_obj': lambda resource: resource.model.objects.filter(
            hash=resource.obj.hash,
            status=Status.NORMAL
        ).first(),
        'conflict_consistency_check': lambda obj, conflict_obj: \
                obj.name == conflict_obj.name
            and obj.course == conflict_obj.course
    }]
    belong_to = [{
        'root': 'course.models.Course',
        'parent': 'course.models.Course',
        'get': lambda self_model, course: self_model.objects.filter(course=course, status=Status.NORMAL),
        'set': lambda self, course: setattr(self, 'course', course),
    }]
    subsidiary = [{
        'force': {
            'creater_id': None,
            'last_edit_user_id': None,
        },
        'subsidiary': {
            'practice': {
                'get': lambda self: get_task_object(self.practice),
                'set': lambda self, task: setattr(self, 'practice', task.hash if task else None),
            },
            'homework': {
                'get': lambda self: get_task_object(self.homework),
                'set': lambda self, task: setattr(self, 'homework', task.hash if task else None),
            },
            'envs': {
                'many_to_many': True,
                'get': lambda self: self.envs.filter(env__status=Env.Status.TEMPLATE),
                'set': lambda self, lesson_envs: self.envs.add(*lesson_envs),
            },
        },
    }]


def coursejstree(self, course):
    setattr(self, 'lesson', None)
    setattr(self, 'course', course)


def lessonjstree(self, lesson):
    setattr(self, 'lesson', lesson)
    setattr(self, 'course', lesson.course)


class LessonJstreeMeta(object):
    check = [{
        'get_conflict_obj': lambda resource: resource.model.objects.filter(
            self_id=resource.obj.self_id,
            course=resource.obj.course
        ).first(),
    }]
    belong_to = [{
        'root': 'course.models.Course',
        'parent': 'course.models.Course',
        'get': lambda self_model, course: self_model.objects.filter(course=course, lesson=None),
        'set': coursejstree,
    }, {
        'root': 'course.models.Course',
        'parent': 'course.models.Lesson',
        'get': lambda self_model, lesson: self_model.objects.filter(lesson=lesson),
        'set': lessonjstree,
    }]


def getTaskEvent(task=None):
    if task is not None:
        task.event = None
        return task
    return None


class LessonPaperTaskMeta(object):
    """
    课后练习只是导出理论题型， 其它的暂时不考虑
    """
    check = [{
        'get_conflict_obj': lambda resource: resource.model.objects.filter(
            task_hash=resource.obj.task_hash,
            lesson=resource.obj.lesson
        ).first(),
    }]
    belong_to = [{
        'root': 'course.models.Course',
        'parent': 'course.models.Lesson',
        # 'get': lambda self_model, lesson: self_model.objects.filter(lesson=lesson, task_hash__endswith='.0'),
        'get': lambda self_model, lesson: self_model.objects.filter(lesson=lesson),
        'set': lambda self, lesson: setattr(self, 'lesson', lesson)
    }]
    subsidiary = [{
        'subsidiary': {
            'lessonpapertask': {
                # todo 保留理论基础题目
                'get': lambda self: getTaskEvent(get_task_object(self.task_hash)),
                'set': lambda self, task: setattr(self, 'task_hash', task.hash if task else None),
            },
        },
    }]


class LessonEnvMeta(object):
    @staticmethod
    def _get_conflict_obj(resource):
        from course.models import Lesson
        owner_lessons = [resrc.obj for resrc in resource.owner_resources if isinstance(resrc.obj, Lesson)]

        same_lessonenvs = resource.model.objects.filter(env=resource.obj.env)
        for lessonenv in same_lessonenvs:
            # 如果已经被拥有者引用 返回本身
            for owner_lesson in owner_lessons:
                if owner_lesson.envs.filter(pk=lessonenv.pk).exists():
                    return lessonenv

            # 查询场景是否已被引用（未被引用则是可被利用的冲突对象）
            if not Lesson.objects.filter(envs=lessonenv).exists():
                return lessonenv
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
