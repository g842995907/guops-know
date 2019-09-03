# -*- coding: utf-8 -*-
import random
import os

from django.http import Http404
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse

from rest_framework import generics, exceptions, response
from rest_framework.decorators import permission_classes, api_view
from rest_framework.permissions import IsAuthenticated

from common_auth.utils import is_admin as judge_admin
from common_framework.utils.constant import Status
from common_framework.views import find_menu

from common_web.decorators import login_required

from course.setting import api_settings

from course.models import Direction, Course, Record, Lesson
from course.cms.serializers import CourseSerializer
from course.web.serializers import NewLessonSerializer
from course.utils.course_util import add_attend_class_time
from course.utils.user_action import ua
from course_occupation.models import OccupationCourse
from course.constant import VIDEOSTATE

from common_framework.models import AuthAndShare
from functools import wraps

slug = api_settings.SLUG


def get_auth_course(model=Lesson, model_id='lesson_id', method='GET'):
    def deco(func):
        @wraps(func)
        def check_auth(request, *args, **kwargs):
            user = request.user
            course_lesson_id = getattr(request, method).get(model_id) or kwargs.get('course_id', None)
            course_lesson = get_object_or_404(model, id=course_lesson_id, public=True)
            # course_lesson = model.objects.get(id=course_lesson_id)
            if isinstance(course_lesson, Lesson):
                course = course_lesson.course
            elif isinstance(course_lesson, Course):
                course = course_lesson
            else:
                raise Exception('Invalid course')
            if not user.is_superuser and not course.create_user == user:
                if not course.auth == AuthAndShare.AuthMode.ALL_AUTH_MODE:
                    if user.faculty not in course.auth_faculty.all() and user.major not in course.auth_major.all() and user.classes not in course.auth_classes.all():
                        return render(request, 'web/404.html', context={})
            return func(request, *args, **kwargs)
        return check_auth
    return deco


@login_required
@find_menu(slug)
def list(request, **kwargs):
    context = kwargs.get('menu')
    occupation_id = ''
    occupations = ""
    directions = Direction.objects.filter(parent__isnull=True).filter(status=Status.NORMAL).order_by('-update_time')
    sub_directions = Direction.objects.filter(parent__isnull=False).filter(status=Status.NORMAL)

    # occupations = OccupationSystem.objects.filter(public=True)
    # 判断用户是否本身职位,只显示公开，未删除的职业, 暂时不选中
    # occupation_is_choices = OccupationIsChoice.objects.filter(user=request.user, occupation__public=True)
    # if occupation_is_choices.exists():
    #     occupation_id = occupation_is_choices[0].occupation.id
    occupation_course_count = OccupationCourse.objects.filter(occupation_system__occupation_choice__user=request.user,
                                    occupation_system__occupation_choice__status=Status.NORMAL,
                                    status=Status.NORMAL).count()

    language = getattr(request, 'LANGUAGE_CODE', u'zh-hans')
    rows = []
    sub_rows = []
    if language == 'zh-hans':
        for row in directions:
            if Course.objects.filter(direction=row.id, status=1):
                rows.append({'id': row.id, "name": row.cn_name})
        for sub_row in sub_directions:
            if Course.objects.filter(direction=sub_row.id, status=1):
                sub_rows.append({'id': sub_row.id, "name": sub_row.cn_name, "parent_id": sub_row.parent.id})
    else:
        for row in directions:
            if Course.objects.filter(direction=row.id, status=1):
                rows.append({'id': row.id, "name": row.en_name})
        for sub_row in sub_directions:
            if Course.objects.filter(direction=sub_row.id, status=1):
                sub_rows.append({'id': sub_row.id, "name": sub_row.en_name, "parent_id": sub_row.parent.id})

    context.update({
        "directions": rows,
        "sub_directions": sub_rows,
        "occupations": occupations,
        'occupation_id': occupation_id,
        "occupation_course_count": occupation_course_count
    })
    return render(request, 'course/web/list.html', context)


