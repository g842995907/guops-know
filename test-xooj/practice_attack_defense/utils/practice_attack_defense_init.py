# -*- coding: utf-8 -*-

from practice_attack_defense import models as attack_defense_models


def practice_attack_defense_init():
    task_list = attack_defense_models.PracticeAttackDefenseTask.original_objects.exclude(
        create_user__username__in=['admin', 'root'])
    for task in task_list:
        if task.file:
            task.file.delete()
        task.delete()
