# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _

import api as practice_api


# 获取特定类型的题目
def _get_task_list(type, event=None, category=None, difficult=None, task_name=None, public=None, **kwargs):
    instance = practice_api.practice_instance.get(int(type))
    if instance and isinstance(instance, practice_api.Practice):
        tasks = instance.get_task_list(event, category, difficult, task_name, public, **kwargs)
        return tasks

    return None


# 获取特定类型的记录
def _get_task_log_list(p_type, major, classes, days):
    instance = practice_api.practice_instance.get(p_type)
    if instance and isinstance(instance, practice_api.Practice):
        tasklogs = instance.get_task_log_list(major, classes, days)
        return tasklogs

    return None


# 获取特定类型练习的排行
def _get_event_rank(p_type, event, classes, major):
    instance = practice_api.practice_instance.get(p_type)
    if instance and isinstance(instance, practice_api.Practice):
        tasklogs = instance.get_event_rank_list(event, classes, major)
        return tasklogs

    return None


# 提交特定类型的答题记录
def _commit_task_answer(p_type, task, user, answer):
    instance = practice_api.practice_instance.get(int(p_type))
    if instance and isinstance(instance, practice_api.Practice):
        _ret = instance.commit_task_answer(p_type, task, user, answer)
        return _ret

    return None


# 根据类型获取序列化函数
def _get_task_serializer(p_type):
    instance = practice_api.practice_instance.get(int(p_type))
    if instance and isinstance(instance, practice_api.Practice):
        task_serializer = instance.get_task_serializer()
        return task_serializer

    return None


# 获取具体题目
def _get_task_detail(p_type, taskhash, backend=False):
    instance = practice_api.practice_instance.get(int(p_type))
    if instance and isinstance(instance, practice_api.Practice):
        task_detail = instance.get_task_detail(taskhash, backend)
        return task_detail

    return None


# 获取具体题目对象
def _get_task_object(p_type, taskhash):
    instance = practice_api.practice_instance.get(int(p_type))
    if instance and isinstance(instance, practice_api.Practice):
        task_detail = instance.get_task_object(taskhash)
        return task_detail

    return None


# 根据hash列表获取题目列表
def _get_tash_by_hashlist(p_type, hashlist):
    instance = practice_api.practice_instance.get(int(p_type))
    if instance and isinstance(instance, practice_api.Practice):
        task_list = instance.get_task_by_hashlist(hashlist)
        return task_list

    return None


# 获取某个类型的答题记录
def _get_record_by_type(user, p_type, is_solved):
    instance = practice_api.practice_instance.get(int(p_type))
    if instance and isinstance(instance, practice_api.Practice):
        record_list = instance.get_record_by_person(user, is_solved, p_type)
        return record_list

    return None


# 获取某道题的答题记录
def _get_record_by_taskhash(user, p_type, taskhash):
    instance = practice_api.practice_instance.get(int(p_type))
    if instance and isinstance(instance, practice_api.Practice):
        record_detail = instance.get_record_detail(user, taskhash)
        return record_detail

    return None


# 拷贝某道题
def _copy_task(p_type, task_hash):
    instance = practice_api.practice_instance.get(int(p_type))
    if instance and isinstance(instance, practice_api.Practice):
        record_detail = instance.copy_task(task_hash)
        return record_detail

    return None


def _get_task_category(p_type, backend=False, **kwargs):
    instance = practice_api.practice_instance.get(int(p_type))
    if instance and isinstance(instance, practice_api.Practice):
        category_list = instance.get_task_category(backend, **kwargs)
        return category_list

    return None


# 根据类型名称获取类型
def _get_task_category_by_name(p_type, name):
    instance = practice_api.practice_instance.get(int(p_type))
    if instance and isinstance(instance, practice_api.Practice):
        category = instance.get_task_category_by_name(name)
        return category

    return None


# 根据习题集获取hash
def _get_task_hash_list(p_type, event):
    instance = practice_api.practice_instance.get(int(p_type))
    if instance and isinstance(instance, practice_api.Practice):
        hashlist = instance.get_hash_list(event)
        return hashlist

    return None


# 获取中文类型
def _get_ch_type(p_type):
    switcher = {
        0: _("x_theory"),
        1: _("x_real_vuln"),
        2: _("x_exercise"),
        3: _("x_man_machine"),
        4: _("x_ad_mode"),
        5: _("x_infiltration"),
    }
    return switcher.get(p_type, "nothing")
