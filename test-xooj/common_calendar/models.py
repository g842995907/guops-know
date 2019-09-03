# -*-coding: utf-8 -*-

from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
from django.utils.datetime_safe import date

from common_auth.models import User, Faculty, Major, Classes, Team


class Calendar(models.Model):
    title = models.CharField(max_length=1024, default=None, null=True)
    content = models.CharField(max_length=1024, default=None, null=True)
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    is_event = models.BooleanField(default=False)

    # 日历的类型, 比如:我的收藏, 练习, 参加比赛等等
    type = models.PositiveIntegerField(default=0)
    faculty = models.ForeignKey(Faculty, null=True)
    major = models.ForeignKey(Major, null=True)
    classes = models.ForeignKey(Classes, null=True)
    team = models.ForeignKey(Team, null=True)

    url = models.URLField(max_length=1024, null=True, default=None)
    create_time = models.DateTimeField(default=timezone.now)
    show_time = models.DateField(default=date.today)

    class Meta:
        db_table = "common_calendar"

    def __unicode__(self):
        return '%s%s' % (self.title, self.content)
