# -*- coding: utf-8 -*-

from practice import models as practice_models


def practice_init():
    task_event_list = practice_models.TaskEvent.original_objects.exclude(creater__username__in=['admin', 'root'])
    for event in task_event_list:
        if event.logo:
            event.logo.delete()
        event.delete()

    practice_models.PracticeSubmitSolved.objects.all().delete()
