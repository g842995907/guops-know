#coding: utf-8
from __future__ import unicode_literals

from django.db import models
from event.models import Event, EventTask
from common_auth.models import User
from django.utils import timezone


# Create your models here.
class extendEvent(models.Model):
    event = models.OneToOneField(Event, primary_key=True)
    ans_display_method = models.IntegerField(default=0)

    # 显示成绩 排名状态
    score_status = models.BooleanField(default=False)
    rank_status = models.BooleanField(default=False)
    capabili_name = models.CharField(max_length=50, blank=True, null=True)


class ExamUserState(models.Model):
    event = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    create_time = models.DateTimeField(default=timezone.now)


class SubmitFlags(models.Model):
    event = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    topic_hash = models.CharField(max_length=500,default=None,null=True)
    score = models.DecimalField(default=0, max_digits=12, decimal_places=4)


class SubmitRecord(models.Model):
    event = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    score = models.DecimalField(default=0, max_digits=12, decimal_places=4)
    answer = models.CharField(default=None, null=True, max_length=4096)
    # correct_rate = models.DecimalField(default=0, max_digits=12, decimal_places=4)
    submit_time = models.DateTimeField(default=timezone.now)


class SolvedRecord(models.Model):
    event = models.ForeignKey(Event, on_delete=models.SET_NULL, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    solved_time = models.DateTimeField(default=timezone.now)
