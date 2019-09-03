# -*- coding: utf-8 -*-

import logging

from django.core.management import BaseCommand
from common_framework.utils.constant import Status
from course.models import Lesson, Course, LessonJstree

from course.utils.course_util import lesson_jstree_CURD, Method_Type

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    def handle(self, *args, **options):
        """
        对所有已经存在的课程添（公开和隐藏）加课时（公开）排序结构
        """
        course_queryset = Course.objects.filter(status=Status.NORMAL)

        for course in course_queryset:
            if not LessonJstree.objects.filter(course=course).exists():
                # 创建课程根节点
                lesson_jstree_CURD(Method_Type.COURSE_CREATE, LessonJstree, course)

                # 获取当前课程下所有可用的课时
                lesson_queryset = Lesson.objects.filter(status=Status.NORMAL, course=course).order_by('order')
                lesson_count = lesson_queryset.count()
                logger.info(
                    "run current course--> {0} and this course has public lesson count is = {1}".format(course.name,
                                                                                                        lesson_count))

                if lesson_count > 0:
                    # 批量创建课程节点
                    lesson_jstree_CURD(Method_Type.PUBLIC, LessonJstree, None, queryset=lesson_queryset,
                                       public=True)

        logger.info('course_lesson_sort is run over')
