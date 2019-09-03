# -*- coding: utf-8 -*-

from django.utils.translation import ugettext_lazy as _

COURSE_MODULE_ID = 0x1000

PRACTICE_MODULE_ID = 0x2000
PRACTICE_THEORY_MODULE_ID = 0x2001
PRACTICE_REAL_VULN_MODULE_ID = 0x2002
PRACTICE_EXERCISE_MODULE_ID = 0x2003
PRACTICE_INFILTRATION_MODULE_ID = 0x2004

EVENT_EXAM = 0x3001
EVENT_JEOPARDY = 0X3002
EVENT_ATTACK_DEFENSE = 0X3003
EVENT_TRIAL = 0X3004
EVENT_INFILTRATION = 0X3005

SYSTEM = 0x4000


_module_list = {
    'course': {'id': COURSE_MODULE_ID, 'name': _('x_course')},
    'practice': {'id': PRACTICE_MODULE_ID, 'name': _('x_practice')},
    'practice_theory': {'id': PRACTICE_THEORY_MODULE_ID, 'name': _('x_theory')},
    'practice_real_vuln': {'id': PRACTICE_REAL_VULN_MODULE_ID, 'name': _('x_real_vuln')},
    'practice_exercise': {'id': PRACTICE_EXERCISE_MODULE_ID, 'name': _('x_exercise')},
    'practice_infiltration': {'id': PRACTICE_INFILTRATION_MODULE_ID, 'name': _('x_infiltration')},
    'event_exam':{'id':EVENT_EXAM, 'name': _('x_exam')},
    'event_jeopardy':{'id':EVENT_JEOPARDY, 'name':_('x_jeopardy')},
    'event_attack_defense':{'id':EVENT_ATTACK_DEFENSE, 'name':_('x_ad_game')},
    'event_trial':{'id':EVENT_TRIAL, 'name':_('x_trial_game')},
    'event_infiltration':{'id':EVENT_INFILTRATION, 'name':_('x_infiltration')},
    'system': {'id': SYSTEM, 'name': _('x_system_module')}
}


def get_module(app_name):
    _ret = _module_list.get(app_name)
    return _ret


def get_all_module():
    return _module_list


def get_module_name(id):
    for m in _module_list:
        _m = _module_list.get(m)
        if _m.get('id') == id:
            return _m.get('name')

    return ''
