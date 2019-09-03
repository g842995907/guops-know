# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from common_auth.models import User
from common_framework.models import ShowLock

from practice import base_models
from practice_attack_defense import resource


# Create your models here.
class PracticeAttackDefenseCategory(base_models.TaskCategory):
    class Meta:
        db_table = 'practice_attack_defense_category'


class PracticeAttackDefenseTask(base_models.SolvedBaseTask, ShowLock):
    category = models.ForeignKey(PracticeAttackDefenseCategory, on_delete=models.PROTECT)
    create_user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='attack_defense_task_create_user', null=True,
                                    default=None)
    last_edit_user = models.ForeignKey(User, default=None, on_delete=models.SET_NULL, null=True,
                                       related_name='attack_defense_task_last_edit_user')

    ResourceMeta = resource.PracticeAttackDefenseTaskMeta