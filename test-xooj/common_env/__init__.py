# -*- coding: utf-8 -*-
from django.utils.translation import ugettext as _

__version__ = '1.1.1'
def common_env_init():
    import logging
    logger = logging.getLogger(__name__)
    logger.info('init common env：start')

    from common_auth.models import User
    from .handlers.local_lib import scene
    from .handlers.manager import admin_delete_env, EnvHandler
    from .utils.standard_device import delete_tmp_vm
    from . import models as env_models

    admin_user = User.objects.get(pk=1)

    # 只删admin管理员以外的环境
    envs = env_models.Env.objects.exclude(user=admin_user)
    # 删真实环境
    logger.info('init common env： clear real scene start')
    envs = envs.exclude(status=env_models.Env.Status.TEMPLATE)
    for env in envs:
        logger.info('init common env： try clear env[%s]' % env.pk)
        env.file.delete()
        admin_delete_env(env)
    logger.info('init common env： clear real scene end')

    logger.info('init common env： clear env snapshot start')
    # 删快照
    template_envs = envs.filter(status=env_models.Env.Status.TEMPLATE)
    for template_env in template_envs:
        template_env.file.delete()
        if template_env.image_status != env_models.Env.ImageStatus.NOT_APPLY:
            logger.info('init common env： try clear env snapshot[%s]' % template_env.pk)
            env_handler = EnvHandler(admin_user, template_env, True)
            env_handler.delete_env_snapshot()
    logger.info('init common env： clear env snapshot end')

    # 删标靶临时机器
    logger.info('init common env： clear stardard device tmp vms start')
    tmp_vms = env_models.StandardDeviceEditServer.objects.all()
    for tmp_vm in tmp_vms:
        delete_tmp_vm(tmp_vm)
    logger.info('init common env： clear stardard device tmp vms end')

    # 删标靶镜像(TODO危险操作, 暂时去掉)
    # logger.info('init common env： clear stardard device image start')
    # standard_devices = env_models.StandardDevice.objects.exclude(create_user=admin_user).filter(
    #     type=env_models.StandardDevice.Role.TERMINAL
    # )
    # for standard_device in standard_devices:
    #     scene.delete_image(standard_device.name)
    # logger.info('init common env： clear stardard device image end')


    logger.info('init common env： clear database record start')
    # 清空快照环境对应记录(临时环境全部删除)
    snapshot_env_maps = env_models.SnapshotEnvMap.objects.all()
    for snapshot_env_map in snapshot_env_maps:
        if snapshot_env_map.tmp_env:
            delete_env_record(snapshot_env_map.tmp_env)
    snapshot_env_maps.delete()
    # 清空测试环境对应记录(临时环境全部删除)
    test_env_maps = env_models.TestEnvMap.objects.all()
    for test_env_map in test_env_maps:
        if test_env_map.test_env:
            delete_env_record(test_env_map.test_env)
    test_env_maps.delete()

    # 清空环境对应记录
    env_models.EnvNet.objects.exclude(env__user=admin_user).delete()
    envgateways = env_models.EnvGateway.objects.exclude(env__user=admin_user)
    for envgateway in envgateways:
        envgateway.nets.clear()
    envgateways.delete()
    envterminals = env_models.EnvTerminal.objects.exclude(env__user=admin_user)
    for envterminal in envterminals:
        envterminal.nets.clear()
    envterminals.delete()
    env_models.Env.objects.exclude(user=admin_user).delete()

    # 清空标靶对应记录
    env_models.StandardDevice.objects.exclude(create_user=admin_user).delete()
    env_models.StandardDeviceEditServer.objects.all().delete()
    logger.info('init common env： clear database record end')


# 物理删除单个环境记录
def delete_env_record(env):
    from . import models as env_models
    env_models.EnvNet.objects.filter(env=env).delete()

    for envgateway in env_models.EnvGateway.objects.filter(env=env):
        envgateway.nets.clear()
    env_models.EnvGateway.objects.filter(env=env).delete()

    for envterminal in env_models.EnvTerminal.objects.filter(env=env):
        envterminal.nets.clear()
    env_models.EnvTerminal.objects.filter(env=env).delete()

    env.delete()



def get_env_target_task(env):
    from .models import TestEnvMap

    test_env_map = TestEnvMap.objects.filter(test_env=env).first()
    if not test_env_map:
        return None

    return {
        'app': _('场景测试'),
        'type': '',
        'name': test_env_map.test_env.name,
    }
