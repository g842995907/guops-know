from __future__ import unicode_literals

from django.db import models

from common_framework.utils.constant import Status


class AbstractComment(models.Model):
    parent = models.ForeignKey('self', blank=True, null=True, default=None, related_name='child')

    class Meta:
        abstract = True


class Comment(AbstractComment):
    tenant = models.CharField(max_length=64, blank=True, null=True)
    username = models.CharField(max_length=64)
    nickname = models.CharField(max_length=64, blank=True, null=True)
    avatar = models.CharField(max_length=255, blank=True, null=True)
    resource = models.CharField(max_length=64)
    theme_name = models.CharField(max_length=64, null=True, blank=True)
    comment = models.TextField()
    source_ip = models.CharField(max_length=16, blank=True, null=True)
    thumbs_up = models.IntegerField(default=0)
    public = models.BooleanField(default=True)
    status = models.PositiveIntegerField(default=Status.NORMAL)
    create_time = models.DateTimeField(auto_now_add=True)
    update_time = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'x_comment'
        ordering = ["-create_time"]

    def __unicode__(self):
        return self.comment

    def comment_username(self):
        return self.nickname or self.username

class NewLikes(models.Model):
    comment = models.ForeignKey("Comment",related_name='likes')
    username=models.CharField(max_length=64, blank=True, null=True)
    username_id = models.IntegerField(default=0)
    resource = models.CharField(max_length=64)
    create_time = models.DateTimeField(auto_now_add=True)
    updata_time =models.DateTimeField(auto_now=True)
    status = models.PositiveIntegerField(default=Status.NORMAL)

    class Meta:
        db_table = 'x_comment_new_likes'
        ordering = ["-create_time"]

    def __unicode__(self):
        return self.username