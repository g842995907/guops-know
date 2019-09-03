# -*- coding: utf-8 -*-
import collections
import logging
import os
import json
import shutil

from django.db.models import Q, Count, Avg
from django.contrib.auth.models import Group
from django.http import HttpResponse, JsonResponse
from django.http import QueryDict
from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils.html import escape
from django.utils.translation import gettext
from django.utils.translation import ugettext as _
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework import exceptions

from common_cms import views as cms_views
from common_framework.utils.constant import Status
from common_framework.utils.request import is_en
from common_framework.utils.rest import mixins as common_mixins
from common_framework.utils import views as default_views
from common_framework.utils.rest.permission import IsStaffPermission

from course import models as course_model
from course.models import Course, Lesson, CourseSchedule
from course.constant import VIDEOSTATE, CourseResError
from oj.config import ORGANIZATION_EN, ORGANIZATION_CN
from practice.api import get_category_by_type
from common_auth.constant import GroupType
from common_auth.models import Faculty, Major, Classes, User

from x_note.models import Note
from x_person.utils.product_type import get_product_type


from . import serializers as mserializers
from oj.settings import DEBUG, MEDIA_ROOT

logger = logging.getLogger(__name__)

def get_difficulty():
    difficulty = collections.OrderedDict()
    difficulty[gettext('x_easy')] = 0
    difficulty[gettext('x_normal')] = 1
    difficulty[gettext('x_hard')] = 2

    return difficulty


