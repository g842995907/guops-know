# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from common_framework.utils.enum import enum

ResError = enum(
    VULN_CONNECTED_FAILED=_('x_vuln_connected_failed'),
)
