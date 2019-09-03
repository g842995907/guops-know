from __future__ import unicode_literals

from django.db import models

from common_auth.models import User
from practice import base_models
from practice_theory import resource
from common_framework.utils.enum import  enum


class ChoiceCategory(base_models.TaskCategory):
    class Meta:
        db_table = 'practice_theory_category'


class ChoiceTask(base_models.BaseTask):
    TopicProblem = enum(
        SINGLE=0,
        MULTIPLE=1,
        JUDGMENT=2,
    )
    Difficulty = enum(
        INTRUDCTION=0,
        INCREASE=1,
        EXPERT=2
    )
    multiple = models.PositiveIntegerField(default=TopicProblem.SINGLE)
    option = models.TextField(null=True)
    category = models.ForeignKey(ChoiceCategory, on_delete=models.PROTECT)
    create_user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='choice_task_create_user', null=True,
                                    default=None)
    last_edit_user = models.ForeignKey(User, default=None, on_delete=models.SET_NULL, null=True,
                                       related_name='choice_task_last_edit_user')
    difficulty_rating = models.PositiveIntegerField(default=Difficulty.INTRUDCTION)

    ResourceMeta = resource.ChoiceTaskMeta

    def __unicode__(self):
        return '%s' % self.content[:15]