@login_required
@find_menu(slug)
def theory_list(request, **kwargs):
    context = kwargs.get('menu')
    directions = Direction.objects.filter(status=Status.NORMAL)

    language = getattr(request, 'LANGUAGE_CODE', u'zh-hans')
    rows = []
    if language == 'zh-hans':
        for row in directions:
            rows.append({'id': row.id, "name": row.cn_name})
    else:
        for row in directions:
            rows.append({'id': row.id, "name": row.en_name})
    context.update({"directions": rows, "search_type": 0})
    return render(request, 'course/web/list.html', context)


@login_required
@find_menu(slug)
def experiment_list(request, **kwargs):
    context = kwargs.get('menu')
    directions = Direction.objects.filter(status=Status.NORMAL)

    language = getattr(request, 'LANGUAGE_CODE', u'zh-hans')
    rows = []
    if language == 'zh-hans':
        for row in directions:
            rows.append({'id': row.id, "name": row.cn_name})
    else:
        for row in directions:
            rows.append({'id': row.id, "name": row.en_name})
    context.update({"directions": rows, "search_type": 1})
    return render(request, 'course/web/list.html', context)


@login_required
@find_menu(slug)
def detail(request, **kwargs):
    template = 'course/web/detail.html'
    context = kwargs.get('menu')
    course_id = kwargs.get("course_id")
    context.update({"course_id": course_id})
    try:
        course = Course.objects.get(id=course_id)
    except Exception, e:
        raise Http404()
    return render(request, template, context)


@login_required
@find_menu(slug)
def learn(request, **kwargs):
    template = 'course/web/learn.html'
    context = kwargs.get('menu')
    course_id = kwargs.get("course_id")
    context.update({"course_id": course_id})
    try:
        course = Course.objects.get(id=course_id)
    except Exception, e:
        raise Http404()
    lesson_id = kwargs.get("lesson_id")
    if lesson_id:
        context.update({"lesson_id": lesson_id})
        lesson = Lesson.objects.get(id=lesson_id)

        Record.objects.filter(lesson=lesson,
                                     user=request.user,
                                     defaults={"progress": 2})
    return render(request, template, context)


@login_required
@find_menu(slug)
def task(request, **kwargs):
    context = kwargs.get('menu')
    task_hash = request.GET.get("task_hash")
    try:
        _, type_id = task_hash.split(".")
        context.update({"task_hash": task_hash,
                        "type_id": type_id})
        if int(type_id) == 0:
            template = "course/web/do_task.html"
        else:
            template = "course/web/do_task2.html"
    except Exception, e:
        template = 'course/web/task.html'
    return render(request, template, context)


@login_required
@find_menu(slug)
def pdf(request, **kwargs):
    context = kwargs.get('menu')
    pdf_url = request.GET.get("pdf_url")
    if pdf_url:
        context.update({"pdf_url": pdf_url})
    return render(request, 'course/web/pdf.html', context)


@login_required
@find_menu(slug)
def video(request, **kwargs):
    context = kwargs.get('menu')
    video_url = request.GET.get("video_url")
    if video_url:
        context.update({"video_url": video_url})
    return render(request, 'course/web/video.html', context)


@login_required
@find_menu(slug)
def attachment(request, **kwargs):
    context = kwargs.get('menu')
    attachment_url = request.GET.get("attachment_url")
    if attachment_url:
        context.update({"attachment_url": attachment_url})
    return render(request, 'course/web/attachment.html', context)


@login_required
@find_menu(slug)
def attachment(request, **kwargs):
    context = kwargs.get('menu')
    attachment_url = request.GET.get("attachment_url")
    if attachment_url:
        context.update({"attachment_url": attachment_url})
    return render(request, 'course/web/attachment.html', context)


@login_required
@find_menu(slug)
def env(request, **kwargs):
    context = kwargs.get('menu')
    lesson_id = request.GET.get("lesson_id")
    if lesson_id:
        lesson = Lesson.objects.get(pk=lesson_id)
        from common_env.models import Env
        lesson_env = lesson.envs.filter(
            env__status__in=Env.ActiveStatusList,
            env__user=request.user
        ).first()
        context.update({
            'lesson_id': lesson_id,
            'lesson': lesson,
            'lesson_env': lesson_env
        })
    return render(request, 'course/web/env.html', context)


@login_required
@find_menu(slug)
def note(request, **kwargs):
    context = kwargs.get('menu')
    course_id = request.GET.get("course_id")
    if course_id:
        context.update({"course_id": course_id})
    return render(request, 'course/web/note.html', context)


