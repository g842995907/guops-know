# -*- coding: utf-8 -*-
import logging
import datetime

from django.conf import settings
from django.db import connection
from django.utils import timezone


logger = logging.getLogger(__name__)
import django.dispatch

clean = django.dispatch.Signal()


# 清除过期环境
def clear_expired_env():
    try:
        from common_env.handlers.manager import admin_delete_env
        from common_env.models import Env, TestEnvMap

        from course.models import LessonEnv
        from practice.base_models import TaskEnv

        now_time = timezone.now()

        # 题目环境
        expired_task_envs = TaskEnv.objects.exclude(
            env=None
        ).filter(
            env__status__in=(Env.Status.CREATING, Env.Status.USING),
            destroy_time__lte=timezone.now()
        )

        for task_env in expired_task_envs:
            try:
                admin_delete_env(task_env.env)
                logger.info('clear expired task env[task_env_id=%s, env_id=%s] ok' % (task_env.id, task_env.env.id))
            except Exception as e:
                logger.error('clear expired task env[task_env_id=%s, env_id=%s] error: %s' % (
                    task_env.id, task_env.env.id, str(e)))

        # 实验环境
        expired_lesson_envs = LessonEnv.objects.exclude(
            env=None
        ).filter(
            env__status__in=(Env.Status.CREATING, Env.Status.USING),
            destroy_time__lte=timezone.now()
        )
        for lesson_env in expired_lesson_envs:
            try:
                admin_delete_env(lesson_env.env)
                logger.info('clear expired lesson env[lesson_env_id=%s, env_id=%s] ok' % (lesson_env.id, lesson_env.env.id))
            except Exception as e:
                logger.error('clear expired lesson env[lesson_env_id=%s, env_id=%s] error: %s' % (
                    lesson_env.id, lesson_env.env.id, str(e)))

        # 场景测试环境
        prev_time = now_time - datetime.timedelta(hours=2)
        test_env_maps = TestEnvMap.objects.exclude(
            test_env=None
        ).filter(
            test_env__status__in=Env.ActiveStatusList,
            test_env__create_time__lte=prev_time,
        )

        for test_env_map in test_env_maps:
            try:
                admin_delete_env(test_env_map.test_env)
                logger.info('clear expired test env[test_env_map_id=%s, env_id=%s] ok' % (test_env_map.id, test_env_map.test_env.id))
            except Exception as e:
                logger.error('clear expired test env[test_env_map_id=%s, env_id=%s] error: %s' % (
                    test_env_map.id, test_env_map.test_env.id, str(e)))

        connection.close()
    except Exception as e:
        logger.error('clear expired task env error: %s' % str(e))

    from common_framework.utils import delay_task
    delay_task.new_task(clear_expired_env, 60 * 2, ())


def _clear_resources(resource_ids, delete_func, base_queryset_infos, log_format):
    if resource_ids:
        using_resource_ids = []
        for base_queryset_info in base_queryset_infos:
            base_queryset = base_queryset_info[0]
            related_field = base_queryset_info[1]
            using_datas = base_queryset.filter(**{related_field + '__in': resource_ids})
            using_resource_ids.extend([getattr(using_data, related_field) for using_data in using_datas])
        not_use_resource_ids = list(set(resource_ids) - set(using_resource_ids))
        if not_use_resource_ids:
            logger.info(log_format % not_use_resource_ids)
            for resource_id in not_use_resource_ids:
                try:
                    delete_func(resource_id)
                except Exception as e:
                    logger.error('clear not use resource error: %s' % str(e))


