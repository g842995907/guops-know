# -*- coding: utf-8 -*-
from django.core.cache import cache
from django.utils import timezone
from rest_framework import response, status

from practice import constant
from practice.api import Practice, PRACTICE_TYPE_THEORY
from practice.utils.task import generate_task_hash
from practice_theory.models import ChoiceTask, ChoiceCategory
from practice_theory.web import serializers as webSerializers
from practice_theory.cms import serializers as cmsSerializers

DELIMITER = '|'

def answer_syntax_parser(answer):
    return answer.split(DELIMITER)


class TheoryPractice(Practice):
    serializer_class = webSerializers.ChoiceTaskSerializer
    queryset = ChoiceTask.objects.filter(is_copy=False, event__public=True).order_by('-id')
    cms_serializer = cmsSerializers.ChoiceTaskSerializer
    web_serializer = webSerializers.ChoiceTaskSerializer
    task_class = ChoiceTask
    task_category = ChoiceCategory
    category_web_serializer = webSerializers.ChoiceCategorySerializer
    category_cms_serializer = cmsSerializers.ChoiceCategorySerializer

    def copy_task(self, taskhash):
        try:
            new_task = ChoiceTask.objects.get(hash=taskhash)
        except:
            return None

        new_task.pk = None
        new_task.is_copy = True
        new_task.hash = generate_task_hash(type=PRACTICE_TYPE_THEORY)
        new_task.save()
        return new_task.hash

    def get_choice_score(self, task, answer):
        correct_answer = set(answer_syntax_parser(task.answer))
        answer = set(answer_syntax_parser(answer))
        if answer == correct_answer:
            return True, task.score, 0

        return False, 0, 0

    def commit_task_answer(self, p_type, task, user, answer):
        if None == p_type or not task or not user or not answer:
            return

        # 已经答对过
        _record = self.get_solved_record(user, task.hash)
        if _record.count() > 0:
            return

        # 写入答题记录
        self.save_submit_log(user, task.hash, answer, p_type)

        # 判断得分
        _solved, score, w_score = self.get_choice_score(task, answer)

        if _solved:
            # 答对了
            cache.clear()
            self.save_submit_solved(user, task.hash, answer, p_type, score, w_score)

        return {'is_solved':_solved, 'score':score}





