# -*- coding: utf-8 -*-

import hashlib
import logging

from django.core.cache import cache
from django.db.models import Q, Sum
from django.urls import reverse
from django.utils.html import escape
from django.utils.translation import ugettext_lazy as _
from rest_framework import response, status, exceptions
from rest_framework.decorators import api_view, list_route
from rest_framework.response import Response

from common_calendar import api as calendar_api
from common_env.models import Env
from common_framework.models import AuthAndShare
from common_framework.utils.rest.list_view import list_view
from common_framework.utils.rest.mixins import DestroyModelMixin
from common_framework.utils.rest.validators import Validator
from oj import settings
from practice import constant
from practice.constant import TaskEventStatus
from practice.models import TaskEvent, PracticeSubmitSolved, PracticeSubmitLog
from practice.private_api import _get_task_list, _get_task_log_list, _get_event_rank, _commit_task_answer, \
    _get_task_serializer, _get_task_detail, _get_ch_type, _get_task_object, _get_tash_by_hashlist, _get_record_by_type, \
    _get_record_by_taskhash, _copy_task, _get_task_category, _get_task_category_by_name, _get_task_hash_list
from practice.utils.task import get_submit_score, get_choice_score, get_type_by_hash, \
    non_choice_answer, choice_answer, generate_task_hash
from practice.web.serializers import TaskEventSerializer, PracticeSubmitSolvedSerializer
from response import TaskResError

logger = logging.getLogger(__name__)

practice_config = {}
practice_instance = {}
practice_types = {}

PRACTICE_TYPE_THEORY = 0
PRACTICE_TYPE_REAL_VULN = 1
PRACTICE_TYPE_EXCRISE = 2
PRACTICE_TYPE_MAN_MACHINE = 3
PRACTICE_TYPE_ATTACK_DEFENSE = 4
PRACTICE_TYPE_INFILTRATION = 5

OJ_PRACTICE_TYPE_LIST = [
    PRACTICE_TYPE_THEORY,
    PRACTICE_TYPE_REAL_VULN,
    PRACTICE_TYPE_EXCRISE,
]

TYPE_NAME_MAP = {
    PRACTICE_TYPE_THEORY: 'x_theory',
    PRACTICE_TYPE_REAL_VULN: 'x_real_vuln',
    PRACTICE_TYPE_EXCRISE: 'x_exercise',
    PRACTICE_TYPE_MAN_MACHINE: 'x_man_machine',
    PRACTICE_TYPE_ATTACK_DEFENSE: 'x_ad_mode',
    PRACTICE_TYPE_INFILTRATION: 'x_infiltration',
}

PRACTICE_TYPE_EXCRISE_CATEGORY = ["Web", "Reverse", "Pwn", "Crypto", "Misc", "Mobile"]

DELIMITER = "|"


def register(p_type, category, practice_class=None):
    if p_type is None or category is None:
        return

    c = practice_config.get(p_type)
    if c is None:
        ch_type = _get_ch_type(p_type)
        practice_config[p_type] = category
        practice_types[p_type] = ch_type

    if practice_class:
        if issubclass(practice_class, Practice):
            practice_instance[p_type] = practice_class()


class PublicWriteModelMixin(object):
    @list_route(methods=['patch'], )
    def batch_public_writeup(self, request):
        ids = request.data.getlist('ids', [])
        if not ids:
            return Response(status=status.HTTP_204_NO_CONTENT)

        public = int(request.data.get('public', 0))

        queryset = self.queryset.filter(id__in=ids)
        if hasattr(self, 'clear_cache') and self.perform_batch_public_writeup(queryset, public):
            self.clear_cache()

        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_batch_public_writeup(self, queryset, public):
        if queryset.update(public_official_writeup=public) > 0:
            return True
        return False


