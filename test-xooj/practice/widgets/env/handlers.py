# -*- coding: utf-8 -*-
import copy
import datetime
import hashlib
import json
import logging
import uuid

from django.utils import timezone

from system_configuration.models import SystemConfiguration
from common_env.handlers import manager as common_manager
from common_env.handlers.exceptions import MsgException
from common_env.models import Env
from common_env.setting import api_settings as common_env_settings

from practice.base_models import TaskEnv

from .error import error
from .utils import get_remain_seconds

logger = logging.getLogger(__name__)


# 环境处理, 创建销毁环境
class EnvHandler(object):
    def __init__(self, user, **kwargs):
        self.user = user
        self.team = kwargs.get('team', None)
        self.base_handler = common_manager.EnvHandler(user, **kwargs)
        self._check_team()
        if self.team:
            self.group_filter_params = {
                'env__team': self.team
            }
        else:
            self.group_filter_params = {
                'env__user': self.user
            }

    # 检查用户是否属于队伍
    def _check_team(self):
        # 不检查管理员
        if self.team and not self.base_handler.is_admin:
            if self.user.team != self.team:
                raise MsgException(error.NO_PERMISSION)

    def get_name_prefix(self, task, template_task_env):
        return '{type}.{player}.{task}'.format(
            type=TaskEnv.Type.reverse_source[template_task_env.type],
            player=self.team.name if self.team else self.user.username,
            task=task.title,
        )

    def get_template_task_env(self, task):
        template_task_env = task.envs.filter(env__status=Env.Status.TEMPLATE).first()
        if not template_task_env:
            raise MsgException(error.TASK_ENV_NOT_CONFIGURED)
        return template_task_env

    def check_create(self, task):
        template_task_env = self.get_template_task_env(task)

        using_status = Env.ActiveStatusList

        # 当前环境类型使用的环境
        using_type_task_envs = task.envs.filter(type=template_task_env.type, env__status__in=using_status)
        # 所有正在使用的场景
        using_envs = Env.objects.filter(status__in=using_status)

        if template_task_env.type == TaskEnv.Type.PRIVATE:
            # 检查是否已存在私有环境
            if using_type_task_envs.filter(**self.group_filter_params).exists():
                raise MsgException(error.TASK_ENV_EXIST)
            # 检查总体环境数量是否已满
            if using_envs.count() >= self.base_handler.creater_class.get_all_env_limit():
                raise MsgException(error.FULL_ENV_CAPACITY)
            if not self.team:
                # 检查个人环境数量是否已满
                my_using_envs = using_envs.filter(user=self.user)
                # 由于共享环境/队伍环境存在，需排除所有共享环境/队伍环境
                if my_using_envs.count() - self.base_handler.creater_class.get_ignored_using_env_count(self.user) >= self.base_handler.creater_class.get_person_env_limit():
                    raise MsgException(error.FULL_PERSONAL_ENV_CAPACITY)
        elif template_task_env.type == TaskEnv.Type.SHARED:
            # 检查是否已存在共享给自己的环境
            if using_type_task_envs.filter(shared_users=self.user).exists():
                raise MsgException(error.TASK_ENV_EXIST)

            # 如果已存在未共享给自己的共享环境, 由于只会添加共享引用不会创建场景, 所以不需要检查数量限制
            task_env = using_type_task_envs.first()
            if task_env:
                # 直接返回无需创建的存在的共享环境
                return template_task_env, task_env
            else:
                # 检查环境数量是否已满
                if using_envs.count() >= self.base_handler.creater_class.get_all_env_limit():
                    raise MsgException(error.FULL_ENV_CAPACITY)
                    # 共享环境不检查个人环境数量是否已满
        else:
            raise MsgException(error.NO_PERMISSION)

        return template_task_env, None

    def create(self, task):
        template_task_env, task_env = self.check_create(task)

        # 创建之前清除错误环境
        self.delete(task)

        if not task_env:
            task_env = copy.copy(template_task_env)
            task_env.pk = None
            if task_env.is_dynamic_flag:
                flags = self.generate_flags(task_env.flag_count)
            else:
                flags = task.answer.split('|')
            task_env.flags = json.dumps(flags)

            name_prefix = self.get_name_prefix(task, template_task_env)
            task_env.env = self.base_handler.create(task_env.env, flags, name_prefix)
            task_env.save()
            task.envs.add(task_env)

        # 共享环境添加引用
        if task_env.type == TaskEnv.Type.SHARED:
            task_env.shared_users.add(self.user)

        return task_env

    def recover(self, task, async=True):
        task_env = self.get_user_task_envs(task).first()
        if task_env and task_env.env and task_env.env.status == Env.Status.PAUSE:
            pause_time = task_env.env.pause_time
            if task_env.destroy_time and pause_time:
                pause_timedelta = timezone.now() - pause_time
                task_env.destroy_time = task_env.destroy_time + pause_timedelta
                task_env.save()
            self.base_handler.recover(task_env.env, async)
        return task_env

    def delete(self, task, async=True):
        task_envs = self.get_user_task_envs(task)

        for task_env in task_envs:
            if task_env.type == TaskEnv.Type.PRIVATE:
                # 私有环境直接删掉
                self.base_handler.delete(task_env.env, async)
            else:
                # 共享环境删掉关系
                task_env.shared_users.remove(self.user)
                # 如果没有共享关系再删除环境
                if not task_env.shared_users.exists():
                    self.base_handler.delete(task_env.env, async)

    def get_user_task_envs(self, task):
        template_task_env = self.get_template_task_env(task)

        task_envs = task.envs.filter(
            type=template_task_env.type,
            env__status__in=Env.UseStatusList,
        )
        if template_task_env.type == TaskEnv.Type.PRIVATE:
            task_envs = task_envs.filter(**self.group_filter_params)

        return task_envs


    def get_task_env(self, task):
        template_task_env = self.get_template_task_env(task)
        using_task_envs = task.envs.filter(type=template_task_env.type, env__status__in=Env.ActiveStatusList)
        if template_task_env.type == TaskEnv.Type.PRIVATE:
            task_env = using_task_envs.filter(**self.group_filter_params).first()
        else:
            task_env = using_task_envs.filter(shared_users=self.user).first()

        if not task_env:
            raise MsgException(error.TASK_ENV_NOT_EXIST)

        return task_env

    def get(self, task, is_complete=False):
        try:
            task_env = self.get_task_env(task)
        except MsgException as e:
            task_env = self.get_template_task_env(task)
        else:
            # 修正数据
            destroy_delay = task_env.destroy_delay
            if task_env.env.status in Env.UsingStatusList and not task_env.destroy_time and destroy_delay:
                task_env.destroy_time = timezone.now() + datetime.timedelta(hours=destroy_delay)
                task_env.save()

        data = self.base_handler.get(task_env.env, is_complete)

        data.update({
            'task_env_id': task_env.id,
            'task_env_type': task_env.type,
            'destroy_time': task_env.destroy_time,
            'remain_seconds': get_remain_seconds(task_env.destroy_time)
        })
        return data

    def delay(self, task):
        task_env = self.get_task_env(task)

        if task_env.env.status not in Env.UsingStatusList or not task_env.destroy_time:
            raise MsgException(error.NO_PERMISSION)

        left_time = datetime.timedelta(minutes=15)
        delay_time = datetime.timedelta(hours=1)
        # only fewer than 15 minites can delay
        if task_env.destroy_time < timezone.now() or task_env.destroy_time > timezone.now() + left_time:
            raise MsgException(error.NO_PERMISSION)

        task_env.destroy_time = task_env.destroy_time + delay_time
        try:
            task_env.save()
        except Exception as e:
            logger.error('delay taskenv[env_id=%s] error: %s', task_env.id, e)
            raise e

        return task_env

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

    # 用来获取最近申请的所有环境的flag，用以评判flag(新增)
    def get_all_recent_flags(self, task, start_time=None, flag=None, recent_one=False):
        template_task_env = self.get_template_task_env(task)
        recent_task_envs = task.envs.filter(
            type=template_task_env.type,
            env__status__in=Env.AllStatusList,
        )
        if start_time:
            recent_task_envs = recent_task_envs.filter(env__create_time__gte=start_time)
        if template_task_env.type == TaskEnv.Type.PRIVATE:
            recent_task_envs = recent_task_envs.filter(**self.group_filter_params)
        recent_task_envs = recent_task_envs.order_by('-env__create_time')
        recent_flags = []
        for recent_task_env in recent_task_envs:
            try:
                flags = json.loads(recent_task_env.flags)
            except Exception as e:
                logger.error('invalid task env[%s] flags: %s' % (recent_task_env.pk, recent_task_env.flags))
            else:
                if flag and (flag in flags or unicode(flag) in flags):
                    return flags
                elif recent_one:
                    return flags
                else:
                    recent_flags.extend(flags)

        return recent_flags


def env_created_callback(env):
    task_env = TaskEnv.objects.filter(env=env).first()
    if not task_env:
        return None

    destroy_delay = task_env.destroy_delay
    if destroy_delay:
        task_env.destroy_time = timezone.now() + datetime.timedelta(hours=destroy_delay)
        task_env.save()

common_env_settings.ENV_CREATED_CALLBACKS.add(env_created_callback)