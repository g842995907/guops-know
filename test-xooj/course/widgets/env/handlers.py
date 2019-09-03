# -*- coding: utf-8 -*-
import copy
import datetime
import hashlib
import logging
import uuid

from django.db import transaction
from django.utils import timezone

from common_env.handlers import manager as common_manager
from common_env.handlers.exceptions import MsgException
from common_env.models import Env
from common_env.setting import api_settings as common_env_settings
from system_configuration.models import SystemConfiguration

from course.models import LessonEnv

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

    def get_name_prefix(self, lesson, template_lesson_env):
        return '{type}.{player}.{lesson}'.format(
            type=LessonEnv.Type.reverse_source[template_lesson_env.type],
            player=self.team.name if self.team else self.user.username,
            lesson=lesson.name,
        )

    def get_template_lesson_env(self, lesson):
        template_lesson_env = lesson.envs.filter(env__status=Env.Status.TEMPLATE).first()
        if not template_lesson_env:
            raise MsgException(error.LESSON_ENV_NOT_CONFIGURED)
        return template_lesson_env

    def check_create(self, lesson, group_users=None):
        template_lesson_env = self.get_template_lesson_env(lesson)

        using_status = Env.ActiveStatusList

        # 所有正在使用的场景
        using_envs = Env.objects.filter(status__in=using_status)

        # 小组环境
        if group_users:
            # 检查环境数量是否已满
            if using_envs.count() >= self.base_handler.creater_class.get_all_env_limit():
                raise MsgException(error.FULL_ENV_CAPACITY)

            lesson_env = lesson.envs.filter(
                type=LessonEnv.Type.GROUP,
                env__status__in=using_status,
                group_users__in=group_users,
            ).first()
            if lesson_env:
                # 直接返回无需创建的存在的小组环境
                return template_lesson_env, lesson_env
        else:
            # 当前环境类型使用的环境
            using_type_lesson_envs = lesson.envs.filter(type=template_lesson_env.type, env__status__in=using_status)
            if template_lesson_env.type == LessonEnv.Type.PRIVATE:
                # 检查是否已存在私有环境
                if using_type_lesson_envs.filter(**self.group_filter_params).exists():
                    raise MsgException(error.LESSON_ENV_EXIST)
                # 检查总体环境数量是否已满
                if using_envs.count() >= self.base_handler.creater_class.get_all_env_limit():
                    raise MsgException(error.FULL_ENV_CAPACITY)
                if not self.team:
                    # 检查个人环境数量是否已满
                    my_using_envs = using_envs.filter(user=self.user)
                    # 由于共享环境/队伍环境/小组环境存在，需排除所有共享环境/队伍环境/小组环境
                    if my_using_envs.count() - self.base_handler.creater_class.get_ignored_using_env_count(self.user) >= self.base_handler.creater_class.get_person_env_limit():
                        raise MsgException(error.FULL_PERSONAL_ENV_CAPACITY)
            elif template_lesson_env.type == LessonEnv.Type.SHARED:
                # 检查是否已存在共享给自己的环境
                if using_type_lesson_envs.filter(shared_users=self.user).exists():
                    raise MsgException(error.LESSON_ENV_EXIST)

                # 如果已存在未共享给自己的共享环境, 由于只会添加共享引用不会创建场景, 所以不需要检查数量限制
                lesson_env = using_type_lesson_envs.first()
                if lesson_env:
                    # 直接返回无需创建的存在的共享环境
                    return template_lesson_env, lesson_env
                else:
                    # 检查环境数量是否已满
                    if using_envs.count() >= self.base_handler.creater_class.get_all_env_limit():
                        raise MsgException(error.FULL_ENV_CAPACITY)
                        # 共享环境不检查个人环境数量是否已满
            else:
                raise MsgException(error.NO_PERMISSION)

        return template_lesson_env, None

    def create(self, lesson, group_users=None):
        template_lesson_env, lesson_env = self.check_create(lesson, group_users)

        # 创建之前清除错误环境
        self.delete(lesson, group_users=group_users)

        if not lesson_env:
            flags = self.generate_flags(common_env_settings.MAX_FLAG_COUNT)
            lesson_env = copy.copy(template_lesson_env)
            if group_users:
                lesson_env.type = LessonEnv.Type.GROUP
            lesson_env.pk = None
            name_prefix = self.get_name_prefix(lesson, template_lesson_env)
            lesson_env.env = self.base_handler.create(template_lesson_env.env, flags, name_prefix)
            lesson_env.save()
            lesson.envs.add(lesson_env)

        # 共享环境添加引用
        if lesson_env.type == LessonEnv.Type.SHARED:
            lesson_env.shared_users.add(self.user)
        # 小组环境添加组员
        elif lesson_env.type == LessonEnv.Type.GROUP:
            lesson_env.group_users.add(*group_users)

        return lesson_env

    def recover(self, lesson, async=True, group_users=None):
        lesson_env = self.get_user_lesson_envs(lesson, group_users).first()
        if lesson_env and lesson_env.env and lesson_env.env.status == Env.Status.PAUSE:
            pause_time = lesson_env.env.pause_time
            if lesson_env.destroy_time and pause_time:
                pause_timedelta = timezone.now() - pause_time
                lesson_env.destroy_time = lesson_env.destroy_time + pause_timedelta
                lesson_env.save()
            self.base_handler.recover(lesson_env.env, async)
        return lesson_env

    def delete(self, lesson, async=True, group_users=None):
        lesson_envs = self.get_user_lesson_envs(lesson, group_users)

        for lesson_env in lesson_envs:

            # 记录用户实验时间
            if not self.team and not self.base_handler.backend_admin and lesson_env.env.created_time:
                seconds = (timezone.now() - lesson_env.env.created_time).total_seconds()
                from course.utils.course_util import add_experiment_time
                add_experiment_time(self.user, lesson, seconds)

            if lesson_env.type in (LessonEnv.Type.PRIVATE, LessonEnv.Type.GROUP):
                # 私有环境 直接删掉
                self.base_handler.delete(lesson_env.env, async)
            elif lesson_env.type == LessonEnv.Type.SHARED:
                # 共享环境删掉关系
                lesson_env.shared_users.remove(self.user)
                # 如果没有共享关系再删除环境
                if not lesson_env.shared_users.exists():
                    self.base_handler.delete(lesson_env.env, async)

    def get_user_lesson_envs(self, lesson, group_users=None):
        if group_users:
            lesson_envs = lesson.envs.filter(
                type=LessonEnv.Type.GROUP,
                env__status__in=Env.UseStatusList,
                group_users__in=group_users,
            )
        else:
            template_lesson_env = self.get_template_lesson_env(lesson)
            # 优先删除小组环境
            lesson_envs = lesson.envs.filter(
                type=LessonEnv.Type.GROUP,
                env__status__in=Env.UseStatusList,
                group_users=self.user,
            )
            if not lesson_envs:
                lesson_envs = lesson.envs.filter(
                    type=template_lesson_env.type,
                    env__status__in=Env.UseStatusList,
                )
                if template_lesson_env.type == LessonEnv.Type.PRIVATE:
                    lesson_envs = lesson_envs.filter(**self.group_filter_params)
        return lesson_envs

    def get_lesson_env(self, lesson):
        template_lesson_env = self.get_template_lesson_env(lesson)
        using_lesson_envs = lesson.envs.filter(env__status__in=Env.ActiveStatusList)

        # 由于页面没有配置小组环境，没有小组模板环境，显式查询是否有小组环境
        lesson_env = using_lesson_envs.filter(type=LessonEnv.Type.GROUP, group_users=self.user).first()
        if lesson_env:
            return lesson_env

        using_lesson_envs = using_lesson_envs.filter(type=template_lesson_env.type)

        if template_lesson_env.type == LessonEnv.Type.PRIVATE:
            lesson_env = using_lesson_envs.filter(**self.group_filter_params).first()
        else:
            lesson_env = using_lesson_envs.filter(shared_users=self.user).first()

        if not lesson_env:
            raise MsgException(error.LESSON_ENV_NOT_EXIST)

        return lesson_env

    def get(self, lesson, is_complete=False):
        try:
            lesson_env = self.get_lesson_env(lesson)
        except MsgException as e:
            lesson_env = self.get_template_lesson_env(lesson)
        else:
            # 修正数据
            destroy_delay = lesson_env.destroy_delay
            if lesson_env.env.status in Env.UsingStatusList and not lesson_env.destroy_time and destroy_delay:
                lesson_env.destroy_time = timezone.now() + datetime.timedelta(hours=destroy_delay)
                lesson_env.save()

        data = self.base_handler.get(lesson_env.env, is_complete)

        data.update({
            'lesson_env_id': lesson_env.id,
            'lesson_env_type': lesson_env.type,
            'destroy_time': lesson_env.destroy_time,
            'remain_seconds': get_remain_seconds(lesson_env.destroy_time)
        })
        return data

    def delay(self, lesson):
        lesson_env = self.get_lesson_env(lesson)

        if lesson_env.env.status not in Env.UsingStatusList or not lesson_env.destroy_time:
            raise MsgException(error.NO_PERMISSION)

        left_time = datetime.timedelta(minutes=15)
        delay_time = datetime.timedelta(hours=1)
        # only fewer than 15 minites can delay
        if lesson_env.destroy_time < timezone.now() or lesson_env.destroy_time > timezone.now() + left_time:
            raise MsgException(error.NO_PERMISSION)

        lesson_env.destroy_time = lesson_env.destroy_time + delay_time
        try:
            lesson_env.save()
        except Exception as e:
            logger.error('delay lessonenv[env_id=%s] error: %s', lesson_env.id, e)
            raise e

        return lesson_env

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


def env_created_callback(env):
    lesson_env = LessonEnv.objects.filter(env=env).first()
    if not lesson_env:
        return None

    destroy_delay = lesson_env.destroy_delay
    if destroy_delay:
        lesson_env.destroy_time = timezone.now() + datetime.timedelta(hours=destroy_delay)
        lesson_env.save()


common_env_settings.ENV_CREATED_CALLBACKS.add(env_created_callback)