class Practice(object):
    def get_task_list(self, event=None, category=None, difficult=None, task_name=None, public=None, **kwargs):
        task_list = self.queryset
        auth_faculty = kwargs.get('auth_faculty')
        auth_major = kwargs.get('auth_major')
        auth_classes = kwargs.get('auth_classes')

        if kwargs.get('user') is not None:
            user = kwargs.get('user')
        else:
            user = ''

        create_user_filed = getattr(task_list, 'create_user_filed') if \
            hasattr(task_list, 'create_user_filed') else None
        if not create_user_filed:
            create_user_filed = 'create_user'

        if auth_classes is not None and auth_classes != '':
            task_list = (task_list.filter(
                Q(event__auth_faculty__in=[auth_faculty], event__auth=AuthAndShare.AuthMode.CUSTOM_AUTH_MODE)) | task_list.filter(
                Q(event__auth_major__in=[auth_major], event__auth=AuthAndShare.AuthMode.CUSTOM_AUTH_MODE)) | task_list.filter(
                Q(event__auth_classes__in=[auth_classes], event__auth=AuthAndShare.AuthMode.CUSTOM_AUTH_MODE) |
                Q(event__auth=AuthAndShare.AuthMode.ALL_AUTH_MODE) |
                Q(**{'{create_user_filed}'.format(create_user_filed=create_user_filed): user})
            )).distinct()

        if event is not None and event != '':
            task_list = task_list.filter(event=event)

        if category is not None and category != '':
            task_list = task_list.filter(category=category)

        if difficult is not None and difficult != '':
            task_list = task_list.filter(difficulty_rating=int(difficult))

        if public is not None:
            task_list = task_list.filter(public=public)

        if task_name is not None and task_name != '':
            task_list = task_list.filter(Q(title__icontains=task_name) | Q(content__icontains=task_name))

        return task_list

    def get_task_log_list(self, classes=None, major=None, days=None):
        pass

    def get_event_rank_list(self, event=None, classes=None, major=None):
        pass

    def commit_task_answer(self, p_type, task, user, answer):
        """
        :param p_type: 类型（真实漏洞、夺旗解题）
        :param task: 题目
        :param user: 答题用户
        :param answer: 提交的答案
        :return: is_solved、score、content、error_code、all_score
        """
        if None == p_type or not task or not user or not answer:
            raise exceptions.ValidationError(TaskResError.PARAMETER_ERROR)

        # 已经完全答对了
        _record = self.get_all_rolved(user, task.hash, answer)
        if _record:
            rolved_log = PracticeSubmitSolved.objects.filter(submit_user=user, task_hash=task.hash)
            return {
                "is_solved": rolved_log.first().is_solved,
                "score": rolved_log.first().score,
                "content": task.title,
                "error_code": 0,
                "all_score": rolved_log.first().score,
                "is_over": True
            }
            # raise exceptions.ValidationError(TaskResError.HAS_ALL_ANSWER)

        # 写入答题记录
        self.save_submit_log(user, task.hash, answer, p_type)

        # 判断对错，总分数，当前flag的分数
        _solved, all_score, score = get_submit_score(p_type, task, answer, user)

        # 判断已得分数
        scored_points = self.get_scored_points(task.hash, user, score)

        # 判断答案是否已经是提交过得了。
        _record_answer = self.repeat_flag(user, task.hash, answer)
        if _record_answer:
            return {
                "is_solved": False,
                "score": scored_points - int(score),
                "content": task.title,
                "error_code": 1,
                "all_score": all_score
            }

        if _solved:
            cache.clear()
            _ret = self.handle_submit_solved(user, answer, task, p_type, scored_points, all_score)

        else:
            _ret = {
                "is_solved": _solved,
                'score': scored_points,
                "content": task.title,
                "error_code": 0,
                "all_score": all_score
            }
        return _ret

    def get_task_serializer(self):
        return self.serializer_class

    def get_task_detail(self, taskhash, backend=False):
        if backend:
            serializer = self.cms_serializer
        else:
            serializer = self.web_serializer
        try:
            task = self.task_class.objects.get(hash=taskhash)
        except:
            return None
        return serializer(task).data

    def get_task_object(self, taskhash):
        try:
            task = self.task_class.objects.get(hash=taskhash)
        except:
            task = None
        return task

    def get_task_by_hashlist(self, hashlist):
        try:
            task_list = self.task_class.objects.filter(hash__in=hashlist)
        except:
            task_list = None
        return task_list

    def get_record_by_person(self, user, is_solved, p_type):
        try:
            record_list = PracticeSubmitSolved.objects.filter(
                submit_user=user, is_solved=is_solved, type=p_type
            ).order_by("submit_time")
        except:
            record_list = None

        if record_list:
            return PracticeSubmitSolvedSerializer(record_list, many=True).data

        return None

    @staticmethod
    def sum_solved_score_by_hashlist(user, hashlist):
        all_score = PracticeSubmitSolved.objects.filter(submit_user=user, is_solved=True,
                                                        task_hash__in=hashlist).aggregate(
            Sum('score'))
        if all_score.get('score__sum') is not None:
            return all_score.get('score__sum')
        else:
            return 0

    def get_record_detail(self, user, taskhash):
        try:
            record_detail = PracticeSubmitSolved.objects.filter(submit_user=user, task_hash=taskhash).first()
        except:
            record_detail = None
        if record_detail:
            return PracticeSubmitSolvedSerializer(record_detail).data
        return None

    def copy_task(self, taskhash):
        p_type = get_type_by_hash(taskhash)
        try:
            new_task = self.task_class.objects.get(hash=taskhash)
        except:
            logger.error('{task_class} get hash {hash} is error!'.format(task_class=self.task_class.__name__,
                                                                         hash=taskhash))
            return None

        if new_task.is_dynamic_env:
            template_task_env = new_task.envs.filter(env__status=Env.Status.TEMPLATE).first()
        else:
            template_task_env = None

        new_task.pk = None
        new_task.is_copy = True
        new_task.hash = generate_task_hash(type=p_type)
        new_task.save()

        if template_task_env:
            template_task_env.pk = None
            template_task_env.save()
            new_task.envs.add(template_task_env)

        return new_task.hash

    def get_task_category(self, backend=False, **kwargs):
        if backend:
            serializer = self.category_cms_serializer
        else:
            serializer = self.category_web_serializer

        category_list = self.task_category.objects.all()
        return serializer(category_list, many=True, **kwargs).data

    def get_task_category_by_name(self, name):
        category = self.task_category.objects.filter(cn_name=name)
        if category:
            return category.first()
        return None

    def get_hash_list(self, event):
        task_list = self.get_task_list(event)
        hash_list = task_list.values('hash')
        return hash_list

    def get_solved_record(self, user, task_hash):
        return PracticeSubmitSolved.objects.filter(submit_user=user, task_hash=task_hash)

    def save_submit_log(self, user, task_hash, answer, p_type):
        PracticeSubmitLog.objects.create(
            submit_user=user,
            submit_answer=answer,
            task_hash=task_hash,
            type=p_type,
        )

    def save_submit_solved(self, user, task_hash, answer, p_type, score, w_score, is_solved=True):
        PracticeSubmitSolved.objects.create(
            submit_user=user,
            submit_answer=answer,
            score=score,
            weight_score=w_score,
            task_hash=task_hash,
            type=p_type,
            is_solved=is_solved,
        )

    def update_submit_solved(self, user, task_hash, answer, p_type, score, w_score, is_solved=True):
        pss = PracticeSubmitSolved.objects.filter(submit_user=user, task_hash=task_hash).first()
        if not pss:
            return

        answer_log = pss.submit_answer

        answer = answer_log + DELIMITER + answer

        pss.submit_answer = answer
        pss.score = score
        pss.is_solved = is_solved
        pss.weight_score = w_score

        pss.save()

    def get_all_rolved(self, user, task_hash, answer):
        rolved_log = PracticeSubmitSolved.objects.filter(submit_user=user, task_hash=task_hash)
        if rolved_log.count() > 0:
            return rolved_log.first().is_solved
        return False

    # 获取最新一共得分
    def get_scored_points(self, task_hash, user, score):
        score_flag = PracticeSubmitSolved.objects.filter(submit_user=user, task_hash=task_hash)
        if score_flag.count() > 0:
            scored_points = int(score_flag.first().score)
            all_scored_points = scored_points + int(score)
            return all_scored_points
        else:
            return int(score)

    def handle_submit_solved(self, user, answer, task, p_type, score, all_score):
        if not task or not user or not answer:
            return

        _pss = PracticeSubmitSolved.objects.filter(submit_user=user, task_hash=task.hash).first()
        w_score = int(score) * task.event.weight / 1000.0
        is_full_solved = True if score == all_score else False

        _fun = self.save_submit_solved if not _pss else self.update_submit_solved

        _fun(user, task.hash, answer, p_type, score, w_score, is_full_solved)

        return {
            "is_solved": True,
            'score': score,
            "content": task.title,
            "error_code": 0,
            "all_score": all_score
        }

    def repeat_flag(self, user, task_hash, answer):
        rolved_log = PracticeSubmitSolved.objects.filter(submit_user=user, task_hash=task_hash).first()
        if rolved_log:
            if answer in rolved_log.submit_answer.split(DELIMITER):
                return True
        return False


