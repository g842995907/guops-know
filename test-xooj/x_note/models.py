# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.utils.html import strip_tags

from common_auth.models import User
from common_framework.utils.constant import Status


class Note(models.Model):
    content = models.TextField()
    user = models.ForeignKey(User)
    resource = models.CharField(max_length=64)
    public = models.BooleanField(default=True)
    status = models.PositiveIntegerField(default=Status.NORMAL)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)
    score = models.FloatField(default=0)

    ispass = models.BooleanField(default=False)
    markcomment = models.CharField(max_length=2048, null=True, blank=True)
    teacher = models.ForeignKey(User, related_name='teacher_user', null=True,
                                on_delete=models.SET_NULL)

    class Meta:
        db_table = 'xnote_note'

    def __unicode__(self):
        return '%s' % self.content

    def username(self):
        return self.user.username

    def resource_name(self):
        return self.resource

    def content_abstract(self):
        abstract_str = strip_tags(self.content)
        if len(abstract_str) > 32:
            return "{} ...".format(abstract_str[:32])
        return abstract_str


class RecordLoads(models.Model):
    """
    加载记录
    """
    slug = models.CharField(max_length=100, unique=True)
    status = models.BooleanField(default=False)  # 成功True
    info = models.CharField(max_length=500, null=True, blank=True)
    create_time = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User)
    errorinfo = models.TextField(default='')

    def __unicode__(self):
        return '%s' % self.slug