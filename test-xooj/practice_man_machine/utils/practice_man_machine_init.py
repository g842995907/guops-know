# -*- coding: utf-8 -*-

from practice_man_machine import models as man_machine_models


def practice_man_machine_init():
    task_list = man_machine_models.ManMachineTask.original_objects.exclude(create_user__username__in=['admin', 'root'])
    for task in task_list:
        if task.file:
            task.file.delete()
        task.delete()
    #man_machine_models.ManMachineTask.objects.all().delete()
