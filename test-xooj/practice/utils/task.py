# -*- coding: utf-8 -*-
import uuid

from practice.widgets.env.handlers import EnvHandler
from practice.models import PracticeSubmitSolved

DELIMITER = '|'


def get_submit_score(ptype, task, answer, user=None, team=None):
    # 动态环境的flag的验证
    correct = False
    allScore = get_contest_all_score(task)

    if task.is_dynamic_env:
        env_handler = EnvHandler(user, team=team)    #动态环境的flag
        flags = env_handler.get_all_recent_flags(task, flag=answer)  #获取所有flag
        if answer in flags or unicode(answer) in flags:
            correct = True
    else:
        flags = answer_syntax_parser(task.answer)
        if unicode(answer) in flags or answer in flags:
            correct = True

    if correct:
        specific_score = get_solved_score(answer, task, flags)
        return True, allScore, specific_score

    return False, allScore, 0


def get_choice_score(task, answer, is_first_try):       #单选题的判断方法
    correct_answer = set(answer_syntax_parser(task.answer))
    answer = set(answer_syntax_parser(answer))
    if answer == correct_answer:
        if is_first_try:
            return True, task.score, 0
        else:
            return True, 0, 0

    return False, 0, 0


def answer_syntax_parser(answer):
    if answer is None:
        return []
    return answer.split(DELIMITER)


# 判断当前这道题的分数
def get_solved_score(solved, task, flags):
    if task.solving_mode:
        flag_position = flags.index(solved)
        flags_length = task.score_multiple.split(DELIMITER)

        if flags_length >= flag_position:
            specific_score = task.score_multiple.split(DELIMITER)[flag_position]
            return specific_score
    else:
        return task.score


def get_contest_all_score(task):
    if task.solving_mode:
        task_flag_score = answer_syntax_parser(task.score_multiple)
        allScore = reduce(lambda x, y: int(x) + int(y), task_flag_score)
    else:
        allScore = task.score
    return int(allScore)


def generate_task_hash(type=0):
    taskhash = '{uuidstr}.{type}'.format(uuidstr=str(uuid.uuid4()), type=type)
    return taskhash


def get_type_by_hash(taskhash):
    try:
        p_type = int(taskhash.split('.')[-1])
    except:
        return None
    return p_type


def non_choice_answer(task, user=None):
    if task.is_dynamic_env:
        env_handler = EnvHandler(user,)
        answer = env_handler.get_all_recent_flags(task, recent_one=True)
    else:
        answer = set(answer_syntax_parser(task.answer))
    return answer

def choice_answer(task):
    return set(answer_syntax_parser(task.answer))