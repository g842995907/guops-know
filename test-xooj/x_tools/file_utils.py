from __future__ import unicode_literals
import os

from django.conf import settings
from django.utils.deconstruct import deconstructible


@deconstructible
class ToolPath(object):
    def __init__(self, sub_path):
        self.sub_path = sub_path

    def __call__(self, instance, filename):
        ext = filename.split('.')[-1]
        filename = '{}_{}.{}'.format(instance.name, instance.version, ext)
        return os.path.join(self.sub_path, filename)


@deconstructible
class ToolCoverPath(object):
    def __init__(self, sub_path):
        self.sub_path = sub_path

    def __call__(self, instance, filename):
        ext = filename.split('.')[-1]
        filename = '{}.{}'.format(instance.name, ext)
        return os.path.join(self.sub_path, filename)


def handle_uploaded_file(f, name, sub_folder=None):
    sub_path = getattr(settings, 'MEDIA_ROOT')
    if sub_folder:
        sub_path = os.path.join(sub_path, sub_folder)
        if not os.path.exists(sub_path):
            os.makedirs(sub_path)
    file_path = os.path.join(sub_path, name)
    with open(file_path, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

    return file_path[1:] if file_path.startswith(".") else file_path

