# -*- coding: utf-8 -*-

from course import models as course_models
from course.cms import serializers as mserializers


class CourseHandler(object):
    def __init__(self):
        super(CourseHandler, self).__init__()

    @staticmethod
    def get_lesson_by_hash(hash):
        try:
            lesson = course_models.Lesson.objects.get(hash=hash)
        except:
            return {}

        return mserializers.LessonSerializer(lesson).data