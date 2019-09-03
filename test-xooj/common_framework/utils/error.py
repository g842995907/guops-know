from __future__ import unicode_literals

from django.utils import six
from rest_framework.exceptions import ErrorDetail

from common_framework.utils.enum import Enum


class Error(object):
    error = Enum()

    def __new__(cls, **errors):
        custom_errors = {}
        for attr_name, error_desc in errors.items():
            error_code = cls.generate_error_code(attr_name)
            if isinstance(error_desc, six.string_types):
                detail = ErrorDetail(error_desc, error_code)
            else:
                error_desc.code = error_code
                detail = error_desc
            custom_errors[attr_name] = detail
        cls.error.update(**custom_errors)
        return Enum(**custom_errors)

    @classmethod
    def generate_error_code(cls, attr_name):
        return attr_name

error = Error.error
