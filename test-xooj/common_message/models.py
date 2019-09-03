from __future__ import unicode_literals

from django.db import models
from django.utils import timezone

from common_auth.models import User

class Message(models.Model):
    title = models.CharField(max_length=1024, default=None, null=True)
    content = models.CharField(max_length=1024, default=None, null=True)
    message_type = models.PositiveIntegerField(default=0)
    create_time = models.DateTimeField(default=timezone.now) 
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    read = models.BooleanField(default=False)
    url = models.URLField(max_length=1024, null=True)

    class Meta:
        db_table = "common_message"

    def __unicode__(self):
        return '%s' % self.content
