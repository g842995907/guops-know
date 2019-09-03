# -*- coding: utf-8 -*-

from practice_exercise import models as exercise_models


def practice_exercise_init():
    task_list = exercise_models.PracticeExerciseTask.original_objects.exclude(
        create_user__username__in=['admin', 'root'])
    for task in task_list:
        if task.file:
            task.file.delete()
        task.delete()
    #exercise_models.PracticeExerciseCategory.objects.all().delete()
