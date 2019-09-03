# -*- coding: utf-8 -*-
import json
import cPickle as pickle
import logging

from django.db.models import Sum, Count
from django.utils import timezone

from common_env.models import ServerCreatePool, WaitingCreatePool
from common_env.setting import api_settings


logger = logging.getLogger(__name__)


def _get_server_key(server):
    return '%s:%s' % (server._meta.db_table, server.pk)


def add_server(server=None, key=None, estimate_consume_time=0):
    if server and key is None:
        key = _get_server_key(server)

    if key is not None:
        ServerCreatePool.objects.create(unique_id=key, estimate_consume_time=estimate_consume_time)


def remove_server(server=None, key=None):
    if server and key is None:
        key = _get_server_key(server)

    if key is not None:
        ServerCreatePool.objects.filter(unique_id=key).delete()


def is_full(need_count=1):
    creating_count = ServerCreatePool.objects.count()
    if creating_count + need_count > api_settings.SERVER_CREATE_POOL_LIMIT:
        return True
    else:
        return False


def get_executing_min_remain_time():
    now_time = timezone.now()
    min_remain_time = 0
    for create_instance in ServerCreatePool.objects.all():
        pass_seconds = (now_time - create_instance.create_time).total_seconds()
        remain_time = create_instance.estimate_consume_time - pass_seconds
        if remain_time < 0:
            remain_time = 0
        min_remain_time = min(min_remain_time, remain_time)
        if min_remain_time == 0:
            break
    return min_remain_time or 10


def get_executor_info(executor=None, instance=None):
    if not instance and executor:
        condition = WaitingCreatePool.dump_executor(executor)
        instance = WaitingCreatePool.objects.filter(**condition).first()
    if instance:
        stat = WaitingCreatePool.objects.filter(
            pk__lt=instance.pk
        ).aggregate(
            count=Count('id'),
            wait_time=Sum('estimate_consume_time')
        )
        return {
            'creating_count': ServerCreatePool.objects.count(),
            'queue_seq': stat['count'] + 1,
            'wait_time': (stat['wait_time'] or 0) + get_executing_min_remain_time(),
        }
    return None


def add_executor(executor, consume_count=1, estimate_consume_time=0):
    condition = WaitingCreatePool.dump_executor(executor)
    instance = WaitingCreatePool.objects.filter(**condition).first()
    if not instance:
        instance = WaitingCreatePool.objects.create(
            estimate_consume_time=estimate_consume_time,
            consume_count=consume_count,
            extra=executor.get('extra', ''),
            **condition)
    return instance


def remove_executor(executor):
    condition = WaitingCreatePool.dump_executor(executor)
    WaitingCreatePool.objects.filter(**condition).delete()


def check_pop_pool():
    logger.info('check pop pool start')
    # 获取当前创建中机器数量
    creating_count = ServerCreatePool.objects.count()
    # 计算可用数量
    avaliable_count = api_settings.SERVER_CREATE_POOL_LIMIT - creating_count
    if avaliable_count <= 0:
        logger.info('pool has no avaliable count')
    else:
        # 获取队列
        queues = WaitingCreatePool.objects.order_by('id')
        for queue in queues:
            if avaliable_count < queue.consume_count:
                logger.info('pool has avaliable count: %s, queue need: %s', avaliable_count, queue.consume_count)
                break

            avaliable_count = avaliable_count - queue.consume_count
            queue.execute(logger=logger)

    logger.info('check pop pool end')