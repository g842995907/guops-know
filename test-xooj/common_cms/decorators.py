# -*- coding: utf-8 -*-
import zipfile
from functools import partial, wraps

from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required as django_login_required
from rest_framework import status
from rest_framework.response import Response

login_required = partial(django_login_required, login_url='common_cms:login')

white_list = ('bmp', 'png', 'jpg', 'jpeg', 'md')


def judge_zip(zfile):
    zf = zipfile.ZipFile(zfile, 'r')
    file_list = zf.filelist
    for f in file_list:
        if not f.filename.endswith('/'):
            if f.filename.split('.')[-1] not in white_list:
                return False

    return True


def file_filter(field_name):
    def filter(func):
        @wraps(func)
        def wrapper(*agrs, **kwargs):
            try:
                request = agrs[0]
                user_file = request.FILES.get(field_name, None)
                suffix = user_file.name.split('.')[-1]
            except:
                pass
            else:
                if (suffix == 'zip' and not judge_zip(user_file)) or (suffix != 'zip' and suffix not in white_list):
                    return Response(data=_("x_this_file_not_allow"), status=status.HTTP_400_BAD_REQUEST)

            return func(*agrs, **kwargs)
        return wrapper
    return filter
