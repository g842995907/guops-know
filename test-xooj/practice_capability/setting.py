# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _

from common_framework.x_setting.settings import APISettings

from practice import api as practice_api
from practice_theory import api

DEFAULTS = {
    'MENU': (
        {
            'name': _('x_self_test_paper_library'),
            'parent':  _('x_contest'),
            'href': 'list',
            'icon': {
                'style': 'font awesonme',
                'value': 'fa fa-newspaper-o',
            },
        },
    ),
    'WEB_MENU': (
        {
            'name': _('x_self_test_paper'),
            'parent': _('x_practice'),
            'href': 'exam',
            'icon': {'value': 'oj-icon oj-icon-E91F font25P'}
        },
    ),
    'SLUG': 'practice_capability',
    'RELY_ON': [],
    'WEB_AD_SHOW': False,
}

IMPORT_STRINGS = ()

api_settings = APISettings('practice_capability', None, DEFAULTS, IMPORT_STRINGS)

categorys = [
]

practice_api.register(practice_api.PRACTICE_TYPE_THEORY, categorys, api.TheoryPractice)
