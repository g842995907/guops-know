# -*- coding: utf-8 -*-
import os
import uuid

from oj import settings


def save_system_logo(originpath):
    system_logo_path = os.path.join(settings.MEDIA_ROOT, 'system_logo')
    filename = str(uuid.uuid4()) + '.png'
    if not os.path.exists(system_logo_path):
        os.mkdir(system_logo_path)
    full_file_name = os.path.join(system_logo_path, filename)
    try:
        file_object = open(os.path.join(settings.BASE_DIR, originpath.lstrip('/')), 'rb')
        chunk = file_object.read()
        fileobj = open(full_file_name, 'wb')
        fileobj.write(chunk)
    except IOError:
        raise IOError
    finally:
        fileobj.close()

    delete_origin_logo(os.path.join(settings.BASE_DIR, originpath.lstrip('/')))

    return filename


def delete_origin_logo(path):
    if os.path.exists(path):
        try:
            os.remove(path)
        except Exception, e:
            pass
