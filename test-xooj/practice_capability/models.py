# -*- coding: utf-8 -*-
import uuid

from django.db import models
from django.utils import timezone

from common_auth.models import User
from common_framework.models import BaseShare
from common_framework.utils.enum import enum

from practice import api


def testpaper_hash():
    return "{}.exam".format(uuid.uuid4())


class TestPaper(BaseShare):
    name = models.CharField(max_length=50, unique=True)
    hash = models.CharField(max_length=100, null=True, default=testpaper_hash)
    # task_ids = modddels.CharField(max_length=1024, default=None, null=True)
    # task_scores = models.CharField(max_length=1024, default=None, null=True)
    task_number = models.PositiveIntegerField(default=0)
    task_all_score = models.FloatField(default=0)
    create_time = models.DateTimeField(default=timezone.now)
    create_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='test_paper_create_user')
    logo = models.FileField(upload_to='testpaper/logo', null=True, default=None)
    introduction = models.CharField(max_length=1024, default=None, null=True)

    Status = enum(
        DELETE=0,
        NORMAL=1,
    )
    status = models.PositiveIntegerField(default=Status.NORMAL)

    public = models.BooleanField(default=False)


class TestPaperTask(models.Model):
    test_paper = models.ForeignKey(TestPaper, on_delete=models.PROTECT)
    task_hash = models.CharField(max_length=500)
    score = models.FloatField()


class TestPaperRecord(models.Model):
    test_paper = models.ForeignKey(TestPaper, on_delete=models.PROTECT)
    score = models.FloatField(default=0)
    task_hash = models.CharField(max_length=500)
    answer = models.CharField(max_length=500)
    solved = models.BooleanField(default=False)
    create_time = models.DateTimeField(default=timezone.now)
    submit_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