# 清除异常不用的网络，路由，虚拟机等占用着的资源
def clear_not_use_resources():
    logger.info('clear not use resources start')
    # 清除场景相关的资源
    try:
        from common_env.handlers.local_lib import scene
        from common_env.models import Env, EnvTerminal, EnvNet, EnvGateway, StandardDeviceEditServer
        from common_env.setting import api_settings as common_env_settings
        from common_scene.setting import api_settings as common_scene_settings
        from common_scene.complex.views import BaseScene
        from common_scene.clients.neutron_client import Client as NeutronClient

        operator = BaseScene()

        using_status = Env.ActiveStatusList

        vms = operator.list_server(prefix=common_env_settings.BASE_GROUP_NAME)
        dockers = operator.list_container(prefix=common_env_settings.BASE_GROUP_NAME)
        routers = operator.list_router(prefix=common_env_settings.BASE_GROUP_NAME)
        firewalls = operator.list_firewall(prefix=common_env_settings.BASE_GROUP_NAME)
        networks = operator.list_network(prefix=common_env_settings.BASE_GROUP_NAME)

        _clear_resources(
            [vm.id for vm in vms],
            scene.vm.delete,
            [
                (EnvTerminal.objects.filter(env__status__in=using_status, image_type=EnvTerminal.ImageType.VM), 'vm_id'),
                (StandardDeviceEditServer.objects.exclude(status=StandardDeviceEditServer.Status.DELETED), 'tmp_vm_id')
            ],
            'clear not use env resources: not_use_vm_ids - %s'
        )
        _clear_resources(
            [docker.id for docker in dockers],
            scene.docker.delete,
            [
                (EnvTerminal.objects.filter(env__status__in=using_status, image_type=EnvTerminal.ImageType.DOCKER), 'vm_id'),
                (StandardDeviceEditServer.objects.exclude(status=StandardDeviceEditServer.Status.DELETED), 'tmp_docker_id')
            ],
            'clear not use env resources: not_use_docker_ids - %s'
        )
        _clear_resources(
            [router['id'] for router in routers],
            scene.router.delete,
            [
                (EnvGateway.objects.filter(env__status__in=using_status), 'router_id'),
                (StandardDeviceEditServer.objects.exclude(status=StandardDeviceEditServer.Status.DELETED), 'tmp_router_id')
            ],
            'clear not use env resources: not_use_router_ids - %s'
        )
        _clear_resources(
            [firewall['id'] for firewall in firewalls],
            scene.firewall.delete,
            [
                (EnvGateway.objects.filter(env__status__in=using_status), 'firewall_id'),
            ],
            'clear not use env resources: not_use_firewall_ids - %s'
        )
        _clear_resources(
            [network['id'] for network in networks],
            scene.network.delete,
            [
                (EnvNet.objects.filter(env__status__in=using_status), 'net_id'),
                (StandardDeviceEditServer.objects.exclude(status=StandardDeviceEditServer.Status.DELETED), 'tmp_network_id')
            ],
            'clear not use env resources: not_use_network_ids - %s'
        )

        operator.clear_unused_port()

        logger.info('clear not use env resources ok')
    except Exception as e:
        logger.error('clear not use env resources error: %s' % str(e))

    # 清除攻防赛相关的资源, 攻防赛机器使用的是场景的, 只需清理路由和网络
    try:
        from event_attack_defense.models import AttackDefenseEvent
        from event_attack_defense.setting import api_settings as event_ad_settings

        routers = operator.list_router(prefix=event_ad_settings.BASE_GROUP_NAME)
        networks = operator.list_network(prefix=event_ad_settings.BASE_GROUP_NAME)

        _clear_resources(
            [router['id'] for router in routers],
            scene.router.delete,
            [
                (AttackDefenseEvent.objects.all(), 'global_router'),
            ],
            'clear not use ad event resources: not_use_router_ids - %s'
        )

        _clear_resources(
            [network['id'] for network in networks],
            scene.network.delete,
            [
                (AttackDefenseEvent.objects.all(), 'global_network'),
            ],
            'clear not use ad event resources: not_use_network_ids - %s'
        )

        logger.info('clear not use ad event resources ok')

    except Exception as e:
        logger.error('clear not use ad event resources error: %s' % str(e))

    # 清除错误资源
    try:
        error_vms = operator.list_server(prefix=common_env_settings.BASE_GROUP_NAME, search_opts={'status': 'ERROR'})
        error_vm_ids = [error_vm.id for error_vm in error_vms]
        if error_vm_ids:
            logger.info('clear error resources: error_vm_ids - %s', error_vm_ids)
            for vm_id in error_vm_ids:
                scene.vm.delete(vm_id)

        dockers = operator.list_container(prefix=common_env_settings.BASE_GROUP_NAME)
        error_docker_ids = [docker.id for docker in dockers if docker.status.lower() == 'error']
        if error_docker_ids:
            logger.info('clear error resources: error_docker_ids - %s', error_docker_ids)
            for docker_id in error_docker_ids:
                scene.docker.delete(docker_id)
    except Exception as e:
        logger.error('clear error resources error: %s' % str(e))


    logger.info('clear not use resources end')

    # 一天执行一次
    from common_framework.utils import delay_task
    delay_task.new_task(clear_not_use_resources, 60 * 60 * 24, ())


def clear_unexcept_envs():
    from common_env.models import Env, EnvTerminal
    from common_env.handlers.manager import admin_delete_env
    unexcept_envs = Env.objects.exclude(
        envterminal__status=EnvTerminal.Status.DELETED,
    ).filter(
        status__in=Env.Status.DELETED,
    )
    for env in unexcept_envs:
        try:
            admin_delete_env(env)
            logger.info('clear unexcept env[env_id=%s] ok', env.id)
        except Exception as e:
            logger.error('clear unexcept env[env_id=%s] error: %s', env.id, str(e))

    # 半小时执行一次
    from common_framework.utils import delay_task
    delay_task.new_task(clear_unexcept_envs, 60 * 30, ())


def clear_uncontrol_standard_device_tmp_vm():
    from common_env.models import StandardDeviceEditServer
    from common_env.utils.standard_device import delete_tmp_vm
    # 启动时清除还没完成的机器
    tmp_vms = StandardDeviceEditServer.objects.filter(
        status__in=(StandardDeviceEditServer.Status.CREATING, StandardDeviceEditServer.Status.STARTING))
    for tmp_vm in tmp_vms:
        delete_tmp_vm(tmp_vm)


def clear_unexcept_standard_device_tmp_vm():
    from common_env.models import StandardDeviceEditServer
    from common_env.utils.standard_device import delete_tmp_vm
    # 每隔半小时清除半小时内还没完成的机器
    tmp_vms = StandardDeviceEditServer.objects.filter(
        create_time__lt=(timezone.now() - datetime.timedelta(minutes=30)),
        status__in=(StandardDeviceEditServer.Status.CREATING, StandardDeviceEditServer.Status.STARTING),
    )
    for tmp_vm in tmp_vms:
        delete_tmp_vm(tmp_vm)

    # 半小时执行一次
    from common_framework.utils import delay_task
    delay_task.new_task(clear_unexcept_standard_device_tmp_vm, 60 * 30, ())


def callback(**kwargs):
    from common_framework.utils import delay_task

    if not settings.DEBUG:
        delay_task.new_task(clear_not_use_resources, 0, ())

    def normal_callback():
        clear_expired_env()
        clear_unexcept_envs()
        clear_unexcept_standard_device_tmp_vm()
    delay_task.new_task(normal_callback, 0, ())

    clear_uncontrol_standard_device_tmp_vm()

    from common_remote.managers import check_setting
    check_setting()


clean.connect(callback)
