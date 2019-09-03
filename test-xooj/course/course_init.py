# -*- coding: utf-8 -*-

from course.models import Record, Lesson, Course, Direction, LessonEnv


def course_init():
    Record.objects.all().delete()

    LessonEnv.objects.all().delete()

    lessons = Lesson.objects.exclude(creater__username__in=['admin', 'root'])
    for lesson in lessons:
        if lesson.pdf:
            lesson.pdf.delete()
        if lesson.video:
            lesson.video.delete()
        if lesson.attachment:
            lesson.attachment.delete()
        lesson.delete()

    courses = Course.objects.exclude(creater__username__in=['admin', 'root'])
    for course in courses:
        if course.logo:
            course.logo.delete()
        course.delete()

    # Direction.objects.all().delete()
