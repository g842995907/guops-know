# -*- coding: utf-8 -*-

from practice_theory import models as theory_models


def practice_theory_init():
    theory_models.ChoiceTask.original_objects.exclude(create_user__username__in=['admin', 'root']).delete()
