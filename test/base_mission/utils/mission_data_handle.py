# -*- coding: utf-8 -*-
import os
import shutil

from base.utils.thread import async_exe
from base_mission import constant
from base_mission.utils.exam_tasks_handler import create_update_tasks
from base_mission.utils.check_ctf_handler import save_ctf_or_check_mission
from cr import settings


def save_related_mission(mission, data, update=False):
    if mission.type in [constant.Type.CTF, constant.Type.CHECK]:
        save_ctf_or_check_mission(mission, data, update=update)
    elif mission.type == constant.Type.EXAM:
        create_update_tasks(mission, data)

    if mission.type == constant.Type.CHECK:
        async_exe(mission_copy_file, (mission, data,), delay=0)


def get_mission_script_dir(mission_id):
    return os.path.join(settings.MEDIA_ROOT, 'scripts/mission/{}').format(mission_id)


def get_related_mission_script_path(related_mission):
    mission_script_dir = get_mission_script_dir(related_mission.mission_id)
    mission_script_path = os.path.join(mission_script_dir, related_mission.scripts)
    return mission_script_path


def get_src_script_path(script, check_type):
    if check_type == constant.CheckType.SYSTEM:
        script_path = os.path.join(settings.MEDIA_ROOT, 'scripts/remote/{}').format(script)
    elif check_type == constant.CheckType.AGENT:
        script_path = os.path.join(settings.MEDIA_ROOT, 'scripts/local/{}').format(script)
    else:
        raise Exception('No script file')

    if not os.path.exists(script_path):
        raise Exception('No script file')

    return script_path


def mission_copy_file(mission, data):
    if not hasattr(mission, "id"):
        raise Exception('No id attribute')

    mission_script_dir = get_mission_script_dir(mission.id)

    if not os.path.exists(mission_script_dir):
        os.makedirs(mission_script_dir)

    if data.get("scripts", None):
        script = data.get("scripts")
    else:
        return False

    if "check_type" in data:
        check_type = data.get("check_type")
    else:
        return False

    script_path = get_src_script_path(script, check_type)

    mission_script_path = os.path.join(mission_script_dir, '{}').format(script)
    try:
        shutil.copyfile(script_path, mission_script_path)
    except Exception as e:
        raise Exception('An error occurred :%s', e)
