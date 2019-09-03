# -*- coding: utf-8 -*-
import logging

from django.core.management import BaseCommand
from django.db.models import Q

from common_env.models import Env
from common_env.utils.resource import empty_zip_file, merge_config_to_file


logger = logging.getLogger(__name__)


# 清除没有被使用的场景配置文件
class Command(BaseCommand):
    def handle(self, *args, **options):
        # 所有环境配置
        envs = Env.objects.filter(Q(file__isnull=True) | Q(file=''), Q(status=Env.Status.TEMPLATE))

        for env in envs:
            env.file = merge_config_to_file(empty_zip_file(), env.json_config)
            env.save()
