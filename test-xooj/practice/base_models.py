# -*- coding: utf-8 -*-
from django.db import models
from django.utils import timezone

from common_auth.models import User
from common_env.models import Env
from common_framework.models import Builtin
from common_framework.utils.enum import enum
from common_framework.utils.models.manager import MyManager
from common_resource.base.model import Resource

from practice import resource
from practice.constant import TaskStatus, Difficulty, CategoryStatus
from practice.models import TaskEvent



class BaseTask(Resource, Builtin):
    title = models.CharField(max_length=100, default='')
    event = models.ForeignKey(TaskEvent, on_delete=models.SET_NULL, null=True)
    content = models.TextField(default=None, null=True)
    answer = models.CharField(max_length=1024, null=True)
    score = models.PositiveIntegerField(default=0)
    public = models.BooleanField()
    last_edit_time = models.DateTimeField(default=timezone.now)
    status = models.PositiveIntegerField(default=TaskStatus.NORMAL)
    hash = models.CharField(max_length=100, null=True)
    is_copy = models.BooleanField(default=False)
    objects = MyManager({'status': TaskStatus.DELETE})
    original_objects = models.Manager()
    knowledges = models.CharField(max_length=1024, null=True)

    class Meta:
        abstract = True

    class MyMeta:
        _builtin_modify_field = ['public', 'id', 'is_copy', 'hash', 'status', 'last_edit_time']

    ResourceMeta = resource.BaseTaskMeta

    def __unicode__(self):
        return '%s' % self.title


class TaskEnv(Resource, models.Model):
    env = models.ForeignKey(Env, on_delete=models.SET_NULL, null=True, default=None)
    Type = enum(
        SHARED=0,
        PRIVATE=1
    )
    type = models.IntegerField(default=Type.PRIVATE)
    is_dynamic_flag = models.BooleanField(default=False)
    flag_count = models.PositiveIntegerField(default=1)
    flags = models.TextField(default='[]')
    flag_servers = models.TextField(default='[]')
    destroy_delay = models.IntegerField(default=2)
    destroy_time = models.DateTimeField(default=None, null=True)
    # 正在共享的用户
    shared_users = models.ManyToManyField(User)

    ResourceMeta = resource.TaskEnvMeta


class SolvedBaseTask(BaseTask):
    file = models.FileField(upload_to='task', null=True, max_length=500)
    url = models.URLField(max_length=1024, null=True)
    official_writeup = models.TextField(null=True)
    public_official_writeup = models.BooleanField(default=False)
    difficulty_rating = models.PositiveIntegerField(default=Difficulty.INTRUDCTION)
    markdown = models.TextField(null=True, blank=True)

    is_dynamic_env = models.BooleanField(default=False)
    envs = models.ManyToManyField(TaskEnv)

    solving_mode = models.BooleanField(default=False)
    score_multiple = models.CharField(max_length=1024, null=True)
    flag_servers = models.CharField(max_length=1024, null=True)

    class Meta:
        abstract = True


class BaseSubmitLog(models.Model):
    submit_user = models.ForeignKey(User, on_delete=models.CASCADE)
    submit_time = models.DateTimeField(default=timezone.now)
    submit_answer = models.CharField(max_length=500, null=True)
    score = models.PositiveIntegerField(default=0)
    weight_score = models.FloatField(default=0)
    is_solved = models.BooleanField(db_index=True, default=False)

    class Meta:
        abstract = True


class BaseSubmitSolved(models.Model):
    submit_user = models.ForeignKey(User, on_delete=models.CASCADE)
    submit_time = models.DateTimeField(default=timezone.now)
    score = models.PositiveIntegerField(default=0)
    weight_score = models.FloatField(default=0)

    class Meta:
        abstract = True


class TaskCategory(Resource, models.Model):
    cn_name = models.CharField(max_length=255)
    en_name = models.CharField(max_length=255)

    status = models.PositiveIntegerField(default=CategoryStatus.NORMAL)

    objects = MyManager({'status': TaskStatus.DELETE})
    original_objects = models.Manager()

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.cn_name

    ResourceMeta = resource.TaskCategoryMeta