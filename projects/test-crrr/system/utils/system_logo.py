# -*- coding: utf-8 -*-
import os
import uuid

from cr import settings


def save_system_logo(originpath):
    if originpath == 'null':
        return ''
    try:
        if originpath.startswith('/media/system_logo'):
            return originpath
    except Exception:
        pass
    system_logo_path = os.path.join(settings.MEDIA_ROOT, 'system_logo')
    filename = str(uuid.uuid4()) + '.png'
    if not os.path.exists(system_logo_path):
        os.mkdir(system_logo_path)
    full_file_name = os.path.join(system_logo_path, filename)
    try:

        chunk = originpath.read()
        with open(full_file_name, 'wb') as fileobj:
            fileobj.write(chunk)
    except IOError:
        raise IOError

    return filename


def delete_origin_logo(path):
    if os.path.exists(path):
        try:
            os.remove(path)
        except Exception:
            pass