def get_task_type(category=None, event=None):
    pass


# 题目类型的删除
class RealDestroyModelMixin(DestroyModelMixin):
    def perform_batch_destroy(self, queryset):
        queryset.delete()
        return True


# 获取题目的统一接口
def get_task_list(p_type=None, event=None, category=None, difficult=None, task_name=None, public=None, **kwargs):
    if not p_type:
        tasks = []
        for t in practice_config:
            tasks.append(_get_task_list(t, event, category, difficult, task_name, public, **kwargs))

        return tasks

    # if category is not None and p_type is None:
    #     p_type = get_task_type(category)
    #
    # if event is not None and p_type is None:
    #     p_type = get_task_type(event)

    if p_type:
        return _get_task_list(p_type, event, category, difficult, task_name, public, **kwargs)


# 获取题目详情
def get_task_detail(p_type, taskhash, backend=False):
    if not p_type or not taskhash:
        return None
    if p_type and taskhash:
        task = _get_task_detail(p_type, taskhash, backend)
        return task


def get_task_info(taskhash, backend=False):
    if not taskhash:
        return None
    p_type = get_type_by_hash(taskhash)
    if p_type is None or not taskhash:
        return None
    task = _get_task_detail(p_type, taskhash, backend)
    return task


# 获取题目详情对象，
def get_task_object(taskhash):
    if not taskhash:
        return None

    p_type = int(taskhash.split('.')[-1])
    task = _get_task_object(p_type, taskhash)
    return task