@login_required
@find_menu(slug)
def report(request, **kwargs):
    context = kwargs.get('menu')
    lesson_hash = request.GET.get("lesson_hash")
    if lesson_hash:
        context.update({"lesson_hash": lesson_hash})
    return render(request, 'course/web/report.html', context)


@login_required
@find_menu(slug)
def markdown(request, **kwargs):
    context = kwargs.get('menu')
    lesson_id = request.GET.get("lesson_id")
    if lesson_id:
        lesson = Lesson.objects.get(pk=lesson_id)
        context.update({"markdown": lesson.markdown})
    return render(request, 'course/web/markdown.html', context)


class CourseRecommandView(generics.ListAPIView):
    serializer_class = CourseSerializer

    def get_queryset(self):
        course_id = self.request.query_params.get("course_id")
        try:
            direction_id = Course.objects.get(id=course_id).sub_direction.id
        except Exception, e:
            direction_id = None
        queryset = Course.objects.filter(sub_direction_id=direction_id).exclude(
            id=course_id).filter(status=Status.NORMAL).filter(public=1)
        if len(queryset) > 2:
            return random.sample(queryset, 2)
        return queryset


@login_required
@find_menu(slug)
def learn_new(request, **kwargs):
    template = 'course/web/learn_new.html'
    context = kwargs.get('menu')
    course_id = kwargs.get("course_id")
    context.update({"course_id": course_id})
    try:
        course = Course.objects.get(id=course_id)
    except Exception, e:
        raise Http404()
    lesson_id = kwargs.get("lesson_id")
    if lesson_id:
        context.update({"lesson_id": lesson_id})
        lesson = Lesson.objects.get(id=lesson_id)

        Record.objects.get_or_create(lesson=lesson,
                                     user=request.user,
                                     defaults={"progress": 2})
    return render(request, template, context)


@login_required
@find_menu(slug)
def pdf(request, **kwargs):
    context = kwargs.get('menu')
    pdf_url = request.GET.get("pdf_url")
    if pdf_url:
        context.update({"pdf_url": pdf_url})
    return render(request, 'course/web/pdf.html', context)


@login_required
@find_menu(slug)
def video(request, **kwargs):
    context = kwargs.get('menu')
    video_url = request.GET.get("video_url")
    if video_url:
        context.update({"video_url": video_url})
    return render(request, 'course/web/video.html', context)


@login_required
@find_menu(slug)
def attachment(request, **kwargs):
    context = kwargs.get('menu')
    attachment_url = request.GET.get("attachment_url")
    if attachment_url:
        context.update({"attachment_url": attachment_url})
    return render(request, 'course/web/attachment.html', context)


@login_required
@find_menu(slug)
def attachment(request, **kwargs):
    context = kwargs.get('menu')
    attachment_url = request.GET.get("attachment_url")
    if attachment_url:
        context.update({"attachment_url": attachment_url})
    return render(request, 'course/web/attachment.html', context)


@login_required
@find_menu(slug)
def env(request, **kwargs):
    context = kwargs.get('menu')
    lesson_id = request.GET.get("lesson_id")
    if lesson_id:
        lesson = Lesson.objects.get(pk=lesson_id)
        from common_env.models import Env
        lesson_env = lesson.envs.filter(
            env__status__in=Env.ActiveStatusList,
            env__user=request.user
        ).first()
        context.update({
            'lesson_id': lesson_id,
            'lesson': lesson,
            'lesson_env': lesson_env
        })
    return render(request, 'course/web/env.html', context)


# ===================
@login_required
@find_menu(slug)
def note_new(request, **kwargs):
    context = kwargs.get('menu')

    course_id = request.GET.get('course_id')
    lesson_id = request.GET.get('lesson_id')
    context.update({"lesson_id": lesson_id})
    context.update({'course_id': course_id})

    if course_id:
        context.update({"course_id": course_id})
    return render(request, 'course/web/note_new.html', context)


