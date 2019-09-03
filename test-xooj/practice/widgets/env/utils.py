# -*- coding: utf-8 -*-
import os
import shutil
import uuid
import zipfile

from django.conf import settings
from django.utils import timezone
from rest_framework import exceptions

from common_auth.models import Team

from .error import error


# 解压check attack脚本文件
def extract_env_scripts(env_file):
    env_file.seek(0)
    zip_env_file = zipfile.ZipFile(env_file)
    if 'check.py' in zip_env_file.namelist() and 'attack.py' in zip_env_file.namelist():
        script_path = os.path.join(settings.MEDIA_ROOT, 'script', str(uuid.uuid4()))
        zip_env_file.extract('check.py', path=script_path)
        zip_env_file.extract('attack.py', path=script_path)
        check_script = os.path.join(script_path, 'check.py')
        attack_script = os.path.join(script_path, 'attack.py')
        return check_script, attack_script
    return None, None

# 删除check attack脚本文件
def remove_env_scripts(script):
    full_script_path = os.path.join(settings.BASE_DIR, script.rstrip('check.py').rstrip('attack.py'))
    shutil.rmtree(full_script_path)


def get_remain_seconds(destroy_time):
    if destroy_time:
        remain_seconds = (destroy_time - timezone.now()).total_seconds()
    else:
        remain_seconds = 0

    return remain_seconds


def get_team(team_id):
    if team_id:
        try:
            team = Team.objects.get(pk=team_id)
        except Team.DoesNotExist as e:
            raise exceptions.NotFound(error.TEAM_NOT_EXIST)
    else:
        team = None
    return team