def custom_delete_file(media_root, instance_id, **kwargs):
    video_change_path = 'course/video_trans/video_change'

    if len(kwargs.values()) > 2:
        logger.info('the dict len is big then 2')
        return 'error'
    for k,v in kwargs.items():
        if not v:
            continue
        if v.startswith('/'):
            file_path = os.path.join(media_root, v[1:])
        else:
            file_path = os.path.join(media_root, v)
        if os.path.isfile(file_path):
            try:
                os.remove(file_path)
            except:
                logger.info('file remove is fail')
    mulu_files = os.path.join(media_root, video_change_path, str(instance_id))
    # 删除目录
    try:
        shutil.rmtree(mulu_files)
    except:
        logger.info('file dir is remove fail maybe is not exist')
    return 'success'


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def direction(request):
    context = {}
    data = []
    row = {
        'id': "rootnode",
        'parent': '#',
        'text': gettext("x_directional_type"),
        'type': 'root'
    }
    data.append(row)

    all_directions = course_model.Direction.objects.filter(status=Status.NORMAL)
    direction_type_list = all_directions.filter(parent__isnull=True).order_by('-update_time')
    direction_sub_type_list = all_directions.filter(parent__isnull=False)

    for direction_type in direction_type_list:
        row = {
            'id': str(direction_type.id),
            'parent': 'rootnode',
            'text': escape(direction_type.en_name) if is_en(request) else escape(direction_type.cn_name),
            'cn_name': escape(direction_type.cn_name),
            'type': 'device_type',
            'en_name': escape(direction_type.en_name)
        }
        data.append(row)

    for direction_sub_type in direction_sub_type_list:
        row = {
            'id': '{}:{}'.format(direction_sub_type.parent_id, direction_sub_type.id),
            'parent': str(direction_sub_type.parent_id),
            'text': escape(direction_sub_type.en_name) if is_en(request) else escape(direction_sub_type.cn_name),
            'type': 'device_sub_type',
            'cn_name': escape(direction_sub_type.cn_name),
            'en_name': escape(direction_sub_type.en_name)
        }
        data.append(row)
    context['jstree'] = json.dumps(data)
    return render(request, 'course/cms/standard_direction_type.html', context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def course(request):
    all_directions = course_model.Direction.objects.filter(status=Status.NORMAL)
    context = {
        'difficulty': get_difficulty(),
        'directions': all_directions.filter(parent__isnull=True),
        'sub_directions': all_directions.filter(parent__isnull=False),
        'debug': settings.DEBUG
    }
    return render(request, 'course/cms/courses.html', context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def experiment(request):
    context = {
        'difficulty': get_difficulty(),
        'directions': course_model.Direction.objects.filter(status=Status.NORMAL)
    }
    return render(request, 'experiment/cms/experiments.html', context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def direction_detail(request, direction_id):
    context = {
        'mode': 1
    }

    direction_id = int(direction_id)
    directions = course_model.Direction.objects.filter(parent__isnull=True).filter(status=Status.NORMAL)
    if direction_id == 0:
        context['mode'] = 0
    else:
        directions = directions.exclude(id=direction_id)
        context['direction'] = course_model.Direction.objects.get(id=direction_id)

    context["directions"] = directions
    return render(request, 'course/cms/direction_detail.html', context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def course_detail(request, course_id):
    context = {
        'mode': 1,
        'directions': course_model.Direction.objects.filter(parent__isnull=True).filter(status=Status.NORMAL)
    }

    course_id = int(course_id)
    if course_id == 0:
        context['mode'] = 0
    else:
        context['course'] = course_model.Course.objects.get(id=course_id)
        if context['course'].builtin == 1:
            return default_views.Http404Page(request, Exception())

    context['difficulty'] = get_difficulty()

    return render(request, 'course/cms/course_detail.html', context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def lesson_sort(request, course_id):
    course_id = int(course_id)
    context = {}
    course_obj = course_model.Course.objects.get(id=course_id)

    lessons = Lesson.objects.filter(course_id=course_id).filter(
        status=Status.NORMAL).order_by('order', 'id')

    context['course'] = course_obj
    context['lessons'] = lessons
    return render(request, 'course/cms/lesson_sort.html', context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def lesson_sort_new(request, course_id):
    course_id = int(course_id)
    context = {}
    course_obj = course_model.Course.objects.get(id=course_id)

    lessons = Lesson.objects.filter(course_id=course_id).filter(
        status=Status.NORMAL).order_by('order', 'id')

    context['course'] = course_obj
    context['lessons'] = lessons
    return render(request, 'course/cms/lesson_sort_new.html', context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def experiment_detail(request, experiment_id):
    context = {
        'mode': 1,
        'directions': course_model.Direction.objects.filter(status=Status.NORMAL)
    }

    experiment_id = int(experiment_id)
    if experiment_id == 0:
        context['mode'] = 0
    else:
        context['course'] = course_model.Course.objects.get(id=experiment_id)

    context['difficulty'] = get_difficulty()

    return render(request, 'experiment/cms/experiment_detail.html', context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def lesson(request, course_id):
    course_obj = Course.objects.get(id=course_id)
    context = {
        'course_id': course_id,
        'course': course_obj,
        'DEBUG': DEBUG and True or False
    }

    return render(request, 'course/cms/lessons.html', context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def exp_lesson(request, experiment_id):
    experiment_obj = Course.objects.get(id=experiment_id)
    context = {
        'experiment_id': experiment_id,
        'experiment': experiment_obj
    }

    return render(request, 'course/cms/lessons.html', context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def lesson_detail(request, course_id, lesson_id):
    context = {
        'mode': 1,
        'course_id': course_id,
        'debug': 1 if DEBUG else 0
    }

    course_id = int(lesson_id)
    if course_id == 0:
        context['mode'] = 0
    else:
        # lesson = course_model.Lesson.objects.get(id=lesson_id)
        lesson = get_object_or_404(Lesson, id=lesson_id, builtin=False)

        context['lesson'] = lesson
        context['lesson_data'] = mserializers.LessonSerializer(lesson).data

    return render(request, 'course/cms/lesson_detail.html', context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def exp_lesson_detail(request, experiment_id, lesson_id):
    context = {
        'mode': 1,
        'experiment_id': experiment_id
    }

    course_id = int(lesson_id)
    if course_id == 0:
        context['mode'] = 0
    else:
        context['lesson'] = course_model.Lesson.objects.get(id=lesson_id)

    return render(request, 'course/cms/lesson_detail.html', context)


@api_view(['GET', 'PUT'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def custom_lesson_detail(request, lesson_id):
    if request.method == 'PUT':
        params = QueryDict(request.body)
        lesson = Lesson.objects.get(id=lesson_id)
        if "pdf" in params:
            if lesson.pdf:
                lesson.pdf.delete()
            lesson.save()
        if "video" in params:
            # 删除 video 的时候将视屏转换的也进行删除
            # 删除文件夹 转码中不允许删除视屏文件
            if lesson.video_state == VIDEOSTATE.CHANGEING:
                logger.info('video({}) is changing you can\'t delete this video'.format(lesson.video))
                raise exceptions.NotAcceptable(CourseResError.VIDEO_IS_CHANGE)
            logger.info('this {} delete video begin'.format(lesson.video))
            delete_statue = custom_delete_file(MEDIA_ROOT, lesson.id, video_preview=lesson.video_preview.name,
                                               video_poster=lesson.video_poster.name)
            if delete_statue == 'success':
                lesson.video.delete()
                lesson.video_change = ''
                lesson.video_preview = ''
                lesson.video_poster = ''
                lesson.video_scale = ''
                lesson.video_state = VIDEOSTATE.NOVIDEO
                lesson.save()
        if "attachment" in params:
            if lesson.attachment:
                lesson.attachment.delete()
            lesson.save()
        if 'markdown' in params:
            if lesson.markdown:
                lesson.markdown = None
                lesson.markdownfile.delete()
            lesson.save()
        if 'html' in params:
            if lesson.html:
                lesson.html_type = Lesson.HTML_TYPE.NEITHER
                lesson.html.delete()
            lesson.save()
        from django.core.cache import cache
        cache.clear()
    return HttpResponse(None, status=200)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def auth_class(request, course_id):
    context = {
        'url_list_url': reverse("cms_course:course"),
        'query_auth_url': reverse("cms_course:api:course-get-auths", kwargs={'pk': course_id}),
        'query_all_auth_url': reverse("cms_course:api:course-get-all-auth", kwargs={'pk': course_id}),
        'modify_auth_url': reverse("cms_course:api:course-set-auths", kwargs={'pk': course_id}),
    }

    return cms_views.auth_class(request, context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def share_teacher(request, event_id):
    from common_cms import views as cms_views
    context = {
        'url_list_url': reverse("cms_course:course"),
        'query_share_url': reverse("cms_course:api:course-get-shares", kwargs={'pk': event_id}),
        'modify_share_url': reverse("cms_course:api:course-set-shares", kwargs={'pk': event_id}),
    }

    return cms_views.share_teacher(request, context)

@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def practice_categories(request, type_id):
    try:
        type_id = int(type_id)
        categorys = get_category_by_type(type_id)
    except Exception, e:
        categorys = []
    return JsonResponse({"data": categorys})


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def report_list(request, experiment_id, lesson_id):
    lesson = Lesson.objects.get(id=lesson_id)
    context = {"lesson": lesson, "course_id": experiment_id}
    return render(request, 'course/cms/report_list.html', context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def report_detail(request, report_id):
    note = Note.objects.get(id=report_id)
    context = {"note": note}
    return render(request, 'course/cms/report_detail.html', context)


@api_view(['GET', 'POST'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def order_lessons(request):
    from course.cms.viewset import LessonViewSet
    orders = request.POST.get("lesson_order")
    if orders:
        order_list = orders.split(",")
        for index, lesson_id in enumerate(order_list):
            lesson = Lesson.objects.get(id=lesson_id)
            lesson.order = index
            lesson.save()
        common_mixins.CacheModelMixin.clear_cls_cache(LessonViewSet)
    return JsonResponse({"msg": "OK"})


@api_view(['GET',])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def video_show(request, lesson_id):
    context = {"lesson_id": lesson_id}
    return render(request, 'course/cms/video_show.html', context)


@api_view(['GET', ])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def lesson_monitor(request, lesson_id):
    lesson_obj = get_object_or_404(Lesson, pk=int(lesson_id))
    type = int(request.GET.get('type', 0))
    context = {"lesson_obj": lesson_obj}
    context.update({"type": type})
    if lesson_obj:
        classroom = course_model.CourseSchedule.objects.filter(
            lesson=lesson_obj,
            create_user=request.user,
            status=course_model.CourseSchedule.Status.NORMAL,
        ).order_by('-start').first()
        context.update({"classroom": classroom})
    return render(request, 'course/cms/lesson_monitor.html', context)
    pass


@api_view(['GET', ])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def schedule_list(request):
    if is_en(request):
        ORGANIZATION = ORGANIZATION_EN
    else:
        ORGANIZATION = ORGANIZATION_CN

    default_schedule = CourseSchedule.objects.filter(status=Status.NORMAL).first()
    context = {
        'teacher_list': User.objects.exclude(status=User.USER.DELETE).filter(
                                            Q(groups__id=GroupType.TEACHER) | Q(is_superuser=1)),
        'default_schedule': default_schedule,
        'ORGANIZATION': ORGANIZATION,
    }
    return render(request, 'course/cms/schedule.html', context)


@api_view(['GET', ])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def class_statistics_list(request):
    if is_en(request):
        ORGANIZATION = ORGANIZATION_EN
    else:
        ORGANIZATION = ORGANIZATION_CN

    faculty_list = Faculty.objects.all()
    major_list = Major.objects.all()
    classes_list = Classes.objects.all()
    direction_ids = list(course_model.Course.objects.values_list('direction', flat=True).distinct())
    sub_direction_ids = list(course_model.Course.objects.values_list('sub_direction', flat=True).distinct())
    all_ids = direction_ids + sub_direction_ids
    all_directions = course_model.Direction.objects.filter(status=Status.NORMAL, id__in=all_ids)

    context = dict(
        faculty_list=faculty_list,
        major_list=major_list,
        classes_list=classes_list,
        ORGANIZATION = ORGANIZATION,
    )

    context.update({
        'difficulty': get_difficulty(),
        'directions': all_directions.filter(parent__isnull=True),
        'sub_directions': all_directions.filter(parent__isnull=False)
    })

    return render(request, 'course/cms/class_statistics_list.html', context)


@api_view(['GET', ])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def class_statistics_detail(request, class_id):
    class_id = int(class_id)
    users = User.objects.filter(classes_id=class_id).exclude(status=User.USER.DELETE)
    class_obj = Classes.objects.filter(id=class_id)

    if class_obj.exists():
        if is_en(request):
            ORGANIZATION = ORGANIZATION_EN
        else:
            ORGANIZATION = ORGANIZATION_CN

        context = dict(
            class_id=class_id,
            student_nums=users.count(),
            class_name=class_obj.first().name,
            ORGANIZATION=ORGANIZATION
        )

        return render(request, 'course/cms/class_statistics_detail.html', context)


@api_view(['GET', ])
@permission_classes((IsAuthenticated, IsStaffPermission, ))
def user_statistics(request, user_id):
    if is_en(request):
        ORGANIZATION = ORGANIZATION_EN
    else:
        ORGANIZATION = ORGANIZATION_CN

    user_obj = User.objects.filter(id=user_id).first()
    direction_obj = course_model.Direction.objects.exclude(parent_id=None)
    context = {
        "user": user_obj,
        "direction": direction_obj,
        "ORGANIZATION": ORGANIZATION,
    }
    return render(request, 'course/cms/user_statistics.html', context)


@api_view(['GET', ])
@permission_classes((IsAuthenticated, IsStaffPermission, ))
def get_user_statistics(request):
    user_id = request.GET.get('user')
    user_obj = User.objects.filter(id=user_id).first()
    user_group_dict = {group.name: group.user_set.all().exclude(status=Status.DELETE) for group in Group.objects.all()}
    user_dict = {}
    for group, users in user_group_dict.items():
        user_dict.update({user.id: group for user in users})
    if user_obj.id in user_dict:
        role = user_dict.get(user_obj.id)
    else:
        role = _('x_student')
    organization = user_obj.faculty.name + ' / ' + user_obj.major.name + ' / ' + user_obj.classes.name
    # 已学习课程方向统计
    direction_queryset = course_model.Direction.objects.filter(status=Status.NORMAL).filter(parent_id=None)
    direction_cn_name_list = [direction.cn_name for direction in direction_queryset]
    course_direction_list = []
    course_direction_name_list = []
    lesson_records = course_model.Record.objects.filter(progress=course_model.Record.Progress.LEARED
                                                           ).exclude(user__status=Status.DELETE).filter(
                                                                user_id=user_id
                                                            )
    lesson_records = lesson_records.values('lesson_id', 'user_id', 'lesson__course__direction__cn_name')
    learn_course_dicts = _get_dict_by_key(lesson_records, 'lesson__course__direction__cn_name', direction_cn_name_list)
    for direction_name, learn_course_count in learn_course_dicts.items():
        course_direction_list.append(direction_name)
        course_direction_name_list.append(learn_course_count)

    context = {
        'course_direction_list': course_direction_list,
        'course_direction_name_list': course_direction_name_list
    }

    # 已学习课时数量统计
    notes = Note.objects.filter(resource__icontains='.lesson_report').filter(user_id=user_id)
    note_dict = notes.values('user_id').annotate(average_score=Avg('score'))
    lesson_record_solveds = course_model.LessonPaperRecord.objects.filter(solved=True)
    complete_lessons = len(lesson_records)
    complete_notes = len(notes)
    complete_exercises = len(lesson_record_solveds)
    average_score = note_dict[0]['average_score'] if notes.exists() else 0
    context.update(
        {
            'lesson_count_statistics': {
                'name': user_obj.first_name,
                'organization': organization,
                'role': role,
                'complete_lessons': complete_lessons,
                'complete_notes': complete_notes,
                'complete_exercises': complete_exercises,
                'average_score': round(average_score, 2)
            }
        }
    )

    # 所属班级信息统计
    notes = Note.objects.filter(resource__icontains='.lesson_report').exclude(user__status=User.USER.DELETE)
    note_list = notes.values('user__classes', 'user__classes__name').annotate(
        note_count=Count('user__classes')).exclude(user__classes=None)
    note_dicts = {note['user__classes']: note for note in note_list}
    if user_obj.classes.id in note_dicts.keys():
        class_complete_experiments = note_dicts.get(user_obj.classes.id).get('note_count')
    else:
        class_complete_experiments = 0

    lesson_record_solveds = course_model.LessonPaperRecord.objects.filter(solved=True)

    lesson_record_list = lesson_record_solveds.values("submit_user_id__classes",
                                                      "submit_user_id__classes__name").annotate(
        lesson_count=Count("submit_user_id__classes"))
    lesson_record_dicts = {lesson_record['submit_user_id__classes']: lesson_record for lesson_record in
                           lesson_record_list}
    if user_obj.classes.id in lesson_record_dicts.keys():
        class_complete_exercises = lesson_record_dicts.get(user_obj.classes.id).get('lesson_count')
    else:
        class_complete_exercises = 0

    record_queryset = course_model.Record.objects.filter(progress=course_model.Record.Progress.LEARED).exclude(
        user__status=User.USER.DELETE)
    class_records = record_queryset.values('user__classes', 'user__classes__name', 'user__faculty__name',
                                           'user__major__name').annotate(
        complete_lessons=Count('user__classes')).exclude(user__classes=None)
    class_record_dicts = {class_record['user__classes']: class_record for class_record in class_records}
    if user_obj.classes.id in lesson_record_dicts.keys():
        class_complete_lessons = class_record_dicts.get(user_obj.classes.id).get('complete_lessons')
    else:
        class_complete_lessons = 0
    class_count = User.objects.filter(classes_id=user_obj.classes.id).count()
    context.update({
        'class_info_statistics': {
            'class': user_obj.classes.name,
            'organization': user_obj.faculty.name + ' / ' + user_obj.major.name,
            'class_count': class_count,
            'class_complete_experiments': class_complete_experiments if class_complete_experiments else 0,
            'class_complete_exercises': class_complete_exercises if class_complete_exercises else 0,
            'class_complete_lessons': class_complete_lessons if class_complete_lessons else 0
        }
    })

    return JsonResponse(context)


def _get_dict_by_key(objs, key, direction_cn_name_list):
    obj_dicts = {}
    context = {}
    for obj in objs:
        get_key = obj.get(key)
        if get_key not in direction_cn_name_list:
            continue
        if obj_dicts.has_key(get_key):
            obj_dicts[get_key].append(obj['lesson_id'])
        else:
            obj_dicts[get_key] = [obj['lesson_id']]

    for direction_name, lesson_ids in obj_dicts.items():
        course_queryset = course_model.Course.objects.filter(lesson__in=lesson_ids).filter(status=Status.NORMAL)
        course_count = len(course_queryset.values('id').annotate(Count('id')))
        context.update({direction_name: course_count})

    return context


@api_view(['GET', ])
@permission_classes((IsAuthenticated, IsStaffPermission, ))
def exam_statistics(request):
    from event_exam.models import SubmitRecord
    from practice.models import PracticeSubmitSolved
    context_list = []
    user_id = request.GET.get('user')
    username = User.objects.filter(id=int(user_id)).first().username
    thoery_queryset = SubmitRecord.objects.filter(user_id=int(user_id))
    if thoery_queryset.exists():
        for theory in thoery_queryset:
            context_list.append({
                'username': username,
                'score': round(theory.score, 2),
                'exam_type': _('x_theory_exam'),
                'exam_name': theory.event.name
            })
    # practice_queryset = PracticeSubmitSolved.objects.filter(submit_user_id=1)
    # if practice_queryset.exists():
    #     for practice in practice_queryset:
    #         context_list.append({
    #             'username': username,
    #             'score': practice.score,
    #             'exam_type': _get_exam_type(int(practice.type)),
    #             'exam_name': _get_exam_name(practice.type, practice.task_hash)
    #         })
    return JsonResponse({"total": len(context_list), "rows": context_list[0:10]})


def _get_exam_name(p_type, hash):
    from practice.private_api import _get_task_object
    task_detail = _get_task_object(p_type, hash)
    return task_detail


def _get_exam_type(type):
    if type == 1:
        return _('x_jeopardy')
    if type == 2:
        return _('x_trial_game')
    if type == 4:
        return _('x_ad_game')
    if type == 5:
        return _('x_event_infiltration')


@api_view(['GET', ])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def statistics(request, course_id):
    if is_en(request):
        ORGANIZATION = ORGANIZATION_EN
    else:
        ORGANIZATION = ORGANIZATION_CN

    course_id = int(course_id)
    course_obj = get_object_or_404(course_model.Lesson, id=course_id)

    product_type = get_product_type()
    faculty_list = Faculty.objects.all()
    major_list = Major.objects.all()
    classes_list = Classes.objects.all()

    context = {
        'product_type': product_type,
        'faculty_list': faculty_list,
        'major_list': major_list,
        'classes_list': classes_list,
        'course': course_obj,
        'ORGANIZATION': ORGANIZATION,
        'course_type': int(course_obj.type),
    }

    return render(request, 'course/cms/course_statistics.html', context)


@api_view(['GET', ])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def statistics_detail(request, course_id, user_id):
    course_id = int(course_id)
    user_id = int(user_id)

    course_obj = get_object_or_404(course_model.Course, id=course_id)
    lesson_list = course_model.Lesson.objects.filter(status=Status.NORMAL, course=course_obj).values('id', 'name')

    user = get_object_or_404(User, id=user_id)

    context = {
        'course': course_obj,
        'user': user,
        'lesson_list': lesson_list,
    }

    return render(request, 'course/cms/course_statistics_detail.html', context)


@api_view(['GET', ])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def lesson_exercises(request, lesson_id):
    lesson = get_object_or_404(course_model.Lesson, pk=int(lesson_id))
    context = {
        'mode': 0,
        'lesson': lesson
    }
    return render(request, 'course/cms/lesson_exercises.html', context)


@api_view(['GET', ])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def lesson_classroom(request, classroom_id):
    if is_en(request):
        ORGANIZATION = ORGANIZATION_EN
    else:
        ORGANIZATION = ORGANIZATION_CN
    classroom = get_object_or_404(course_model.CourseSchedule, pk=int(classroom_id))
    lesson = classroom.lesson
    context = {
        'id': classroom.id,
        'schedule_id': classroom.id,
        'lesson_id': lesson.id,
        'course_id': lesson.course_id,
        'lesson_name': lesson.name,
        'classes_id': classroom.classes_id,
        'is_experiment': course_model.Lesson.Type.EXPERIMENT == lesson.type and True or False,
        'ORGANIZATION': ORGANIZATION,
    }

    return render(request, 'course/cms/lesson_classroom.html', context)

@api_view(['GET', ])
def show_report_detail(request, note_id):
    context = {
        "note_id": note_id,
    }
    return render(request, 'course/cms/show_report_detail.html', context)