# 根据type和hash获取题目列表
def get_task_list_by_hashlist(hashlist):
    type_list = {
        PRACTICE_TYPE_THEORY: [],
        PRACTICE_TYPE_REAL_VULN: [],
        PRACTICE_TYPE_EXCRISE: [],
        PRACTICE_TYPE_MAN_MACHINE: [],
        PRACTICE_TYPE_ATTACK_DEFENSE: [],
        PRACTICE_TYPE_INFILTRATION: [],
    }
    if hashlist:
        for taskhash in hashlist:
            task_type = get_type_by_hash(taskhash)
            if task_type is not None:
                type_list[task_type].append(taskhash)

        for task_type, task_list in type_list.items():
            type_list[task_type] = _get_tash_by_hashlist(task_type, task_list) or []

        all_task = []
        for task_list in type_list.values():
            all_task.extend(list(task_list))
        return all_task
    else:
        return []


# 获取答题记录的统一接口
def get_task_log_list(p_type=None, classes=None, major=None, days=None):
    if not p_type:
        tasklogs = []
        for t in practice_config:
            tasklogs.append(_get_task_log_list(t, major, classes, days))

        return tasklogs
    else:
        return _get_task_log_list(p_type, major, classes, days)


# 获取练习成绩的统一接口
def get_task_soved_list(p_type=None, event=None, classes=None, major=None):
    if p_type is not None:
        return _get_event_rank(p_type, event, classes, major)
    else:
        task_solved_list = []
        for t in practice_config:
            task_solved_list.append(_get_event_rank(t, event, classes, major))

        return task_solved_list


# 获取所有的类型
def get_type_list():
    return practice_config.keys()


# 根据名称获取类别
def get_task_category_by_name(p_type, name):
    if p_type is None:
        return None
    return _get_task_category_by_name(p_type, name)


