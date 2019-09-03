# -*- coding: utf-8 -*-
import os

from django.db.models import Q, F, Min, Sum, Max, ProtectedError
from django.urls import reverse
from rest_framework.permissions import IsAuthenticated
from rest_framework import exceptions
from rest_framework.response import Response

from common_framework.utils import views as default_views
from common_framework.utils.request import is_en
from common_framework.utils.rest.permission import IsStaffPermission
from common_framework.utils.shortcuts import AppRender
from common_framework.utils.rest.validators import Validator

from common_auth.models import User, Classes
from common_auth.constant import GroupType

from django.utils.translation import ugettext_lazy as _

from event import models as event_models
from event_exam.models import SolvedRecord, SubmitRecord
from event.cms.api import EventViewSet
from event.models import Event
from event.utils import common
from event_exam.constant import ExamResError

from event_exam.setting import api_settings
########################################
from oj import settings
from oj.config import ORGANIZATION_EN, ORGANIZATION_CN
from practice_capability import models as capability_models
from practice_capability.models import TestPaper, TestPaperTask
from practice.api import get_task_object
import json
from rest_framework.decorators import api_view, permission_classes
from django.utils import timezone
from rest_framework import response, permissions
from common_framework.utils.cache import CacheProduct, delete_cache
from event_exam.utils.task import TaskHandler
from practice_capability.cms.viewset import TestPaperViewSet
from practice_capability.models import TestPaperTask
from django.shortcuts import render, HttpResponse
from practice import api as practice_api
from rest_framework import status
import StringIO
import xlwt
from event_exam import models as exam_models
from common_framework.utils.rest.list_view import list_view
from event_exam.cms.serializers import ListEventRankSerializer
from practice_theory.models import ChoiceTask

from x_note.models import Note
import collections

########################################
app_render = AppRender('event_exam', 'cms').render
#################################################
web_render = AppRender('event_exam', 'web').render
#################################################
slug = api_settings.SLUG


#################################################
@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def event_report_score(request, pk):
    if is_en(request):
        ORGANIZATION = ORGANIZATION_EN
    else:
        ORGANIZATION = ORGANIZATION_CN

    context = {}
    context['pk'] = pk
    context['ORGANIZATION'] = ORGANIZATION
    try:
        event = common.get_user_event(request.user, pk)
        context['event'] = event
        taskArrary = event_models.EventTask.objects.filter(event=pk)
        all_score = 0
        all_count = 0
        for t in taskArrary:
            all_count += 1
            all_score = all_score + t.task_score
        context['all_score'] = all_score
        context['all_count'] = all_count
        # 获取授权的班级,年级,院系

        auth_class_list = event.auth_classes.all()

        auth_major = []
        auth_faculty = []
        auth_class = []
        process = []
        # is authority
        process = [{'id': 0, 'status': _("x_answering")}, {'id': 1, 'status': _("x_submit_over")}]

        if len(auth_class_list) == 0:
            auth_class_list = Classes.objects.all()

        for classes in auth_class_list:
            auth_class.append(classes)
            major_dict = {
                'name': classes.major_name(),
                'id': classes.major_id,
                'parent_id': classes.major.faculty_id,
            }
            faculty_dict = {
                'name': classes.faculty_name(),
                'id': classes.faculty(),
            }

            if not auth_major.__contains__(major_dict):
                auth_major.append(major_dict)

            if not auth_faculty.__contains__(faculty_dict):
                auth_faculty.append(faculty_dict)

        context['process'] = process
        context['classes'] = auth_class
        context['majors'] = auth_major
        context['facultys'] = auth_faculty

    except event_models.Event.DoesNotExist as e:
        return default_views.Http404Page(request, e)

    return app_render(request, 'exam_result_list.html', context)

@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def event_achievement(request, pk):
    context = {}
    context['pk'] = pk
    context["num"] = int(request.query_params["num"])
    try:
        event = common.get_user_event(request.user, pk)
        context['event'] = event
    except event_models.Event.DoesNotExist as e:
        return default_views.Http404Page(request, e)

    return app_render(request, 'exam_achievement.html', context)


#################################################
@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def exam_list(request, **kwargs):
    return app_render(request, 'exam_list.html')


