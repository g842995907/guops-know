# -*- coding: utf-8 -*-
import logging
import collections

from django.core.cache import cache
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from rest_framework import exceptions, filters, mixins, viewsets
from rest_framework.permissions import IsAuthenticated

from common_auth.api import oj_auth_class
from common_framework.utils.request import get_ip
from common_framework.utils.rest import mixins as common_mixins

from common_auth.models import User

from event import models as event_models
from event.utils import common
from event.setting import api_settings
from event.utils.mixins import ProductMixin
from event.utils.task import TaskHandler, EventTaskHandler

from event_exam.models import SubmitRecord

from . import error
from . import serializers as mserializers

logger = logging.getLogger(__name__)


# 公共列表页面调用
class EventViewSet(ProductMixin,
                   common_mixins.CacheModelMixin,
                   viewsets.ReadOnlyModelViewSet):
    queryset = event_models.Event.objects.filter(public=True)
    serializer_class = mserializers.EventSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('name',)
    ordering_fields = ('process', 'start_time')
    ordering = ('process', '-start_time')

    def init_type_queryset(self):
        self.queryset = self.queryset.filter(type=self.event_type)

    @oj_auth_class
    def get_queryset(self):
        queryset = self.queryset

        event_type = self.query_data.get('type', int)
        if event_type is not None:
            queryset = queryset.filter(type=event_type)

        now = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        process = '''
            CASE 
                WHEN (start_time <= '{now}' and end_time > '{now}') THEN 0 
                WHEN start_time > '{now}' then 1 
                WHEN end_time <= '{now}' THEN 2 
            END
        '''.format(now=now)
        queryset = queryset.extra(
            select={'process': process},
        )
        return queryset

    def extra_handle_list_data(self, data):
        for row in data:
            # 比赛中各类型题目统计
            task_category = {}
            total_score = {}

            event_id = row.get('id')
            event_task_list = event_models.EventTask.objects.filter(event_id=event_id, public=True)
            task_id_list = {event.id for event in event_task_list}
            task_hash_list = {event.task_hash for event in event_task_list}
            task_list = TaskHandler.get_tasks(task_hash_list)
            event_task_hash_dict = {event_task.task_hash: event_task for event_task in event_task_list}
            if task_hash_list:
                for task in task_list:
                    if not task:
                        continue
                    language = self.request.LANGUAGE_CODE
                    if language != 'zh-hans':
                        task_category_name = task.category.en_name
                    else:
                        task_category_name = task.category.cn_name

                    event_task = event_task_hash_dict.get(task.hash)
                    if task_category.get(task_category_name):
                        task_category[task_category_name] += 1
                        if row.get('integral_mode') == 2:
                            total_score[task_category_name] += \
                            EventTaskHandler.get_task_current_dynamic_score(event_task)[0]
                        else:
                            total_score[task_category_name] += task.score
                    else:
                        task_category[task_category_name] = 1
                        if row.get('integral_mode') == 2:
                            total_score[task_category_name] = \
                            EventTaskHandler.get_task_current_dynamic_score(event_task)[0]
                        else:
                            total_score[task_category_name] = task.score

            row['task_category'] = collections.OrderedDict(
                sorted(task_category.items(), key=lambda t: t[1], reverse=True))
            row['total_score'] = total_score

            user_score = {}
            answer_queryset = event_models.EventUserAnswer.objects.all()
            user = self.request.user
            if user is not None:
                answer_queryset = answer_queryset.filter(user=user)

            # team = user.team
            # if team is not None:
            #     answer_queryset = answer_queryset.filter(team=team)

            if event_task_list is not None:
                answer_queryset = answer_queryset.filter(event_task__in=task_id_list)

            answer_queryset = answer_queryset.filter(status=event_models.EventUserAnswer.Status.NORMAL)
            if answer_queryset:
                for answer in answer_queryset:
                    task = TaskHandler.get_task_info(answer.event_task.task_hash)
                    if not task:
                        continue
                    task_category_name = task['category_name']
                    if user_score.get(task_category_name):
                        user_score[task_category_name] += answer.score
                    else:
                        user_score[task_category_name] = answer.score
            row['user_score'] = user_score

            row["grade"] = False
            user_grade = SubmitRecord.objects.filter(event=row["id"]).filter(user=user)
            if user_grade.exists():
                row["grade"] = True

        return data


