# -*- coding: utf-8 -*-

all_init_function = {}


def register_init_function(appname, function_name):
    fun_name = all_init_function.get(appname)
    if fun_name is None:
        all_init_function[appname] = function_name


def init_database():
    # 场景,初始化
    common_env_init = all_init_function.get("common_env", None)
    if common_env_init is not None:
        common_env_init()

    # 解题赛,初始化
    event_jeopardy_init = all_init_function.get("event_jeopardy", None)
    if event_jeopardy_init is not None:
        event_jeopardy_init()

    # 考试,初始化
    event_exam_init = all_init_function.get("event_exam", None)
    if event_exam_init is not None:
        event_exam_init()

    # 实操练习,初始化
    practice_exercise_init = all_init_function.get("practice_exercise", None)
    if practice_exercise_init is not None:
        practice_exercise_init()

    # 人机攻防,初始化
    practice_man_machine_init = all_init_function.get("practice_man_machine", None)
    if practice_man_machine_init is not None:
        practice_man_machine_init()

    # 真实漏洞,初始化
    practice_real_vuln_init = all_init_function.get("practice_real_vuln", None)
    if practice_real_vuln_init is not None:
        practice_real_vuln_init()

    # 理论基础,初始化
    practice_theory_init = all_init_function.get("practice_theory", None)
    if practice_theory_init is not None:
        practice_theory_init()

    # 习题集初始化
    practice_init = all_init_function.get("practice", None)
    if practice_init is not None:
        practice_init()

    # 系统配置初始化
    system_configuration_init = all_init_function.get("system_configuration", None)
    if system_configuration_init is not None:
        system_configuration_init()

    # 课程初始化
    course_init = all_init_function.get("course", None)
    if course_init is not None:
        course_init()

    # 日历初始化
    calendar_init = all_init_function.get("calendar", None)
    if calendar_init is not None:
        calendar_init()

    # 用户初始化
    x_person_init = all_init_function.get("x_person", None)
    if x_person_init is not None:
        x_person_init()
