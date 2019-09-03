# -*- coding: utf-8 -*-
import os

from oj import settings
from system_configuration import models as system_models


def system_configuration_init():
    system_list = system_models.SystemConfiguration.objects.all()
    for system in system_list:
        if system.key == 'logo':
            system_logo_path = os.path.join(settings.MEDIA_ROOT, 'system_logo')
            system_logo_full_path = os.path.join(system_logo_path, system.value)
            if os.path.exists(system_logo_full_path):
                os.remove(system_logo_full_path)
        system.delete()
    backup_list = system_models.Backup.original_objects.all()
    for backup in backup_list:
        if os.path.exists(backup.backup_name):
            os.remove(backup.backup_name)
        backup.delete()