# 根据类型获取习题集
def get_task_event_by_type(p_type, **kwargs):
    auth_classes = kwargs.get('auth_classes')
    event_list = TaskEvent.objects.all()
    if auth_classes is not None:
        event_list = event_list.filter(
            Q(auth_classes__in=[auth_classes, ])).distinct()

    if p_type is None:
        task_event_list = event_list.filter(status=TaskEventStatus.NORMAL, public=True).order_by('lock')
    else:
        task_event_list = event_list.filter(status=TaskEventStatus.NORMAL, type=int(p_type),
                                            public=True).order_by('lock')

    task_count = '''
                            CASE 
                                WHEN type = 0 THEN {theory} 
                                WHEN type = 1 THEN {real_vuln} 
                                WHEN type = 2 THEN {ctf} 
                                WHEN type = 3 THEN {man_machine}
                                WHEN type = 5 THEN {infiltration}
                            END
                        '''.format(
        theory='(SELECT COUNT(*) FROM practice_theory_choicetask WHERE practice_theory_choicetask.event_id = practice_taskevent.id '
               'AND practice_theory_choicetask.status=1 AND practice_theory_choicetask.is_copy=0 AND practice_theory_choicetask.public=1)',
        real_vuln='(SELECT COUNT(*) FROM practice_real_vuln_realvulntask WHERE practice_real_vuln_realvulntask.event_id = practice_taskevent.id '
                  'AND practice_real_vuln_realvulntask.status=1 AND practice_real_vuln_realvulntask.is_copy=0 AND practice_real_vuln_realvulntask.public=1)',
        ctf='(SELECT COUNT(*) FROM practice_exercise_practiceexercisetask WHERE practice_exercise_practiceexercisetask.event_id = practice_taskevent.id '
            'AND practice_exercise_practiceexercisetask.status=1 AND practice_exercise_practiceexercisetask.is_copy=0 AND practice_exercise_practiceexercisetask.public=1)',
        man_machine='(SELECT COUNT(*) FROM practice_man_machine_manmachinetask WHERE practice_man_machine_manmachinetask.event_id = practice_taskevent.id '
                    'AND practice_man_machine_manmachinetask.status=1 AND practice_man_machine_manmachinetask.is_copy=0 AND practice_man_machine_manmachinetask.public=1)',
        infiltration='(SELECT COUNT(*) FROM practice_infiltration_practiceinfiltrationtask WHERE practice_infiltration_practiceinfiltrationtask.event_id = practice_taskevent.id '
                    'AND practice_infiltration_practiceinfiltrationtask.status=1 AND practice_infiltration_practiceinfiltrationtask.is_copy=0 AND practice_infiltration_practiceinfiltrationtask.public=1)',
    )
    queryset = task_event_list.extra(
        select={'task_count': task_count}
    )
    rows = []
    for event in queryset:
        if event.task_count > 0:
            rows.append(event)
    return rows


# 根据类型获取序列化
def get_task_serializer(p_type):
    if p_type:
        task_serializer = _get_task_serializer(p_type)
        return task_serializer
    else:
        return None


# 根据类型获取已答对题目
def get_record_by_type(user, p_type, is_solved):
    if p_type is not None:
        record_list = _get_record_by_type(user, p_type, is_solved)
        return record_list
    else:
        return None


# 获取题目答题详情
def get_task_record_by_hash(user, p_type, taskhash):
    if p_type is not None:
        record_detail = _get_record_by_taskhash(user, p_type, taskhash)
        return record_detail
    else:
        return None


def get_all_flag(p_type, taskhash, user):
    if not str(p_type) or not taskhash:
        return 0, 0
    elif p_type == PRACTICE_TYPE_THEORY:
        return 0, 0
    elif (p_type == PRACTICE_TYPE_REAL_VULN or p_type == PRACTICE_TYPE_EXCRISE) and taskhash:
        if taskhash.split(".")[1] == str(PRACTICE_TYPE_REAL_VULN):
            from practice_real_vuln.models import RealVulnTask
            flag_text = RealVulnTask.objects.filter(hash=taskhash).first()
        elif taskhash.split(".")[1] == str(PRACTICE_TYPE_EXCRISE):
            from practice_exercise.models import PracticeExerciseTask
            flag_text = PracticeExerciseTask.objects.filter(hash=taskhash).first()

        if flag_text.score_multiple:
            flag_len = flag_text.score_multiple.split(DELIMITER)
            total_score = reduce(lambda x, y: int(x) + int(y), flag_len)
        else:
            total_score = flag_text.score

        try:
            record_detail = PracticeSubmitSolved.objects.filter(submit_user=user, task_hash=taskhash).first()
        except:
            record_detail = total_score, 0

        if record_detail:
            current_score = record_detail.score
            return total_score, current_score

        return total_score, 0
    else:
        return 0, 0


# 根据hash列表拷贝题目
def copy_task_by_hash(hashlist):
    copy_task_list = []

    for task_hash in hashlist:
        p_type = int(task_hash.split('.')[-1])
        copy_task_hash = _copy_task(p_type, task_hash)
        if copy_task_hash is None:
            continue
        copy_task_list.append(copy_task_hash)

    return copy_task_list


# 判断题目答案是否正确
def validate_answer(taskhash, answer, user, team=None):
    p_type = get_type_by_hash(taskhash)
    if p_type is None:
        return None

    submit_task = get_task_object(taskhash)
    if submit_task is None:
        return None

    if p_type == PRACTICE_TYPE_THEORY:
        is_solved, score, specific_score = get_choice_score(submit_task, answer, True)
    else:
        is_solved, score, specific_score = get_submit_score(p_type, submit_task, answer, user, team)

    return is_solved, score, specific_score


