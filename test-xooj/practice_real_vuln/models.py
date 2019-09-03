# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from common_auth.models import User
from common_framework.models import ShowLock

from practice import base_models
from practice_real_vuln import resource


# Create your models here.

class RealVulnCategory(base_models.TaskCategory):
    class Meta:
        db_table = 'practice_real_vuln_category'


class RealVulnTask(base_models.SolvedBaseTask, ShowLock):
    category = models.ForeignKey(RealVulnCategory, on_delete=models.PROTECT)
    identifier = models.CharField(max_length=100, null=True, default=None)
    create_user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='real_vuln_task_create_user',
                                    null=True, default=None)
    last_edit_user = models.ForeignKey(User, default=None, on_delete=models.SET_NULL, null=True,
                                       related_name='real_vuln_task_last_edit_user')

    ResourceMeta = resource.RealVulnTaskMeta