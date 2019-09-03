# -*- coding: utf-8 -*-

from practice_infiltration import models as infiltration_models


def practice_infiltration_init():
    task_list = infiltration_models.PracticeInfiltrationTask.original_objects.exclude(
        create_user__username__in=['admin', 'root'])
    for task in task_list:
        if task.file:
            task.file.delete()
        task.delete()
    #infiltration_models.PracticeInfiltrationCategory.objects.all().delete()
