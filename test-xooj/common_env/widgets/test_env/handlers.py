# -*- coding: utf-8 -*-

import hashlib
import uuid

from django.db import transaction

from system_configuration.models import SystemConfiguration
from common_env.handlers import manager as common_manager
from common_env.handlers.exceptions import MsgException
from common_env.models import Env, TestEnvMap
from common_env.setting import api_settings

from .error import error


# 测试环境处理, 创建销毁环境
class EnvHandler(object):

    def __init__(self, user, **kwargs):
        self.user = user
        self.base_handler = common_manager.EnvHandler(user, **kwargs)

    def get_name_prefix(self):
        return 'test'

    def get_test_env_map(self, template_env):
        return TestEnvMap.objects.filter(template_env=template_env).first()

    def check_create(self, template_env):
        using_status = Env.ActiveStatusList

        test_env_map = self.get_test_env_map(template_env)
        # 检查自己环境是否已存在
        if test_env_map and test_env_map.test_env and test_env_map.test_env.status in using_status:
            raise MsgException(error.TEST_ENV_EXIST)

        # 检查环境数量是否已满
        using_envs = Env.objects.filter(status__in=using_status)
        if using_envs.count() >= self.base_handler.creater_class.get_all_env_limit():
            raise MsgException(error.FULL_ENV_CAPACITY)

        # 检查自己环境数量是否已满
        my_using_envs = using_envs.filter(user=self.user)
        if my_using_envs.count() >= self.base_handler.creater_class.get_person_env_limit():
            raise MsgException(error.FULL_PERSONAL_ENV_CAPACITY)

        return test_env_map

    def create(self, template_env):
        test_env_map = self.check_create(template_env)

        flags = self.generate_flags(api_settings.MAX_FLAG_COUNT)
        name_prefix = self.get_name_prefix()
        test_env = self.base_handler.create(template_env, flags, name_prefix)
        if test_env_map:
            test_env_map.test_env = test_env
            test_env_map.save()
        else:
            test_env_map = TestEnvMap.objects.create(
                template_env=template_env,
                test_env=test_env,
            )

        return test_env

    def delete(self, template_env):
        test_env_map = self.get_test_env_map(template_env)
        if test_env_map and test_env_map.test_env and test_env_map.test_env.status in Env.UseStatusList:
            self.base_handler.delete(test_env_map.test_env)

    def get_env(self, template_env):
        test_env_map = self.get_test_env_map(template_env)
        if not test_env_map or not test_env_map.test_env or \
            test_env_map.test_env.status not in Env.ActiveStatusList:
            raise MsgException(error.TEST_ENV_NOT_EXIST)

        return test_env_map.test_env

    def get(self, template_env, is_complete=False):
        try:
            env = self.get_env(template_env)
        except MsgException as e:
            env = template_env
        data = self.base_handler.get(env, is_complete)
        return data

    @property
    def flag_prefix(self):
        if not hasattr(self, '_flag_prefix'):
            system_configuration = SystemConfiguration.objects.filter(key='answer_prefix').first()
            self._flag_prefix = system_configuration.value.strip() if system_configuration else 'flag'
        return self._flag_prefix

    def generate_flag(self):
        sz_random = hashlib.md5(str(uuid.uuid4())).hexdigest()
        flag = '%s{%s}' % (self.flag_prefix, sz_random)
        return flag

    def generate_flags(self, count):
        return [self.generate_flag() for i in range(count)]