# -*- coding: utf-8 -*-
from cStringIO import StringIO
import uuid
import os
from django.core.files.uploadedfile import InMemoryUploadedFile

BytesIO = StringIO


def save_image(full_logo_name):
    try:
        file_object = open(full_logo_name, 'rb')
        content = file_object.read()
        logofile = InMemoryUploadedFile(BytesIO(content), 'team_logo', str(uuid.uuid4()) + '.' + 'png',
                                        'image/jpeg', len(content), None)

    finally:
        file_object.close()
    # if os.path.exists(full_logo_name):
    #     try:
    #         os.remove(full_logo_name)
    #     except Exception, e:
    #         pass
    return logofile
