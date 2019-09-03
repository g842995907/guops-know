# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import threading

from base.utils.app import AppConfig as BaseAppConfig


class AppConfig(BaseAppConfig):
    name = 'system'

    def ready(self):
        from django.db.models.signals import post_save
        from system.models import UpgradeVersion
        from system.signals import upgrade_system
        from system.utils.logset import set_log_level

        post_save.connect(upgrade_system, sender=UpgradeVersion)
        # redis 订阅后台
        t = threading.Thread(target=set_log_level)
        t.setDaemon(True)
        t.start()
