# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils import timezone

from common_auth.models import User, Team, Classes
from common_framework.models import AuthAndShare
from common_framework.utils.enum import enum
from common_framework.utils.models.manager import MyManager

from practice import api
import uuid
from event.utils.token import generate_signup_token, generate_random_password


def tool_hash():
    return "{}.event".format(uuid.uuid4())


class Event(AuthAndShare):
    name = models.CharField(max_length=500)
    logo = models.ImageField(upload_to='event_logo', null=True, default=None)
    description = models.TextField(default='')
    rule = models.TextField(default='')

    hash = models.CharField(max_length=100, null=True, default=tool_hash)

    # 比赛进程
    Process = enum(
        INPROGRESS=0,
        COMING=1,
        OVER=2,
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    public = models.BooleanField(default=True)
    public_rank = models.BooleanField(default=True)
    public_all_rank = models.BooleanField(default=True)
    public_token = models.BooleanField(default=False)
    can_submit_writeup = models.BooleanField(default=False)

    # 比赛类型
    Type = enum(
        EXAM=1,
        JEOPARDY=2,
        SHARE=3,
        TRIAL=4,
        ATTACK_DEFENSE=5,
        INFILTRATION=6,
    )
    type = models.PositiveIntegerField()

    # 参赛方式
    Mode = enum(
        PERSONAL=1,
        TEAM=2,
    )

    mode = models.PositiveIntegerField(default=Mode.PERSONAL)

    # 积分方式
    IntegralMode = enum(
        EMPTY=0,
        CUMULATIVE=1,
        DYNAMIC=2,
    )
    integral_mode = models.PositiveIntegerField(default=IntegralMode.EMPTY)

    # 奖励方式
    RewardMode = enum(
        EMPTY=0,
        BLOOD=1,
    )
    reward_mode = models.PositiveIntegerField(default=RewardMode.EMPTY)

    # 比赛状态
    Status = enum(
        DELETE=0,
        NORMAL=1,
        PAUSE=2,
        INPROGRESS=3,
        OVER=4,
    )
    status = models.PositiveIntegerField(default=Status.NORMAL)  # 正在进行

    create_time = models.DateTimeField(default=timezone.now)
    create_user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='event_create_user')
    last_edit_time = models.DateTimeField(default=timezone.now)
    last_edit_user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='event_last_edit_user')


    objects = MyManager({'status': Status.DELETE})
    original_objects = models.Manager()

    def __unicode__(self):
        return '%s' % self.name


class BaseEventSignup(models.Model):
    event = models.ForeignKey(Event, on_delete=models.PROTECT)
    time = models.DateTimeField(default=timezone.now)
    token = models.CharField(max_length=33, default=generate_signup_token)

    # 报名状态
    Status = enum(
        DELETE=0,
        SIGNUPED=1,
        FORBIDDEN=2,
    )
    status = models.PositiveIntegerField(default=Status.SIGNUPED)
    last_edit_time = models.DateTimeField(default=timezone.now)

    objects = MyManager({'status': Status.DELETE})
    original_objects = models.Manager()

    init_score = models.PositiveIntegerField(default=2000)
    file = models.BinaryField(null=True, default=None)

    # 随机密码，攻防赛用到
    rand_password = models.CharField(max_length=33, default=generate_random_password)

    class Meta:
        abstract = True


class EventSignupUser(BaseEventSignup):
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='event_signup_user')
    last_edit_user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='event_signup_user_last_edit_user')


class EventSignupTeam(BaseEventSignup):
    team = models.ForeignKey(Team, on_delete=models.PROTECT)
    last_edit_user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='event_signup_team_last_edit_user')


