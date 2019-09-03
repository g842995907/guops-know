# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os
import shutil

from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile, TemporaryUploadedFile

from base.utils.text import rk


def get_language_code(request):
    return getattr(request, 'LANGUAGE_CODE', settings.LANGUAGE_CODE)


def is_en(request):
    language_code = get_language_code(request)
    return language_code == 'en'


def get_ip(request):
    if 'HTTP_X_FORWARDED_FOR' in request.META:
        return request.META['HTTP_X_FORWARDED_FOR']
    elif 'REMOTE_ADDR' in request.META:
        return request.META['REMOTE_ADDR']
    else:
        return ''


class RequestTmpDiskFile(object):

    block_size = 4096

    def __init__(self, request_file):
        self.request_file = request_file

        if isinstance(request_file, InMemoryUploadedFile):
            self.in_memory = True
            self.tmp_dir = os.path.join('/tmp', rk())
            self.file_path = os.path.join(self.tmp_dir, self.request_file.name)
        elif isinstance(request_file, TemporaryUploadedFile):
            self.in_memory = False
            self.file_path = self.request_file.file.name
        else:
            raise Exception('invalid request file')

    def __enter__(self):
        if self.in_memory:
            os.makedirs(self.tmp_dir)
            self.request_file.seek(0)

            with open(self.file_path, 'wb') as tmp_disk_file:
                while True:
                    data = self.request_file.read(self.block_size)
                    if data:
                        tmp_disk_file.write(data)
                    else:
                        break

        return self.file_path

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.in_memory:
            shutil.rmtree(self.tmp_dir)
            self.request_file.seek(0)
