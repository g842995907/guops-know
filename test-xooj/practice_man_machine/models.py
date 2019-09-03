# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.
from common_auth.models import User

from practice import base_models
from practice_man_machine import resource


class ManMachineCategory(base_models.TaskCategory):
    class Meta:
        db_table = 'practice_man_manchine_category'


class ManMachineTask(base_models.SolvedBaseTask):
    at_check_script = models.CharField(max_length=350, null=True, default=None)
    at_attack_script = models.CharField(max_length=350, null=True, default=None)
    category = models.ForeignKey(ManMachineCategory, on_delete=models.PROTECT)
    create_user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='man_machine_task_create_user',
                                    null=True, default=None)
    last_edit_user = models.ForeignKey(User, default=None, on_delete=models.SET_NULL, null=True,
                                       related_name='man_machine_task_last_edit_user')

    ResourceMeta = resource.ManMachineTaskMeta