class EventTask(models.Model):
    event = models.ForeignKey(Event, on_delete=models.PROTECT)
    seq = models.IntegerField()
    task_hash = models.CharField(max_length=500)
    task_score = models.FloatField(default=0)
    public = models.BooleanField(default=True)
    public_time = models.DateTimeField(default=None, null=True)

    # 题目类型
    Type = enum(
        THEORY=api.PRACTICE_TYPE_THEORY,
        REAL_VULN=api.PRACTICE_TYPE_REAL_VULN,
        EXCRISE=api.PRACTICE_TYPE_EXCRISE,
        MAN_MACHINE=api.PRACTICE_TYPE_MAN_MACHINE,
        ATTACK_DEFENSE=api.PRACTICE_TYPE_ATTACK_DEFENSE,
        WLAN=250,
    )
    type = models.PositiveIntegerField()

    # 题目状态
    Status = enum(
        DELETE=0,
        NORMAL=1,
        CLOSE=2,
    )
    status = models.PositiveIntegerField(default=Status.NORMAL)

    objects = MyManager({'status': Status.DELETE})
    original_objects = models.Manager()


class EventWriteup(models.Model):
    event = models.ForeignKey(Event, on_delete=models.PROTECT)
    writeup = models.FileField(upload_to='event_writeup', null=True, default=None)
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='event_writeup_user')
    team = models.ForeignKey(Team, on_delete=models.PROTECT, null=True, default=None)
    time = models.DateTimeField(default=timezone.now)

    # Writeup状态
    Status = enum(
        DELETE=0,
        NORMAL=1,
    )
    status = models.PositiveIntegerField(default=Status.NORMAL)

    objects = MyManager({'status': Status.DELETE})
    original_objects = models.Manager()


class EventUserSubmitLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    team = models.ForeignKey(Team, on_delete=models.PROTECT, null=True, default=None)
    event_task = models.ForeignKey(EventTask, on_delete=models.PROTECT)
    answer = models.TextField()
    score = models.FloatField(default=0)
    is_solved = models.BooleanField(default=False)
    time = models.DateTimeField(default=timezone.now)
    submit_ip = models.CharField(max_length=30, null=True)


class EventUserAnswer(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='event_user_answer_user')
    team = models.ForeignKey(Team, on_delete=models.PROTECT, null=True, default=None)
    event_task = models.ForeignKey(EventTask, on_delete=models.PROTECT)
    answer = models.TextField()
    score = models.DecimalField(default=0, max_digits=12, decimal_places=4)
    time = models.DateTimeField(default=timezone.now)

    # 进度
    schedule = models.FloatField(default=0)
    schedule_score = models.IntegerField(default=0)

    # 答题状态
    Status = enum(
        NORMAL=1,
        CHEAT=2,
    )
    status = models.PositiveIntegerField(default=Status.NORMAL)
    last_edit_time = models.DateTimeField(default=timezone.now)
    last_edit_user = models.ForeignKey(User, null=True, on_delete=models.PROTECT,
                                       related_name='event_user_answer_last_edit_user')

    class Meta:
        unique_together = ('user', 'team', 'event_task')


class BaseNotice(models.Model):
    notice = models.CharField(max_length=1024)
    is_topped = models.BooleanField(default=False)
    create_time = models.DateTimeField(default=timezone.now)
    last_edit_time = models.DateTimeField(default=timezone.now)

    # 通知状态
    Status = enum(
        DELETE=0,
        NORMAL=1,
    )
    status = models.PositiveIntegerField(default=Status.NORMAL)

    objects = MyManager({'status': Status.DELETE})
    original_objects = models.Manager()

    class Meta:
        abstract = True


class EventNotice(BaseNotice):
    event = models.ForeignKey(Event, on_delete=models.PROTECT)
    create_user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='event_notice_create_user')
    last_edit_user = models.ForeignKey(User, null=True, on_delete=models.PROTECT,
                                       related_name='event_notice_last_edit_user')


class EventTaskNotice(BaseNotice):
    event_task = models.ForeignKey(EventTask, on_delete=models.CASCADE)
    create_user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='event_task_notice_create_user')
    last_edit_user = models.ForeignKey(User, null=True, on_delete=models.PROTECT,
                                       related_name='event_task_notice_last_edit_user')


class EventTaskAccessLog(models.Model):
    event_task = models.ForeignKey(EventTask, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    team = models.ForeignKey(Team, on_delete=models.PROTECT, null=True, default=None)
    time = models.DateTimeField(default=timezone.now)


class EventScoreReward(models.Model):
    event = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True)
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    reward_score = models.IntegerField(default=0)
    create_time = models.DateTimeField(default=timezone.now)
