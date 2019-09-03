# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from base.utils.error import Error
from base.utils.text import trans as _

error = Error(
)

mission_period_error = Error(
    INVALID_SCENE_ID=_('x_invalid_scene_id'),
    SCENE_ID_REQUIRED=_('x_scene_id_required'),
    PERIODS_REQUIRED=_('x_period_required'),
    PERIOD_TYPE_ERROR=_('x_period_type_must_list'),
    PERIOD_DUPLICATE=_('x_duplicate_period'),
    PERIOD_DELETE_ERROR=_('x_delete_period_error'),
)