@login_required
@find_menu(slug)
def report_new(request, **kwargs):
    context = kwargs.get('menu')
    lesson_hash = request.GET.get("lesson_hash")

    course_id = request.GET.get('course_id')
    lesson_id = request.GET.get('lesson_id')
    context.update({"lesson_id": lesson_id})
    context.update({'course_id': course_id})

    if lesson_hash:
        context.update({"lesson_hash": lesson_hash})
    return render(request, 'course/web/report_new.html', context)


@login_required
@find_menu(slug)
def pdf_new(request, **kwargs):
    context = kwargs.get('menu')
    pdf_url = request.GET.get("pdf_url")

    course_id = request.GET.get('course_id')
    lesson_id = request.GET.get('lesson_id')
    context.update({"lesson_id": lesson_id})
    context.update({'course_id': course_id})

    if pdf_url:
        context.update({"pdf_url": pdf_url})
    return render(request, 'course/web/pdf_new.html', context)


@login_required
@find_menu(slug)
def video_new(request, **kwargs):
    context = kwargs.get('menu')
    video_url = request.GET.get("video_url")

    course_id = request.GET.get('course_id')
    lesson_id = request.GET.get('lesson_id')
    context.update({"lesson_id": lesson_id})
    context.update({'course_id': course_id})

    if video_url:
        video_name = os.path.splitext(video_url)[1][1:]
        context.update({"video_url": video_url})
        context.update({"video_name": video_name})
    return render(request, 'course/web/video_new.html', context)


@login_required
@find_menu(slug)
def attachment_new(request, **kwargs):
    context = kwargs.get('menu')
    attachment_url = request.GET.get("attachment_url")

    course_id = request.GET.get('course_id')
    lesson_id = request.GET.get('lesson_id')
    context.update({"lesson_id": lesson_id})
    context.update({'course_id': course_id})

    if attachment_url:
        context.update({"attachment_url": attachment_url})
    return render(request, 'course/web/attachment_new.html', context)


@login_required
@find_menu(slug)
@get_auth_course()
def markdown_new(request, **kwargs):
    context = kwargs.get('menu')
    course_screen = request.GET.get('course_screen', None)
    lesson_id = request.GET.get('lesson_id')

    context.update({"lesson_id": lesson_id})
    if course_screen != 'one_screen':
        return redirect('%s?lesson_id=%s' % (reverse('course:html'), lesson_id))

    lesson = get_object_or_404(Lesson, pk=lesson_id, public=True)
    ua.learn_course(
        request.user,
        course=lesson.course.name,
        lesson=lesson.name,
    )
    context.update({'course_id': lesson.course_id})
    record, record_flag = Record.objects.get_or_create(lesson=lesson,
                                 user=request.user,
                                 defaults={"progress": 2})
    if not record_flag and not record.progress == Record.Progress.LEARED:
            record.progress = Record.Progress.LEARED
            record.save()
    serializer_data = NewLessonSerializer(lesson, fields=(
    'id', 'pdf', 'markdown', 'html', 'html_type', 'video', 'type', 'knowledges_list', 'video_state')).data

    context.update({'html': serializer_data.get('html'),
                    'html_type': serializer_data.get('html_type'),
                    'video': serializer_data.get('video'),
                    'lesson_type': serializer_data.get("type"),
                    "markdown": lesson.markdown,
                    'pdf_url': serializer_data.get('pdf'),
                    'knowledges_list': serializer_data.get('knowledges_list'),
                    'video_state': True if serializer_data.get('video_state', 0) == VIDEOSTATE.SUCCESS else False
                    })

    if lesson.html:
        lesson_content_type = 'new_html'
    elif lesson.markdown:
        lesson_content_type = 'old_markdown'
    elif lesson.pdf:
        lesson_content_type = 'old_pdf'
    else:
        lesson_content_type = 'nothing'

    context.update({'lesson_content_type': lesson_content_type})
    return render(request, 'course/web/html_new.html', context)


@login_required
@find_menu(slug)
def env_new(request, **kwargs):
    context = kwargs.get('menu')
    lesson_id = request.GET.get("lesson_id")
    if lesson_id:
        lesson = Lesson.objects.get(pk=lesson_id)
        from common_env.models import Env
        lesson_env = lesson.envs.filter(
            env__status__in=Env.ActiveStatusList,
            env__user=request.user
        ).first()
        context.update({
            'lesson_id': lesson_id,
            'lesson': lesson,
            'lesson_env': lesson_env
        })
    return render(request, 'course/web/env_new.html', context)


