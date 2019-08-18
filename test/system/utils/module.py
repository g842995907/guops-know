# -*- coding: utf-8 -*-

from django.utils.translation import ugettext_lazy as _

BASE_AUTH_MODULE_ID = 0x1000
SYSTEM = 0x1001

BASE_SCENE_MODULE_ID = 0x2000
CR_SCENE_MODULE_ID = 0x2001
BASE_MISSION_MODULE_ID = 0x2002

BASE_TRAFFIC_MODULE_ID = 0x3000
TRAFFIC_EVENT_MODULE_ID = 0X3001

BASE_MONITOR_MODULE_ID = 0x4000


_module_list = {
    'base_auth': {'id': BASE_AUTH_MODULE_ID, 'name': _('x_user')},
    'system': {'id': SYSTEM, 'name': _('x_system_module')},
    'base_scene': {'id': BASE_SCENE_MODULE_ID, 'name': _('x_target')},
    'cr_scene': {'id': CR_SCENE_MODULE_ID, 'name': _('x_scene')},
    'base_mission': {'id': BASE_MISSION_MODULE_ID, 'name': _('x_mission')},
    'base_traffic': {'id': BASE_TRAFFIC_MODULE_ID, 'name': _('x_traffic')},
    'traffic_event':{'id':TRAFFIC_EVENT_MODULE_ID, 'name': _('x_traffic_event')},
    'base_monitor':{'id':BASE_MONITOR_MODULE_ID, 'name':_('x_monitor')},
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


def get_app_name(obj):
    return obj.__module__.split('.')[0]