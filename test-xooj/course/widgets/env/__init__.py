# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.templatetags.static import static
from django.utils.translation import ugettext_lazy as _

from rest_framework.reverse import reverse

from common_env.models import Env
from course.models import LessonEnv


def get_using_lesson_envs(user):
    using_status = Env.ActiveStatusList
    using_lesson_envs = LessonEnv.objects.filter(
        env__status__in=using_status,
        env__user=user,
    )
    return using_lesson_envs


def get_using_env_lessons(user):
    using_env_lessons = {}
    lesson_env_map = {}
    using_lesson_envs = get_using_lesson_envs(user)
    for lesson_env in using_lesson_envs:
        lessons = lesson_env.lesson_set.all()
        using_env_lessons.update({lesson.pk: lesson for lesson in lessons})
        lesson_env_map.update({lesson.pk: lesson_env for lesson in lessons})

    using_env_lesson_infos = []
    for lesson in using_env_lessons.values():
        lesson_env = lesson_env_map[lesson.pk]
        env_lesson_info = {
            'id': '%s:%s' % (lesson.hash, lesson_env.env.id),
            'logo': lesson.course.logo.url if lesson.course.logo else static('course/img/kec.png'),
            'icon': 'oj-icon oj-icon-E923',
            'title': '%s: %s' % (_('x_course'), lesson.course.name),
            'detail': lesson.name,
            # 'url': reverse('course:learn_lesson', (lesson.course.id, lesson.id)),
            'url': reverse('course:markdown_new') + '?course_id='+str(lesson.course.id)+"&lesson_id="+str(lesson.id),
            'delete_url': reverse('cms_course:widgets:lesson_env:lesson_env'),
            'delete_data': {
                'lesson_hash': lesson.pk,
            }
        }
        using_env_lesson_infos.append(env_lesson_info)
    return using_env_lesson_infos

