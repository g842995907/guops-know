# -*- coding: utf-8 -*-

import os

from django.utils import timezone

from common_framework.utils.scan import scan_file
from common_resource.execute import Dumper, Loader
from common_resource.setting import api_settings as resource_api_settings
from django.utils.translation import ugettext_lazy as _


def dump_task_event(queryset):
    dumper = Dumper(queryset)
    name = queryset.count() > 1 and timezone.now().strftime('%Y%m%d%H%M%S') or getattr(queryset[0], 'name',
                                                                                       _('x_task_event'))
    filename = 'event_{}.zip'.format(name)
    file_path = dumper.dumps(filename)
    return file_path


def scan_task_event_resource():
    return scan_file(resource_api_settings.LOAD_TMP_DIR, r'^event_\d{14,14}.zip$')


def load_task_event(filename):
    path = os.path.join(resource_api_settings.LOAD_TMP_DIR, filename)
    loader = Loader()
    loader.loads(path)