# 获取题目答案
def get_task_answer(taskhash, user):
    p_type = get_type_by_hash(taskhash)
    if p_type is None:
        return None

    submit_task = get_task_object(taskhash)
    if submit_task is None:
        return None

    if p_type == PRACTICE_TYPE_THEORY:
        answer = choice_answer(submit_task)
    else:
        answer = non_choice_answer(submit_task, user)

    return answer


# 根据类型获取题目种类
def get_category_by_type(p_type, backend=False, **kwargs):
    if p_type is None:
        return None
    else:
        return _get_task_category(p_type, backend, **kwargs)


# 获取夺旗解题，每种类型的得分比例
def get_solved_ratio(category_name, user):
    category = get_task_category_by_name(PRACTICE_TYPE_EXCRISE, category_name)
    if category is None:
        score = 0
    else:
        all_task_list = get_task_list(PRACTICE_TYPE_EXCRISE, None, category)
        all_hash_list = []
        all_score = 0

        for task in all_task_list:
            all_score += task.score
            all_hash_list.append(task.hash)

        if all_score == 0:
            score = 0
        else:
            all_web_solved_score = Practice.sum_solved_score_by_hashlist(user, all_hash_list)
            score = round((float(all_web_solved_score) / all_score), 2)

    return score


# 根据习题集获取hashlist
def get_hash_list(p_type, event):
    if p_type is not None:
        return _get_task_hash_list(p_type, event)
    else:
        return []


@api_view(['GET', ])
def get_personal_task_record(request):
    submit_record_solved_list = {}
    theory_record_list = get_record_by_type(request.user, PRACTICE_TYPE_THEORY, True)
    exercise_record_list = get_record_by_type(request.user, PRACTICE_TYPE_EXCRISE, True)
    man_machine_record_list = get_record_by_type(request.user, PRACTICE_TYPE_MAN_MACHINE, True)
    real_vuln_list = get_record_by_type(request.user, PRACTICE_TYPE_REAL_VULN, True)

    submit_record_solved_list[PRACTICE_TYPE_THEORY] = theory_record_list
    submit_record_solved_list[PRACTICE_TYPE_EXCRISE] = exercise_record_list
    submit_record_solved_list[PRACTICE_TYPE_MAN_MACHINE] = man_machine_record_list
    submit_record_solved_list[PRACTICE_TYPE_REAL_VULN] = real_vuln_list

    return response.Response(constant.to_response(submit_record_solved_list))


# 获取个人题目笔记
@api_view(['GET'])
def get_task_record_detail(request, task_hash):
    if not task_hash:
        return response.Response(constant.ILLEGAL_REQUEST_PARAMETERS, status=status.HTTP_200_OK)

    task_type = int(task_hash.split('.')[-1])
    task_record_detail = get_task_record_by_hash(request.user, task_type, task_hash)

    if task_type != 0:
        total_score, current_score = get_all_flag(task_type, task_hash, request.user)
        if task_record_detail is not None:
            score_per = round(current_score / (int(total_score) * 1.0), 2)
            task_record_detail.update({"score_per": score_per, })
        else:
            task_record_detail = {"score_per": 0}

    return response.Response(constant.to_response(task_record_detail))


# 提交答题记录
@api_view(['GET', 'POST'])
def commit_task_answer(request):
    if 'type_id' in request.POST and 'hash' in request.POST:
        p_type = int(request.POST['type_id'])
        submit_task = get_task_object(request.POST['hash'])
        user = request.user
        answer = request.POST.get('answer')

        # 没有答案
        if not answer:
            return response.Response(constant.ILLEGAL_REQUEST_PARAMETERS)

        _ret = _commit_task_answer(p_type, submit_task, user, answer)

        if p_type != 0:
            if submit_task.solving_mode:
                score_per = round(_ret["score"] / (int(_ret["all_score"]) * 1.0), 2)
                _ret.update({
                    "score_per": score_per,
                })
            else:
                score_per = 1 if _ret["is_solved"] else 0
                _ret.update({
                    "score_per": score_per,
                })

        if _ret["is_solved"] and p_type != 0:
            # 增加实操练习个人日历
            if _ret["content"] is not None and _ret["content"] != "":
                task_content = _ret["content"].encode('utf-8')
            else:
                task_content = ""
            if p_type == PRACTICE_TYPE_REAL_VULN:
                practice_type = _("x_real_vuln")
                calendar_api.add_calendar(practice_type, task_content, calendar_api.CALENDAR_PARCTICE_REAl,
                                          reverse("practice:defensetraintask",
                                                  kwargs={"typeid": p_type, 'task_hash': request.POST['hash']}),
                                          False, user=request.user)
            else:
                practice_type = _("x_practical_exercises")
                calendar_api.add_calendar(practice_type, task_content, calendar_api.CALENDAR_PARCTICE_EXE,
                                          reverse("practice:defensetraintask",
                                                  kwargs={"typeid": p_type, 'task_hash': request.POST['hash']}),
                                          False, user=request.user)

        return response.Response(constant.to_response(_ret))

    else:
        return response.Response(constant.ILLEGAL_REQUEST_PARAMETERS)


