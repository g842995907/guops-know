import os

from django.conf import settings

from base_monitor.models import Scripts


def get_script_path(script, script_type):
    if script_type == Scripts.Type.REMOTE:
        script_path = os.path.join(settings.MEDIA_ROOT, 'scripts/remote/{}').format(script)
    elif script_type == Scripts.Type.LOCAL:
        script_path = os.path.join(settings.MEDIA_ROOT, 'scripts/local/{}').format(script)
    else:
        raise Exception('No script file')

    if not os.path.exists(script_path):
        raise Exception('No script file')

    return script_path
