# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

from common_auth.models import User
from common_framework.models import ShowLock

from practice import base_models
from practice_exercise import resource


# Create your models here.
class PracticeExerciseCategory(base_models.TaskCategory):
    class Meta:
        db_table = 'practice_exercise_category'


class PracticeExerciseTask(base_models.SolvedBaseTask, ShowLock):
    category = models.ForeignKey(PracticeExerciseCategory, on_delete=models.PROTECT)
    create_user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='exercise_task_create_user', null=True,
                                    default=None)
    last_edit_user = models.ForeignKey(User, default=None, on_delete=models.SET_NULL, null=True,
                                       related_name='exercise_task_last_edit_user')

    ResourceMeta = resource.PracticeExerciseTaskMeta