# 前台获取所有类型
@api_view(['GET', 'POST'])
def http_get_all_types(request):
    if request.method == 'GET':
        type_list = get_type_list()
        data = {
            'type_list': type_list,
        }
        return response.Response(constant.to_response(data))


# 前台根据类型获取习题集
@api_view(['GET', 'POST'])
def http_get_task_event_by_type(request):
    if request.method == 'GET':
        if request.user.is_superuser:
            auth_classes = None
        else:
            auth_classes = request.user.classes
        typeId = request.query_params['type_id']
        event_list = get_task_event_by_type(typeId, auth_classes=auth_classes)
        return list_view(request, event_list, TaskEventSerializer)


# 获取习题集详情
@api_view(['GET', ])
def http_get_event_detail(request, event_id):
    try:
        task_event = TaskEvent.objects.get(id=event_id)
    except:
        raise exceptions.NotFound()
    return response.Response(TaskEventSerializer(task_event).data, status=status.HTTP_200_OK)


# 前台获取题目列表
@api_view(['GET', 'POST'])
def http_get_task_list(request):
    if request.method == 'GET':
        event = ''
        category = ''
        difficult = ''
        task_name = ''
        p_type = request.query_params.get('type_id', None)
        has_solved = request.query_params.get('has_solved', None)
        if has_solved == 'true':
            has_solved = True
        if has_solved == 'false':
            has_solved = False
        if request.user.is_superuser:
            auth_classes = ''
            auth_major = ''
            auth_faculty = ''
        else:
            auth_faculty = request.user.faculty
            auth_major = request.user.major
            auth_classes = request.user.classes

        if p_type is None:
            return response.Response(constant.ILLEGAL_REQUEST_PARAMETERS, status=status.HTTP_200_OK)
        if 'event_id' in request.query_params and request.query_params['event_id'] != '':
            event = TaskEvent.objects.get(id=request.query_params['event_id'])
        if 'category' in request.query_params and request.query_params['category'] != '':
            category = request.query_params['category']
        if 'diffcult' in request.query_params and request.query_params['diffcult'] != '':
            difficult = request.query_params.get('diffcult', None)
        if 'task_name' in request.query_params and request.query_params['task_name'] != '':
            task_name = request.query_params.get('task_name', None)
        validator = Validator(request.query_params)
        validator.validate('offset', required=True, isdigit=True, min=0)
        validator.validate('limit', required=True, isdigit=True, min=0)
        if not validator.is_valid:
            return response.Response(constant.ILLEGAL_REQUEST_PARAMETERS, status=status.HTTP_200_OK)

        offset = int(request.query_params['offset'])
        limit = int(request.query_params['limit'])
        task_list_key = 'type={type}&event_id={event}&category={category}&difficult={difficult}&task_name={task_name}&auth_classes={auth_classes}&has_solved={has_solved}&offset={offset}&limit={limit}'.format(
            type=p_type, event=event, category=category, difficult=difficult, task_name=task_name,
            auth_classes=auth_classes, has_solved=has_solved, offset=offset, limit=limit)
        task_list_key = hashlib.md5(task_list_key).hexdigest()
        if cache.get(task_list_key) is not None:
            task_list = cache.get(task_list_key).get('task')
            total = cache.get(task_list_key).get('total')
        else:
            task_list = get_task_list(p_type, event, category, difficult, task_name, True, auth_classes=auth_classes,
                                      auth_faculty=auth_faculty, auth_major=auth_major, user=request.user)
            if has_solved is not None and has_solved != '':
                solved_hash_list = PracticeSubmitSolved.objects.filter(type=p_type, is_solved=True,submit_user=request.user).values_list('task_hash')
                if has_solved:
                    task_list = task_list.filter(hash__in=solved_hash_list)
                else:
                    task_list = task_list.exclude(hash__in=solved_hash_list)
            total = task_list.count()
            task_list = task_list[offset:offset + limit]
            cache.set(task_list_key, {'task': task_list, 'total': total}, 60)

        if task_list:
            queryset = task_list
        else:
            total = 0
            queryset = []
        rows = []
        for task in queryset:
            if int(task.hash.split('.')[-1]) != 0:
                difficulty = task.difficulty_rating
            else:
                difficulty = None
            is_solved = False
            submit_solved = PracticeSubmitSolved.objects.filter(task_hash=task.hash, submit_user=request.user)
            if submit_solved:
                is_solved = submit_solved.first().is_solved
            # if has_solved is not None and has_solved != '' and is_solved != has_solved:
            #     continue
            identifier = None
            if int(p_type) == PRACTICE_TYPE_REAL_VULN:
                identifier = task.identifier
            if int(p_type) == PRACTICE_TYPE_EXCRISE or int(p_type) == PRACTICE_TYPE_REAL_VULN:
                is_lock = task.lock
            else:
                is_lock = None
            language = getattr(request, 'LANGUAGE_CODE', settings.LANGUAGE_CODE)
            row = {'id': task.id,
                   'title_dsc': escape(task.title),
                   'category': task.category.en_name if language == 'en' else task.category.cn_name,
                   'content': task.content,
                   'event_name': task.event.name,
                   'score': task.score,
                   'hash': task.hash,
                   'difficulty_rating': difficulty,
                   'identifier': identifier,
                   'lock': is_lock,
                   'last_edit_time': task.last_edit_time,
                   'is_solved': is_solved}
            rows.append(row)
        return response.Response({'total': total, 'rows': rows}, status=status.HTTP_200_OK)


