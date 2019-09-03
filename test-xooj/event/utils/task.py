# -*- coding: utf-8 -*-
from django.utils import six

from common_framework.utils.cache import CacheProduct
from practice import api as practice_api

from event import models as event_models
from event.setting import api_settings


class TaskHandler(object):
    def __init__(self, task):
        if isinstance(task, (six.string_types, six.text_type)):
            self.task = self.get_task(task)
        else:
            self.task = task

        if not self.task:
            raise Exception('task does not exists')

    def validate_answer(self, user, answer, team=None):
        is_solved, allscore, specific_score = practice_api.validate_answer(self.task.hash, answer, user, team)
        return is_solved, allscore, specific_score

    def score_answer(self, answer):
        return 10

    @staticmethod
    def get_task(task_hash):
        cache = CacheProduct("get_task")
        task = cache.get(task_hash)
        if task:
            return task

        task = practice_api.get_task_object(task_hash)
        if task:
            cache.set(task_hash, task, 300)

        return task

    @staticmethod
    def get_task_info(task_hash, backend=False):
        return practice_api.get_task_info(task_hash, backend)

    @staticmethod
    def get_tasks(task_hashs):
        return practice_api.get_task_list_by_hashlist(task_hashs)

    @staticmethod
    def copy_tasks(task_hashs):
        return practice_api.copy_task_by_hash(task_hashs)

    @staticmethod
    def handle_tasks(task_hashs):
        return TaskHandler.copy_tasks(task_hashs)

    @staticmethod
    def get_type_by_hash(taskhash):
        try:
            p_type = int(taskhash.split('.')[-1])
        except:
            return None
        return p_type


class EventTaskHandler(object):
    @staticmethod
    def get_current_dynamic_score(solved_count, dynamic_score_list=None):
        if dynamic_score_list is None:
            dynamic_score_list = api_settings.DYNAMIC_SOCRE

        if solved_count <= 1:
            score_index = 0
        else:
            score_index = min(len(dynamic_score_list) - 1, solved_count - 1)
        current_score = dynamic_score_list[score_index]
        old_score = dynamic_score_list[score_index - 1] if score_index > 0 else current_score

        return current_score, old_score

    @staticmethod
    def get_task_current_dynamic_score(event_task):
        solved_count = event_models.EventUserAnswer.objects.filter(
            event_task=event_task,
            status=event_models.EventUserAnswer.Status.NORMAL
        ).count()
        return EventTaskHandler.get_current_dynamic_score(solved_count)