@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def name_check(request):
    if Event.objects.filter(name=request.POST.get('name'), type=Event.Type.EXAM).exists():
        return response.Response({'info': _("x_exams_name_already_exists")}, status=status.HTTP_200_OK)
    else:
        return response.Response({'info': u'', 'code': '0'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def exam_detail(request, pk, **kwargs):
    context = {}
    teachers = User.objects.filter(groups__id=GroupType.TEACHER).exclude(Q(id=request.user.id) | Q(status=0))
    context['teachers'] = teachers

    pk = int(pk)
    if pk == 0:
        context['mode'] = 0
    else:
        try:
            event = common.get_user_event(request.user, pk)
        except event_models.Event.DoesNotExist as e:
            return default_views.Http404Page(request, e)

        context['mode'] = 1
        context['event'] = event
    ######################################################
    # totalEvent = event_models.Event.objects.all()
    # context['totalEvent'] = totalEvent
    ######################################################
    return app_render(request, 'exam_detail.html', context)


# def task_list(request, pk, **kwargs):
#     context = {}
#
#     pk = int(pk)
#     try:
#         event = event_models.Event.objects.get(pk=pk)
#     except event_models.Event.DoesNotExist as e:
#         return default_views.Http404Page(request, e)
#     context['event'] = event
#
#     return app_render(request, 'task_list.html', context)
###########################################################################
class Serializer:
    def __init__(self, raw, tpt):
        self.data = {
            'title': raw.title,
            'id': str(raw.id),
            'hash': str(raw.hash),
            'score': int(tpt.task_score),
            'content': raw.content
        }
        p_type = int(raw.hash.split('.')[-1])
        if p_type == 0:
            self.data['options'] = raw.option
            self.data['options_dsc'] = collections.OrderedDict(
                sorted(json.loads(raw.option).items(), key=lambda t: t[0]))
            self.data['is_choice_question'] = 1
            self.data['is_multiple_choice'] = 1 if raw.multiple else 0


class SerializerNew:
    def __init__(self, raw, tpt, type=None):
        if type == 'TestPaperTask':
            score = int(tpt.score)
        else:
            score = int(tpt.task_score)
        self.data = {
            'title': raw.title,
            'id': str(raw.id),
            'hash': str(raw.hash),
            'score': score,
            'content': raw.content
        }
        p_type = int(raw.hash.split('.')[-1])
        if p_type == 0:
            self.data['option'] = raw.option
            self.data['options_dsc'] = collections.OrderedDict(
                sorted(json.loads(raw.option).items(), key=lambda t: t[0]))
            self.data['multiple'] = True if raw.multiple else False


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def task_list_new(request, pk):
    context = {
        'mode': 1,
    }
    event_exam_id = int(pk)
    event_exam = event_models.Event.objects.get(id=event_exam_id)

    context['event_exam_id'] = event_exam_id
    context['name'] = event_exam.name
    context['description'] = event_exam.description
    return app_render(request, 'testpaper_detail_new.html', context)


@api_view(['POST', "GET"])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def handler_task_list(request, pk):
    examname = request.data.get('examname', '')
    examDescription = request.data.get('examDescription', '')
    datas = request.data.get('data', '')
    event_exam_id = int(pk)
    if request.method == "GET":
        rows = []
        copyCap = request.query_params.get('copyCap', '')
        if copyCap.isdigit():
            taskArrary = TestPaperTask.objects.filter(test_paper__id=copyCap)

            for t in taskArrary:
                task = get_task_object(t.task_hash)
                data = SerializerNew(task, t, 'TestPaperTask').data
                rows.append(data)
        else:
            taskArrary = event_models.EventTask.objects.filter(event__id=event_exam_id)

            for t in taskArrary:
                task = get_task_object(t.task_hash)
                data = SerializerNew(task, t).data
                rows.append(data)

        return Response(data=rows, status=status.HTTP_200_OK)

    if not datas or not json.loads(datas):
        raise exceptions.ParseError(ExamResError.NO_EXAM_QUESTIONS)
    datas = json.loads(datas)

    if not examname:
        raise exceptions.ParseError(ExamResError.WARN_MESSAGES_8)
    if event_models.Event.objects.filter(type=event_models.Event.Type.EXAM, name=examname).exclude(
            pk=event_exam_id).exists():
        raise exceptions.ParseError(ExamResError.WARN_MESSAGES_9)

    event_exam = event_models.Event.objects.filter(id=event_exam_id)
    if not event_exam:
        raise exceptions.NotFound(ExamResError.NOT_FOUND_EXAM)
    event_exam = event_exam[0]
    event_exam.name = examname
    event_exam.description = examDescription
    event_exam.save()

    event_task_list = event_models.EventTask.objects.filter(event=event_exam)
    if event_task_list:
        # 判断原来是否存在初始数据, 批量删除
        try:
            event_models.EventTask.objects.filter(event=event_exam).delete()
        except ProtectedError:
            raise exceptions.ParseError(ExamResError.CANNT_CHANGE_HAS_DONE)

    task_hashs = []
    for data in datas:
        task_hashs.append(data['hash'])
    task_copy_hashs = practice_api.copy_task_by_hash(task_hashs)

    event_task_list = []
    new_topic_list = []
    for data in datas:
        task_type = TaskHandler.get_type_by_hash(data['hash'])
        event_task = event_models.EventTask(
            event=event_exam,
            task_hash=task_copy_hashs[task_hashs.index(data['hash'])],
            task_score=data['score'],
            type=task_type,
            seq=1,
        )
        event_task_list.append(event_task)
        new_topic_dict = {}
        if TaskHandler.get_type_by_hash(data.get("hash")) == 0:
            new_topic = ChoiceTask.objects.filter(hash=task_copy_hashs[task_hashs.index(data.get("hash"))]).first()
            if new_topic is None:
                raise exceptions.ParseError(ExamResError.TESTPAPER_ABNORMAL)
            try:
                new_topic_dict["content"] = new_topic.content
                new_topic_dict["id"] = new_topic.id
                new_topic_dict["option"] = new_topic.option
                new_topic_dict["score"] = data['score']
                new_topic_dict["multiple"] = new_topic.multiple
                new_topic_list.append(new_topic_dict)
            except ProtectedError:
                raise exceptions.ParseError(ExamResError.TESTPAPER_ABNORMAL)
        else:
            tmp = practice_api.get_task_info(task_copy_hashs[task_hashs.index(data.get("hash"))], backend=True)
            if tmp is None:
                raise exceptions.ParseError(ExamResError.TESTPAPER_ABNORMAL)
            try:
                new_topic_dict["title"] = tmp["title"]
                new_topic_dict["content"] = tmp["content"]
                new_topic_dict["id"] = tmp['id']
                new_topic_dict["hash"] = tmp["hash"]
                new_topic_dict["file_url"] = tmp["file_url"] if tmp.has_key("file_url") else None
                new_topic_dict["attach_url"] = tmp["file_url"].get("url", None) if tmp.get("file_url", None) else None
                new_topic_dict["url"] = tmp["url"] if tmp.get("url", None) else None
                new_topic_dict["is_dynamic_env"] = tmp["is_dynamic_env"]
                new_topic_dict["solving_mode"] = tmp["solving_mode"]
                new_topic_dict["option"] = None
                new_topic_dict["score"] = data['score']
                new_topic_dict["multiple"] = 4
                new_topic_list.append(new_topic_dict)
            except ProtectedError:
                raise exceptions.ParseError(ExamResError.TESTPAPER_ABNORMAL)

    datas = json.dumps(new_topic_list)

    json_name = str(event_exam.hash + ".json")
    json_url = os.path.join(settings.BASE_DIR, 'media/event_exam/json/{}'.format(json_name))
    with open(json_url, "w", ) as f:
        f.write(datas)
        f.close()

    event_models.EventTask.objects.bulk_create(event_task_list)
    return Response(data={'type': 'success'}, status=status.HTTP_200_OK)


########################################################################################
def task_detail(request, pk, task_pk, **kwargs):
    context = {}

    pk = int(pk)
    try:
        event = common.get_user_event(request.user, pk)
    except event_models.Event.DoesNotExist as e:
        return default_views.Http404Page(request, e)
    context['event'] = event

    task_pk = int(task_pk)
    if task_pk == 0:
        context['mode'] = 0
    else:
        try:
            task = event_models.EventTask.objects.get(pk=task_pk)
        except event_models.EventTask.DoesNotExist as e:
            return default_views.Http404Page(request, e)
        context['task'] = task

    return app_render(request, 'task_detail.html', context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def auth_class(request, exam_id):
    from common_cms import views as cms_views
    context = {
        'url_list_url': reverse("cms_event_exam:exam_list"),
        'query_auth_url': reverse("cms_event_exam:api:event-get-auths", kwargs={'pk': exam_id}),
        'query_all_auth_url': reverse("cms_event_exam:api:event-get-all-auth", kwargs={'pk': exam_id}),
        'modify_auth_url': reverse("cms_event_exam:api:event-set-auths", kwargs={'pk': exam_id}),
    }

    return cms_views.auth_class(request, context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def share_teacher(request, event_id):
    from common_cms import views as cms_views
    context = {
        'url_list_url': reverse("cms_event_exam:exam_list"),
        'query_share_url': reverse("cms_event_exam:api:event-get-shares", kwargs={'pk': event_id}),
        'modify_share_url': reverse("cms_event_exam:api:event-set-shares", kwargs={'pk': event_id}),
    }

    return cms_views.share_teacher(request, context)

@api_view(['GET'])
@permission_classes((permissions.AllowAny,))
def outputResult(request, pk):
    context = {}
    context['pk'] = pk
    try:
        event = common.get_user_event(request.user, pk)
        context['event'] = event
        task_arrary = event_models.EventTask.objects.filter(event=pk)
        all_score = 0
        all_count = 0
        for t in task_arrary:
            all_count += 1
            all_score = all_score + t.task_score
        context['all_score'] = all_score
        context['all_count'] = all_count
    except event_models.Event.DoesNotExist as e:
        return default_views.Http404Page(request, e)
    events = event_models.Event.objects.get(pk=pk)
    eventset = SubmitRecord.objects.filter(event=events)
    queryset = eventset.values('user__id').annotate(obj_id=F('user__id'), obj_name=F('user__first_name'), obj_username=F('user__username'))
    write_up_list = []
    tash_list = []
    # for task in task_arrary:
    #     task_hash = str(task.task_hash)
    #
    #     write_up_di_lict = Note.objects.filter(resource=task_hash)
    #     tash_list.append(task_hash)
    #     write_up_list.append(write_up_di_lict)

    queryset = queryset.annotate(
        start_time=Min('submit_time'),
        sum_score=Sum('score'),
        submit_time=Max('submit_time'),
    ).order_by('-sum_score', 'submit_time')

    for qs in queryset:
        note = Note.objects.filter(resource=events.hash, user_id=qs['obj_id']).first()
        wr_score = qs['sum_score']
        if note:
            qs['sum_score'] = wr_score + note.score
            qs['writeup_score'] = note.score

    wb = xlwt.Workbook(encoding='utf-8')
    sheet = wb.add_sheet('考试结果')
    pattern = xlwt.Pattern()  # Create the Pattern
    pattern.pattern = xlwt.Pattern.SOLID_PATTERN  # May be: NO_PATTERN, SOLID_PATTERN, or 0x00 through 0x12
    pattern.pattern_fore_colour = 5  # 0 = Black, 1 = White, 2 = Red, 3 = Green, 4 = Blue, 5 = YelloW
    borders = xlwt.Borders()  # Create Borders
    borders.left = xlwt.Borders.THIN  # NO_LINE, THIN, MEDIUM, DASHED, DOTTED, THICK, DOUBLE,
    borders.right = xlwt.Borders.THIN
    borders.top = xlwt.Borders.THIN
    borders.bottom = xlwt.Borders.THIN
    style_border = xlwt.XFStyle()  # Create Style
    style_border_color = xlwt.XFStyle()
    style_border.borders = borders  # Add Borders to Style
    style_border_color.borders = borders
    style_border_color.pattern = pattern
    sheet = excelHead(sheet, context, style_border, style_border_color)
    sheet = excelContent(sheet, queryset, style_border)

    wb.save('report.xls')
    sio = StringIO.StringIO()
    wb.save(sio)
    sio.seek(0)
    response = HttpResponse(sio.getvalue(), content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename=report.xls'
    response.write(sio.getvalue())
    return response


def excelHead(sheet, context, style_border, style_border_color):
    sheet.write(0, 0, "比赛名称", style_border_color)
    sheet.write(1, 0, "比赛开始时间", style_border_color)
    sheet.write(2, 0, "比赛结束时间", style_border_color)
    sheet.write(3, 0, "试卷总分", style_border_color)
    sheet.write(4, 0, "总题数", style_border_color)
    event = context["event"]
    sheet.write(0, 1, event.name, style_border)
    sheet.write(1, 1, event.start_time.strftime("%Y-%m-%d %H:%M:%S"), style_border)
    sheet.write(2, 1, event.end_time.strftime("%Y-%m-%d %H:%M:%S"), style_border)
    sheet.write(3, 1, context["all_score"], style_border)
    sheet.write(4, 1, context["all_count"], style_border)
    sheet.write(6, 0, "姓名", style_border_color)
    sheet.write(6, 1, "开始考试时间", style_border_color)
    sheet.write(6, 2, "提交试卷时间", style_border_color)
    sheet.write(6, 3, "成绩", style_border_color)
    sheet.write(6, 4, "排名", style_border_color)
    return sheet


def excelContent(sheet, queryset, style_border):
    row = 7
    rank = 1
    queryset = sorted(list(queryset), key=lambda a: a.get('sum_score'), reverse=True)
    for ele in queryset:
        sheet.write(row, 0, ele['obj_name'], style_border)
        sheet.write(row, 1, ele['start_time'].strftime("%Y-%m-%d %H:%M:%S"), style_border)
        sheet.write(row, 2, ele['submit_time'].strftime("%Y-%m-%d %H:%M:%S"), style_border)
        sheet.write(row, 3, ele['sum_score'], style_border)
        sheet.write(row, 4, rank, style_border)
        rank = rank + 1
        row = row + 1

    return sheet


@api_view(['POST', "GET"])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def event_rank_list(request):
    event_id = request.GET.get('event', int)
    process = request.GET.get('process', int)
    faculty = request.GET.get('faculty', int)
    major = request.GET.get('major', int)
    classes = request.GET.get('classes', int)
    event = common.get_user_event(request.user, event_id)
    auth_class_list = event.auth_classes.all()
    keyword = request.GET.get("search", None)

    if len(auth_class_list) == 0:
        type = 'unAuthority'
        user_list = User.objects.all()
    else:
        type = 'authoritied'

        auth_class_list = event.auth_classes.all()

        auth_class_id_list = {auth_class.id for auth_class in auth_class_list}
        user_list = User.objects.all().filter(classes__id__in=auth_class_id_list)


    user_id_list = []

    # 如果按班级为单位筛选
    if classes != '':
        # 获取全班所有学生
        user_list = user_list.filter(classes__id=classes)

    elif major != '':
        user_list = user_list.filter(major__id=major)

    elif faculty != '':
        user_list = user_list.filter(faculty__id=faculty)

    else:
        user_list = user_list

    user_id_list = {user.id for user in user_list}

            # queryset = event_models.EventUserSubmitLog.objects.filter()
    # queryset = queryset.filter(event_task__event=event).filter(user__id__in=user_id_list)
    queryset = SolvedRecord.objects.filter()
    queryset = queryset.filter(event=event).filter(user__id__in=user_id_list)

    queryset = queryset.values('user__id').annotate(obj_id=F('user__id'), obj_name=F('user__first_name'), obj_username=F('user__username'))
    # 所有已提交记录
    queryset = queryset.annotate(submit_time=Max('solved_time'), ).order_by("-solved_time")
    if keyword != "" and keyword is not None:
        filter_list = []
        for user_result in queryset:
            if keyword in user_result["obj_name"] or keyword in user_result["obj_username"]:
                filter_list.append(user_result)
        queryset = filter_list
    res_list = []
    submit_list = []
    finish_list = []

    if queryset:
        for doing_user in queryset:
            doing_user['writeup_score'] = 0
            doing_user["submit_time"] = doing_user["submit_time"].strftime("%Y-%m-%d %H:%M:%S")
            doing_user['status'] = _("x_answering")
            doing_user['sum_score'] = 0
            if SubmitRecord.objects.filter(user=doing_user["obj_id"]).filter(event__id=event.id).exists():
                pass
            else:
                submit_list.append(doing_user)

    # 所有已交卷的
    did_queryset = SubmitRecord.objects.filter(event__id=event.id).filter(user__id__in=user_id_list)
    exam_did_list = did_queryset.values('user__id', 'submit_time').annotate(obj_id=F('user__id'), obj_name=F('user__first_name'), obj_username=F('user__username'), score=Sum('score'))


    if keyword != "" and keyword is not None:
        filter_list = []
        for user_result in exam_did_list:
            if keyword in user_result["obj_name"] or keyword in user_result["obj_username"]:
                filter_list.append(user_result)

        exam_did_list = filter_list

    if exam_did_list:
        for did_user in exam_did_list:
            did_user['status'] = _("x_submit_over")
            did_user['submit_time'] = did_user["submit_time"].strftime("%Y-%m-%d %H:%M:%S")
            did_user['writeup_score'] = 0
            did_user['sum_score'] = did_user["score"]
            finish_list.append(did_user)

    context = {}
    context['user_list'] = user_list.exclude(status=User.USER.DELETE)
    ret_list = []
    ret_list.extend(submit_list)
    ret_list.extend(finish_list)
    context['contain_list'] = ret_list

    if process == '':  # 如果是所有状态
        res_list.extend(submit_list)
        res_list.extend(finish_list)

        # not_exam_list = get_not_exam_user(context)
        # if len(not_exam_list) != 0:
        #     res_list.extend(not_exam_list)

    elif process == '1':  # 已交卷
        res_list.extend(finish_list)
    elif process == '0':  # 已提交
        res_list.extend(submit_list)
    # else:  # 如果是未开始状态
    #     res_list = get_not_exam_user(context)
    # if type == 'unAuthority':
    #     res_list = []

    return _list_view(request, res_list, ListEventRankSerializer)

def to_error(code, message):
    return {
        'error_code': code,
        'error_message': message
    }

ILLEGAL_REQUEST_PARAMETERS = to_error(0x0010, 'illegal request parameters')

def _list_view(request, queryset, serializer):
    validator = Validator(request.query_params)
    validator.validate('offset', required=True, isdigit=True, min=0)
    validator.validate('limit', required=True, isdigit=True, min=0)
    if not validator.is_valid:
        return response.Response(ILLEGAL_REQUEST_PARAMETERS, status=status.HTTP_200_OK)

    offset = int(request.query_params['offset'])
    limit = int(request.query_params['limit'])

    sort = request.GET.get("sort")
    order = request.GET.get("order")

    if sort is not None:
        order_status = True if order=="asc" else False
        if sort == "sum_score":
            queryset.sort(key=takeSecond, reverse= order_status)
        else:
            queryset.sort(key=takeSecond_time, reverse=order_status)

    total = len(queryset)
    queryset = queryset[offset:offset + limit]

    rows = [serializer(row).data for row in queryset]

    return response.Response({'total': total, 'rows': rows}, status=status.HTTP_200_OK)

# 获取列表的第二个元素
def takeSecond(elem):
    return elem["sum_score"]

def takeSecond_time(elem):
    return elem["submit_time"]

# 获取未开始的人
def get_not_exam_user(context):

    all_user = context['user_list']
    contain_user = context['contain_list']
    contain_user_ids = {user['obj_id'] for user in contain_user}
    all_list = list(all_user)
    res_list = []

    if all_list:
        for user in all_list:
            res_dict = {}

            if not contain_user_ids.__contains__(user.id):
                res_dict = {
                    'obj_id': user.id,
                    'obj_name': user.first_name,
                    'obj_username':user.username,
                    'sum_score': 0,
                    'writeup_score': 0,
                    'submit_time': '',
                    'status': '未开始',
                }
                res_list.append(res_dict)

    return res_list