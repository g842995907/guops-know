# -*- coding: utf-8 -*-
import logging

from django.core.management import BaseCommand

from common_env.models import Env, EnvTerminal, StandardDevice
from common_env.cms.api import EnvViewSet
from common_env.utils.standard_device import delete_tmp_vm

from common_framework.utils.constant import Status
from common_framework.utils.unique import generate_delete_flag
from practice.constant import TaskStatus


logger = logging.getLogger(__name__)


# 清除没有被使用的场景配置（慎用）
# 这是一个特殊命令，方便部署人员清理的，不属于项目本身，所以会有调用课程和题目app模块
class Command(BaseCommand):
    def handle(self, *args, **options):
        # 所有环境配置
        envs = Env.objects.filter(status=Env.Status.TEMPLATE)

        no_use_envs = []
        for env in envs:
            is_referenced = False
            # 是否有课件引用
            for lessonenv in env.lessonenv_set.all():
                if lessonenv.lesson_set.filter(status=Status.NORMAL).exists():
                    is_referenced = True
                    break
            if is_referenced:
                continue

            # 是否有题目引用
            for taskenv in env.taskenv_set.all():
                if hasattr(taskenv, 'practiceexercisetask_set') and taskenv.practiceexercisetask_set.filter(status=TaskStatus.NORMAL).exists():
                    is_referenced = True
                    break
                if hasattr(taskenv, 'manmachinetask_set') and taskenv.manmachinetask_set.filter(status=TaskStatus.NORMAL).exists():
                    is_referenced = True
                    break
                if hasattr(taskenv, 'practiceattackdefensetask_set') and taskenv.practiceattackdefensetask_set.filter(status=TaskStatus.NORMAL).exists():
                    is_referenced = True
                    break
                if hasattr(taskenv, 'realvulntask_set') and taskenv.realvulntask_set.filter(status=TaskStatus.NORMAL).exists():
                    is_referenced = True
                    break
            if is_referenced:
                continue

            no_use_envs.append(env)

        for env in no_use_envs:
            logger.info('clear no use env[%s] %s' % (env.pk, env.name))
            EnvViewSet._destroy_env_related(env)
            env.status = Env.Status.DELETED
            env.save()


        # 清除镜像
        devices = StandardDevice.objects.filter(
            role=StandardDevice.Role.TERMINAL,
            status=StandardDevice.Status.NORMAL
        )

        no_use_devices = []
        for device in devices:
            # 是否有环境引用
            if EnvTerminal.objects.filter(
                env__status=Env.Status.TEMPLATE,
                image=device.name,
            ).exists():
                continue

            no_use_devices.append(device)

        for device in no_use_devices:
            logger.info('clear no use device[%s] %s' % (device.pk, device.name))
            if device.tmp_vm:
                delete_tmp_vm(device.tmp_vm)
            device.name = device.name + generate_delete_flag(fixed=False)
            device.tmp_vm = None
            device.status = StandardDevice.Status.DELETE
            device.save()
