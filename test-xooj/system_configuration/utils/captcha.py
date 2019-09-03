# -*- coding: utf-8 -*-
from rest_framework import exceptions

from system_configuration.response import CAPTCHA


def captcha_val(request, captcha_key):
    if captcha_key and captcha_key.lower() == request.session.get('captcha'):
        del request.session['captcha']
        return True
    return False


def rest_captcha_val(request):
    captcha_key = request.data.get('captcha')
    if not captcha_val(request, captcha_key):
        raise exceptions.ValidationError({
            'captcha': [CAPTCHA.CAPTCHA_WRONG]
        })
