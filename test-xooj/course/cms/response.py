# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from common_framework.utils.enum import enum

CONSTANTTYPE = enum(
    HEORETICAL_LESSON=_("x_heoretical_lesson"),
    EXPERIMENT_LESSON=_("x_experiment_lesson")
)