# 前台获取题目类型
@api_view(['GET'])
def http_task_category(request):
    try:
        p_type = request.GET['type_id']
    except:
        return response.Response(constant.ILLEGAL_REQUEST_PARAMETERS, status=status.HTTP_200_OK)

    category_list = get_category_by_type(p_type, False, context={'request': request})

    return response.Response(category_list, status=status.HTTP_200_OK)


# 前台获取题目详情
@api_view(['GET'])
def http_gettask_detail(request):
    try:
        p_type = request.GET['type_id']
        task_hash = request.GET['task_hash']
    except:
        return response.Response(constant.ILLEGAL_REQUEST_PARAMETERS, status=status.HTTP_200_OK)
    task_detail = get_task_detail(p_type, task_hash)
    if task_detail:
        return response.Response(constant.to_response(task_detail), status=status.HTTP_200_OK)
    else:
        return response.Response(constant.ILLEGAL_REQUEST_PARAMETERS, status=status.HTTP_200_OK)


# 前台获取习题集hash列表
@api_view(['GET'])
def http_gettask_hash_list(request):
    p_type = request.GET['type_id']
    if 'event_id' in request.query_params and request.query_params['event_id'] != '':
        event = TaskEvent.objects.get(id=request.query_params['event_id'])
    else:
        event = None
    cache_key = "hashlist?event={event}".format(event=event)
    cache_key = hashlib.md5(cache_key).hexdigest()
    if cache.get(cache_key) is not None:
        row = cache.get(cache_key)
    else:
        task_list = get_hash_list(p_type, event)
        row = [task.get('hash') for task in task_list]
        cache.set(cache_key, row, 60)
    return response.Response(constant.to_response(row), status=status.HTTP_200_OK)


# 前台获取CTF解题图表接口
@api_view(['GET'])
def http_get_radar_data(request):
    from common_auth.models import User
    radar_data = []
    user_id = request.GET.get('id')
    user = User.objects.filter(id=user_id).first()
    for category_name in PRACTICE_TYPE_EXCRISE_CATEGORY:
        radar_data.append(get_solved_ratio(category_name, user) if get_solved_ratio(category_name,
                                                                                    user) > 0.2 else 0.2)

    return response.Response(constant.to_response(radar_data), status=status.HTTP_200_OK)


@api_view(['GET'])
def http_get_env_servers(request):
    env_id = request.query_params.get('env_id')
    if env_id:
        from common_env.models import EnvTerminal
        envterminals = EnvTerminal.objects.filter(env_id=env_id)
        servers = [{
            'id': envterminal.sub_id,
            'name': envterminal.name,
        } for envterminal in envterminals]
    else:
        servers = []
    return response.Response(constant.to_response(servers), status=status.HTTP_200_OK)