class BaseEventSignupViewSet(ProductMixin,
                             common_mixins.CacheModelMixin,
                             mixins.CreateModelMixin,
                             mixins.DestroyModelMixin,
                             viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    ordering_fields = ('time',)
    ordering = ('-time',)

    def init_type_queryset(self):
        self.queryset = self.queryset.filter(event__type=self.event_type)

    def get_queryset(self):
        queryset = self.queryset

        event = self.query_data.get('event', int)
        if event is not None:
            queryset = queryset.filter(event=event)

        status = self.query_data.get('status', event_models.EventSignupUser.Status.values())
        if status is not None:
            queryset = queryset.filter(status=status)

        return queryset

    def _check_create(self, event):
        user = self.request.user
        # 比赛状态权限判断
        now = timezone.now()
        # 已结束
        if event.end_time < now:
            raise exceptions.PermissionDenied(error.EVENT_IS_OVER)

        # 用户状态权限判断
        if event.mode == event_models.Event.Mode.PERSONAL:
            is_signup = event_models.EventSignupUser.objects.filter(event=event, user=user).exists()
        elif event.mode == event_models.Event.Mode.TEAM:
            # 未加入队伍
            if not user.team:
                raise exceptions.PermissionDenied(error.USER_NO_TEAM_FOR_EVENT)
            is_signup = event_models.EventSignupTeam.objects.filter(event=event, team=user.team).exists()

        # 已报名
        if is_signup:
            raise exceptions.PermissionDenied(error.HAS_SIGNUPED_EVENT)

    def sub_perform_create(self, serializer):
        raise NotImplementedError('subclasses of BaseEventSignupViewSet must provide a sub_perform_create() method')

    def sub_perform_destroy(self, instance):
        instance.status = event_models.BaseEventSignup.Status.DELETE
        instance.save()
        return True


class EventSignupUserViewSet(BaseEventSignupViewSet):
    queryset = event_models.EventSignupUser.objects.all()
    serializer_class = mserializers.EventSignupUserSerializer
    search_fields = ('user__username', 'event__name')

    def get_queryset(self):
        queryset = super(EventSignupUserViewSet, self).get_queryset()
        queryset = queryset.filter(user=self.request.user)
        return queryset

    def sub_perform_create(self, serializer):
        event = serializer.validated_data['event']
        self._check_create(event)
        serializer.save(
            user=self.request.user,
            last_edit_user=self.request.user,
        )
        return True


class EventSignupTeamViewSet(BaseEventSignupViewSet):
    queryset = event_models.EventSignupTeam.objects.all()
    serializer_class = mserializers.EventSignupTeamSerializer
    search_fields = ('team__name', 'event__name')

    def get_queryset(self):
        queryset = super(EventSignupTeamViewSet, self).get_queryset()
        if self.request.user.team:
            queryset = queryset.filter(team=self.request.user.team)
        else:
            queryset = queryset.filter(pk__in=[])
        return queryset

    def sub_perform_create(self, serializer):
        event = serializer.validated_data['event']
        self._check_create(event)
        serializer.save(
            team=self.request.user.team,
            last_edit_user=self.request.user,
        )
        return True


# 队伍页面调用
class EventSignupTeamActivityViewSet(ProductMixin,
                                     common_mixins.CacheModelMixin,
                                     viewsets.ReadOnlyModelViewSet):
    queryset = event_models.EventSignupTeam.objects.all()
    serializer_class = mserializers.EventSignupTeamSerializer
    ordering_fields = ('event__start_time',)
    ordering = ('-event__start_time',)

    def get_queryset(self):
        queryset = self.queryset
        if self.request.user.team:
            queryset = queryset.filter(team=self.request.user.team)
        else:
            queryset = queryset.filter(pk__in=[])
        return queryset

    def extra_handle_list_data(self, data):
        eventSignups = {}
        for row in data:
            row['sum_score'] = 0
            eventSignups[row['event']] = row
        user_teamid = self.request.user.team_id
        if user_teamid:
            answers = event_models.EventUserAnswer.objects.filter(
                team_id=user_teamid,
                event_task__event__in=eventSignups.keys()
            ).values('event_task__event').annotate(sum_score=Sum('score'))
        else:
            answers = event_models.EventUserAnswer.objects.filter(
                event_task__event__in=eventSignups.keys()
            ).values('event_task__event').annotate(sum_score=Sum('score'))
        for answer in answers:
            eventSignups[answer['event_task__event']]['sum_score'] = answer['sum_score']

        return data



class EventTaskViewSet(ProductMixin,
                       common_mixins.CacheModelMixin,
                       viewsets.ReadOnlyModelViewSet):
    queryset = event_models.EventTask.objects.filter(public=True)
    serializer_class = mserializers.EventTaskSerializer
    permission_classes = (IsAuthenticated,)
    search_fields = ('event__name',)
    ordering_fields = ('event', 'seq')
    ordering = ('event', 'seq')

    unlimit_pagination = True

    def init_type_queryset(self):
        self.queryset = self.queryset.filter(event__type=self.event_type)

    def get_queryset(self):
        queryset = self.queryset

        event = self.query_data.get('event', int)
        if event is not None:
            queryset = queryset.filter(event=event)

        return queryset

    def extra_handle_list_data(self, data):
        return data


class EventWriteupViewSet(ProductMixin,
                          common_mixins.CacheModelMixin,
                          mixins.CreateModelMixin,
                          viewsets.ReadOnlyModelViewSet):
    queryset = event_models.EventWriteup.objects.all()
    serializer_class = mserializers.EventWriteupSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = ('time',)
    ordering = ('-time',)

    def init_type_queryset(self):
        self.queryset = self.queryset.filter(event__type=self.event_type)

    def get_queryset(self):
        queryset = self.queryset

        event_id = self.query_data.get('event', int)
        if event_id is not None:
            try:
                event = event_models.Event.objects.get(pk=event_id)
            except event_models.Event.DoesNotExist as e:
                raise exceptions.NotFound(error.EVENT_NOT_EXIST)

            queryset = queryset.filter(event=event)
            # 只能获取自己提交的
            if event.mode == event_models.Event.Mode.PERSONAL:
                queryset = queryset.filter(user=self.request.user)
            elif event.mode == event_models.Event.Mode.TEAM:
                if self.request.user.team:
                    queryset = queryset.filter(team=self.request.user.team)
                else:
                    queryset = queryset.filter(pk__in=[])
            else:
                queryset = queryset.filter(pk__in=[])
        else:
            queryset = queryset.filter(pk__in=[])

        return queryset

    def _check_create(self, event):
        user = self.request.user
        # 比赛状态权限判断
        now = timezone.now()
        # 未开始
        if event.start_time > now:
            raise exceptions.PermissionDenied(error.EVENT_NOT_START)
        # 比赛未开放提交writeup
        if not event.can_submit_writeup:
            raise exceptions.PermissionDenied(error.EVENT_CAN_NOT_SUBMIT_WRITEUP)

        # 用户状态权限判断
        if event.mode == event_models.Event.Mode.PERSONAL:
            # 未报名
            signup = event_models.EventSignupUser.objects.filter(event=event, user=user).first()
            if not signup:
                raise exceptions.PermissionDenied(error.USER_NOT_SIGNUP_EVENT)
        elif event.mode == event_models.Event.Mode.TEAM:
            # 未加入队伍
            if not user.team:
                raise exceptions.PermissionDenied(error.USER_NO_TEAM_FOR_EVENT)
            # 队伍未报名
            signup = event_models.EventSignupTeam.objects.filter(event=event, team=user.team).first()
            if not signup:
                raise exceptions.PermissionDenied(error.TEAM_NOT_SIGNUP_EVENT)
        else:
            logger.error('error event[%s] mode: %s', event.pk, event.mode)
            raise exceptions.PermissionDenied(error.PERMISSION_DENIED)

    def sub_perform_create(self, serializer):
        event = serializer.validated_data['event']
        if not serializer.validated_data.get('writeup'):
            raise exceptions.ValidationError(error.EVENT_EMPTY_WRITEUP)

        self._check_create(event)

        user = self.request.user

        fixed_params = {
            'user': user,
        }
        if event.mode == event_models.Event.Mode.PERSONAL:
            fixed_params['team'] = None
            delete_queryset = self.queryset.filter(
                event=event,
                user=self.request.user,
            )
        else:
            fixed_params['team'] = user.team
            delete_queryset = self.queryset.filter(
                event=event,
                team=user.team
            )

        with transaction.atomic():
            delete_queryset.update(
                status=event_models.EventWriteup.Status.DELETE
            )
            serializer.save(**fixed_params)
        return True


class EventUserSubmitLogViewSet(ProductMixin,
                                common_mixins.CacheModelMixin,
                                mixins.CreateModelMixin,
                                viewsets.GenericViewSet):
    queryset = event_models.EventUserSubmitLog.objects.all()
    serializer_class = mserializers.EventUserSubmitLogSerializer
    permission_classes = (IsAuthenticated,)
    task_handler_class = TaskHandler

    def init_type_queryset(self):
        self.queryset = self.queryset.filter(event_task__event__type=self.event_type)

    def list(self, request, *args, **kwargs):
        from rest_framework.response import Response
        return Response([])

    # 提交前的一些状态判断
    def _check_create(self, event_task):
        event = event_task.event
        user = self.request.user
        submit_flag = self.request.data.get("answer")

        # 题目状态权限判断
        if not event_task.public:
            raise exceptions.PermissionDenied(error.TASK_NOT_PUBLIC)

        # 比赛状态权限判断
        now = timezone.now()
        # 未开始
        if event.start_time > now:
            raise exceptions.PermissionDenied(error.EVENT_NOT_START)
        # 已结束
        elif event.end_time < now:
            raise exceptions.PermissionDenied(error.EVENT_IS_OVER)
        # 暂停中
        if event.status == event_models.Event.Status.PAUSE:
            raise exceptions.PermissionDenied(error.EVENT_IS_PAUSE)

        # 用户状态权限判断
        if event.mode == event_models.Event.Mode.PERSONAL:
            # 未报名
            signup = event_models.EventSignupUser.objects.filter(event=event, user=user).first()
            if not signup:
                raise exceptions.PermissionDenied(error.USER_NOT_SIGNUP_EVENT)
        elif event.mode == event_models.Event.Mode.TEAM:
            # 未加入队伍
            if not user.team:
                raise exceptions.PermissionDenied(error.USER_NO_TEAM_FOR_EVENT)
            # 队伍未报名
            signup = event_models.EventSignupTeam.objects.filter(event=event, team=user.team).first()
            if not signup:
                raise exceptions.PermissionDenied(error.TEAM_NOT_SIGNUP_EVENT)

        # 被禁赛
        if signup.status == event_models.BaseEventSignup.Status.FORBIDDEN:
            raise exceptions.PermissionDenied(error.EVENT_SIGNUP_FORBIDDEN)

        # 限制提交频率
        submit_key = '{prefix}:{task}:%s'.format(
            prefix=self.__class__.__name__,
            task=event_task.id
        )
        if event.mode == event_models.Event.Mode.PERSONAL:
            submit_key = submit_key % user.id
            submit_cache = cache.get(submit_key)
        elif event.mode == event_models.Event.Mode.TEAM:
            submit_key = submit_key % user.team.id
            submit_cache = cache.get(submit_key)

        if submit_cache:
            raise exceptions.PermissionDenied(error.SUBMIT_TOO_SOON)
        cache.set(submit_key, 1, 10)

        # 判断是不是已提交
        if event.mode == event_models.Event.Mode.PERSONAL:
            task_status = event_models.EventUserAnswer.objects.filter(user=user, event_task=event_task).first()
            if task_status:
                if submit_flag in task_status.answer.split("|"):
                    raise exceptions.PermissionDenied(error.USER_DUMPLICATE_SUBMIT)
        elif event.mode == event_models.Event.Mode.TEAM:
            task_status = event_models.EventUserAnswer.objects.filter(team=user.team, event_task=event_task).first()
            if task_status:
                if submit_flag in task_status.answer.split("|"):
                    raise exceptions.PermissionDenied(error.TEAM_DUMPLICATE_SUBMIT)

    def get_event_task(self, serializer):
        event_task = serializer.validated_data['event_task']
        return event_task

    # flag判断对错，日志、答题表的创建
    def sub_perform_create(self, serializer):
        event_task = self.get_event_task(serializer)
        self._check_create(event_task)

        event = event_task.event

        self.extra_attr.event = event
        self.extra_attr.event_task = event_task

        user = self.request.user

        fixed_params = {
            'user': user,
            'submit_ip': get_ip(self.request),
            'event_task': event_task,
        }

        team = None
        if event.mode == event_models.Event.Mode.TEAM:
            fixed_params['team'] = user.team
            team = user.team

        # 获取提交的flag
        answer = self.request.data.get("answer")

        task_handler = self.task_handler_class(event_task.task_hash)
        try:
            has_solved, all_score, score = task_handler.validate_answer(user, answer, team)
        except Exception as e:
            raise exceptions.ValidationError(error.TASK_ERROR)

        with transaction.atomic():
            if has_solved:
                # 获取已获得得分数
                get_score, schedule_score = self.get_scored_points(event_task, user, score)
                # 计算进度
                schedule = float(schedule_score) / float(all_score)
                # 页面返回“已解决”
                fixed_params['is_solved'] = True

                event_user_answer_params = {
                    'user': user,
                    'last_edit_user': user,
                    'event_task': event_task,
                    'schedule': schedule,
                    'schedule_score': schedule_score,
                }

                solved = event_models.EventUserAnswer.objects.filter(
                    event_task=event_task,
                    status=event_models.EventUserAnswer.Status.NORMAL
                )

                # 判断是不是团队赛和解出的个数
                if common.is_team_mode(event):
                    event_user_answer_params['team'] = user.team
                    user_team = user.team
                    solved_count = solved.exclude(team=user.team).count()
                else:
                    user_team = user
                    solved_count = solved.exclude(user=user).count()

                # 是不是动态积分
                if event.integral_mode == event_models.Event.IntegralMode.DYNAMIC:
                    score, dynamic_score_changed = self.handle_dynamic_score(event_task, solved_count + 1)
                    # 计算得到的动态积分的分值（总分*进度）
                    get_score = score * schedule
                else:
                    dynamic_score_changed = False

                # 计算一二三血奖励
                get_score = self.handle_blood_reward(user, event_task, user_team, get_score, dynamic_score_changed, solved_count)

                fixed_params['score'] = get_score
                event_user_answer_params['score'] = get_score

                # 把数据写进（更新）数据库中，如果有记录就更新，没有就创建记录
                if common.is_team_mode(event):
                    _pss = event_models.EventUserAnswer.objects.filter(team=user.team, event_task=event_task).first()
                else:
                    _pss = event_models.EventUserAnswer.objects.filter(user=user, event_task=event_task).first()

                _fun = self.save_submit_solved if not _pss else self.update_submit_solved
                _fun(event_user_answer_params, answer)

                self.after_handle_answer(event_user_answer_params, answer)

                logger.info(
                    'user[%s-%s] submit event_task[%s] flag success: %s, score[%s]',
                    user.id,
                    user.first_name,
                    event_task.pk,
                    answer,
                    get_score
                )

                # 整个事务完成后进行相关操作
                if fixed_params['is_solved']:
                    # 清除　EventUserAnswer　影响的缓存
                    if hasattr(self, 'answer_related_cache_class'):
                        self.clear_cls_cache(self.answer_related_cache_class)

                    # 动态分数改变了, 清除　EventTask　影响的缓存
                    if dynamic_score_changed:
                        if hasattr(self, 'task_related_cache_class'):
                            self.clear_cls_cache(self.task_related_cache_class)

                    # 一二三血发送比赛通知，清除比赛通知影响的缓存
                    if solved_count <= 2:
                        if hasattr(self, 'event_notice_related_cache_class'):
                            self.clear_cls_cache(self.event_notice_related_cache_class)

            else:
                fixed_params['is_solved'] = False
                all_scored_points, schedule_score = self.get_scored_points(event_task, user, 0)
                fixed_params['score'] = all_scored_points
            serializer.save(**fixed_params)

        return True

    # 获取最新一共得分和进度
    def get_scored_points(self, event_task, user, score):
        if common.is_team_mode(self.extra_attr.event):
            score_flag = event_models.EventUserAnswer.objects.filter(team=user.team, event_task=event_task)
        else:
            score_flag = event_models.EventUserAnswer.objects.filter(user=user, event_task=event_task)

        if score_flag.count() > 0:
            scored_points = float(score_flag.first().schedule_score)
            all_scored_points = scored_points + int(score)

            schedule_score = score_flag.first().schedule_score + int(score)

            return all_scored_points, schedule_score
        else:
            return int(score), int(score)

    # 创建记录
    def save_submit_solved(self, create_params, answer):
        create_params['answer'] = answer
        event_models.EventUserAnswer.objects.create(**create_params)

    # 更新记录
    def update_submit_solved(self, create_params, answer):
        event = self.extra_attr.event
        if common.is_team_mode(event):
            pss = event_models.EventUserAnswer.objects.filter(team=create_params['team'],
                                                              event_task=create_params["event_task"]).first()
        else:
            pss = event_models.EventUserAnswer.objects.filter(user=create_params['user'],
                                                              event_task=create_params["event_task"]).first()
        if not pss:
            return

        answer_log = pss.answer
        answer = answer_log + "|" + answer
        pss.answer = answer

        pss.score = create_params["score"]
        pss.user = create_params["user"]
        pss.last_edit_user = create_params["user"]
        pss.schedule = create_params["schedule"]
        pss.schedule_score = create_params["schedule_score"]
        if common.is_team_mode(event):
            pss.team = create_params["team"]

        pss.save()

    # 处理动态积分
    def handle_dynamic_score(self, event_task, solved_count):
        new_score, old_score = EventTaskHandler.get_current_dynamic_score(solved_count)
        if new_score != old_score:
            # 更新旧的动态分数
            for event in event_models.EventUserAnswer.objects.filter(event_task=event_task):
                update_score = event.schedule * new_score
                event.score = update_score
                event.save()

        return new_score, new_score != old_score

    # 更新一二三血, 并获取最新数据
    def handle_blood_score(self, event_task, score, blood, is_score_changed, blood_bonus_rate=None):
        if blood_bonus_rate is None:
            blood_bonus_rate = api_settings.BLOOD_BONUS_RATE

        # 更新旧的blood分数
        if is_score_changed and blood > 1:
            answers = event_models.EventUserAnswer.objects.filter(
                event_task=event_task,
            ).order_by('time')[0: 3]
            for i, answer in enumerate(answers):
                rate = blood_bonus_rate[i + 1]
                answer.score = float(answer.score) * (1 + rate)
                answer.save()

        rate = blood_bonus_rate[blood]
        new_score = score * (1 + rate)
        return new_score

    # 判断不是不已经拿过一二三血
    def inquire_blood(self, event_task, user_team):
        answers = event_models.EventUserAnswer.objects.filter(
            event_task=event_task,
        ).order_by('time')[0: 3]

        if answers:
            for i, answer in enumerate(answers):
                if user_team == answer.user:
                    return True, i + 1
                elif user_team == answer.team:
                    return True, i + 1
            else:
                return False, 0
        else:
            return False, 0

    def handle_blood_reward(self, user, event_task, user_team, get_score, dynamic_score_changed, solved_count):
        event = self.extra_attr.event
        if event.reward_mode == event_models.Event.RewardMode.BLOOD:
            # 判断是不是已经拿过一二三血
            already_submitted, rank = self.inquire_blood(event_task, user_team)

            if already_submitted:
                # 自己获得了123血, 但是分布得分又有新的提交
                get_score = self.handle_blood_score(event_task, get_score, rank, dynamic_score_changed)
            else:
                if solved_count <= 2:
                    blood = solved_count + 1

                    # 奖励分数
                    get_score = self.handle_blood_score(event_task, get_score, blood, dynamic_score_changed)

                    # 以管理员身份发送一二三血通知作为比赛通知(非题目通知)
                    admin_user = User.objects.get(pk=1)
                    task = TaskHandler.get_task(event_task.task_hash)

                    if common.is_team_mode(event):
                        who = user.team.name
                    else:
                        who = user.first_name

                    notice = api_settings.BLOOD_NOTICE_TEMPLATE[blood].format(
                        who=who,
                        task=task.title,
                    )
                    event_models.EventNotice.objects.create(
                        notice=notice,
                        event=event,
                        create_user=admin_user,
                        last_edit_user=admin_user,
                    )
                else:
                    # 单单更新动态分数 blood传0-2随便
                    self.handle_blood_score(event_task, get_score, 2, dynamic_score_changed)

        return get_score

    def after_handle_answer(self, event_user_answer_params, answer):
        pass


class EventUserAnswerViewSet(ProductMixin,
                             common_mixins.CacheModelMixin,
                             viewsets.ReadOnlyModelViewSet):
    queryset = event_models.EventUserAnswer.objects.all()
    serializer_class = mserializers.EventUserAnswerSerializer
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = ('event_task', 'time')
    ordering = ('event_task', '-time')

    def init_type_queryset(self):
        self.queryset = self.queryset.filter(event_task__event__type=self.event_type)

    def get_queryset(self):
        queryset = self.queryset

        user = self.query_data.get('user', int)
        if user is not None:
            queryset = queryset.filter(user=user)

        team = self.query_data.get('team', int)
        if team is not None:
            queryset = queryset.filter(team=team)

        event = self.query_data.get('event', int)
        if event is not None:
            queryset = queryset.filter(event_task__event=event)

        event_task = self.query_data.get('event_task', int)
        if event_task is not None:
            queryset = queryset.filter(event_task=event_task)

        queryset = queryset.filter(status=event_models.EventUserAnswer.Status.NORMAL)

        return queryset


class BaseNoticeViewSet(ProductMixin,
                        common_mixins.CacheModelMixin,
                        viewsets.ReadOnlyModelViewSet):
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = ('is_topped', 'create_time')
    ordering = ('-is_topped', '-create_time')
    unlimit_pagination = True


class EventNoticeViewSet(BaseNoticeViewSet):
    queryset = event_models.EventNotice.objects.all()
    serializer_class = mserializers.EventNoticeSerializer

    def init_type_queryset(self):
        self.queryset = self.queryset.filter(event__type=self.event_type)

    def get_queryset(self):
        queryset = self.queryset

        event = self.query_data.get('event', int)
        if event is not None:
            queryset = queryset.filter(event=event)

        return queryset


class EventTaskNoticeViewSet(BaseNoticeViewSet):
    queryset = event_models.EventTaskNotice.objects.all()
    serializer_class = mserializers.EventTaskNoticeSerializer

    def init_type_queryset(self):
        self.queryset = self.queryset.filter(event_task__event__type=self.event_type)

    def get_queryset(self):
        queryset = self.queryset

        event = self.query_data.get('event', int)
        if event is not None:
            queryset = queryset.filter(event_task__event=event)

        event_task = self.query_data.get('event_task', int)
        if event_task is not None:
            queryset = queryset.filter(event_task=event_task)

        return queryset


class EventTaskAccessLogViewSet(ProductMixin,
                                mixins.CreateModelMixin,
                                viewsets.GenericViewSet):
    queryset = event_models.EventTaskAccessLog.objects.all()
    serializer_class = mserializers.EventTaskAccessLogSerializer

    def init_type_queryset(self):
        self.queryset = self.queryset.filter(event_task__event__type=self.event_type)

    def perform_create(self, serializer):
        event_task = serializer.validated_data['event_task']
        fixed_params = {'user': self.request.user}
        if event_task.event.mode == event_models.Event.Mode.TEAM:
            fixed_params['team'] = self.request.user.team
        serializer.save(**fixed_params)