@login_required
@find_menu(slug)
def env_load(request, **kwargs):
    context = kwargs.get('menu')
    return render(request, 'course/web/env_load.html', context)


@login_required
@find_menu(slug)
def network(request, **kwargs):
    context = kwargs.get('menu')
    # 传入lesson_id
    course_id = kwargs.get("course_id")
    lesson_id = kwargs.get('lesson_id')
    url = request.GET.get('url')
    # course_id = 21
    # lesson_id = 66
    context.update({"course_id": course_id})
    context.update({"lesson_id": lesson_id})
    context.update({"guacamole_url": url})

    lesson_objs = Lesson.objects.filter(status=Status.NORMAL, pk=lesson_id)
    if lesson_objs:
        lesson_obj = lesson_objs[0]
        context['lesson_obj'] = lesson_obj
    return render(request, 'course/web/network.html', context)

@login_required
@find_menu(slug)
@get_auth_course(model=Course, model_id="course_id")
def detail_new(request, **kwargs):
    template = 'course/web/detail_new.html'
    context = kwargs.get('menu')
    course_id = kwargs.get("course_id")
    is_admin = judge_admin(request.user)
    context.update({"course_id": course_id, "is_admin": is_admin})
    try:
        course = Course.objects.get(id=course_id, public=True)
    except Exception, e:
        raise Http404()
    return render(request, template, context)


@login_required
@find_menu(slug)
def exam_paper_detail(request, **kwargs):
    lesson_id = kwargs.get('lesson_id')
    context = kwargs.get('menu')
    try:
        lesson_obj = Lesson.objects.get(id=lesson_id)
        if not lesson_obj.exercise_public:
            return Http404()
    except Exception as e:
        return Http404()

    context.update({"lesson_id": lesson_id})
    context.update({'course_id': lesson_obj.course.id})

    context["lesson_obj"] = lesson_obj

    return render(request, 'course/web/exam_paper.html', context)


@login_required
@find_menu(slug)
@get_auth_course()
def html(request, **kwargs):
    context = kwargs.get('menu')

    # course_id = request.GET.get('course_id')
    lesson_id = request.GET.get('lesson_id')
    context.update({"lesson_id": lesson_id})

    lesson = get_object_or_404(Lesson, pk=lesson_id, public=True)
    ua.learn_course(
        request.user,
        course=lesson.course.name,
        lesson=lesson.name,
    )
    context.update({'course_id': lesson.course_id})
    Record.objects.get_or_create(lesson=lesson,
                                 user=request.user,
                                 defaults={"progress": 2})

    serializer_data = NewLessonSerializer(lesson, fields=(
    'id', 'pdf', 'markdown', 'html', 'html_type', 'video', 'type', 'knowledges_list')).data

    context.update({'html': serializer_data.get('html'),
                    'html_type': serializer_data.get('html_type'),
                    'video': serializer_data.get('video'),
                    'lesson_type': serializer_data.get("type"),
                    "markdown": lesson.markdown,
                    'pdf_url': serializer_data.get('pdf'),
                    'knowledges_list': serializer_data.get('knowledges_list')
                    })

    if lesson.html:
        lesson_content_type = 'new_html'
    elif lesson.markdown:
        lesson_content_type = 'old_markdown'
    else:
        lesson_content_type = 'old_pdf'

    context.update({'lesson_content_type': lesson_content_type})
    return render(request, 'course/web/html.html', context)


def from_html_video(request, **kwargs):
    lesson_id = kwargs.pop('lesson_id')
    lesson = get_object_or_404(Lesson, pk=lesson_id)
    context = {
        'lesson': lesson,
    }
    return render(request, 'course/web/from_html_to_video.html', context)



@api_view(['GET'])
@permission_classes((IsAuthenticated,))
def attend_class_time(request, lesson_id, **kwargs):
    try:
        seconds = int(request.query_params.get('seconds'))
        if seconds <= 0 or seconds > 60 * 3:
            raise Exception()
        lesson = Lesson.objects.filter(pk=lesson_id)
    except Exception as e:
        raise exceptions.ParseError()

    add_attend_class_time(request.user, lesson, seconds)

    return response.Response()
