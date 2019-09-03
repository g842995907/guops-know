from __future__ import unicode_literals

import cPickle as pickle
import copy

from django.db import models
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

from common_auth.models import Classes, User, Faculty, Major
from common_framework.utils.enum import enum


class ShowLock(models.Model):
    lock = models.BooleanField(default=False)

    class Meta:
        abstract = True


class Builtin(models.Model):
    builtin = models.BooleanField(default=False)

    @classmethod
    def from_db(cls, db, field_names, values):
        origin = super(Builtin, cls).from_db(db, field_names, values)
        origin._origin = copy.deepcopy(origin)
        return origin

    def save(self, *args, **kwargs):
        if (hasattr(self, '_check_builtin') and not self._check_builtin) or self.builtin == 0:
            super(Builtin, self).save(*args, **kwargs)
            return

        if self._is_builtin_modify():
            raise PermissionDenied()

        super(Builtin, self).save(*args, **kwargs)

    def _is_builtin_modify(self):
        _fields = self._meta.concrete_fields
        ignore_fields = self.MyMeta._builtin_modify_field
        for field in _fields:
            field_name = field.attname
            if field_name in ignore_fields:
                continue

            origin_value = getattr(self._origin, field_name)
            new_value = getattr(self, field_name)

            if origin_value != new_value:
                return True

        return False

    class Meta:
        abstract = True

    class MyMeta:
        _builtin_modify_field = ['public', 'id', 'status', 'share', 'auth']


class BaseAuth(models.Model):
    AuthMode = enum(
        ALL_AUTH_MODE=1,
        CUSTOM_AUTH_MODE=2,
    )
    auth = models.PositiveIntegerField(default=AuthMode.CUSTOM_AUTH_MODE)
    auth_faculty = models.ManyToManyField(Faculty)
    auth_major = models.ManyToManyField(Major)
    auth_classes = models.ManyToManyField(Classes)

    class Meta:
        abstract = True


class BaseShare(models.Model):
    ShareMode = enum(
        ALL_SHARE_MODE=1,
        CUSTOM_SHARE_MODE=2,
    )
    share = models.PositiveSmallIntegerField(default=ShareMode.CUSTOM_SHARE_MODE)
    share_teachers = models.ManyToManyField(User, blank=True)

    class Meta:
        abstract = True


class AuthAndShare(BaseShare, BaseAuth):
    class Meta:
        abstract = True


class ExecutePool(models.Model):
    func = models.TextField(default='')
    params = models.TextField(default='')
    extra = models.TextField(default='')

    create_time = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True

    @classmethod
    def dump_executor(self, executor):
        condition = {
            'func': pickle.dumps(executor['func']),
            'params': pickle.dumps(executor['params']),
        }
        return condition

    def load_executor(self):
        executor = {
            'func': pickle.loads(str(self.func)),
            'params': pickle.loads(str(self.params)),
        }
        return executor

    def execute(self, logger=None, delete=True):
        executor = self.load_executor()
        func = executor['func']
        params = executor['params']
        if delete:
            self.delete()

        try:
            if logger:
                logger.info('execute start: %s.%s(%s)', func.__module__, func.func_name, params)
            ret = func(**params)
            if logger:
                logger.info('execute end: %s.%s(%s)', func.__module__, func.func_name, params)
        except Exception as e:
            if logger:
                logger.error('execute error: %s.%s(%s) error[%s]', func.__module__, func.func_name, params, e)
            raise e
        return ret
