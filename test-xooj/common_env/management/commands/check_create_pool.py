# -*- coding: utf-8 -*-
import logging
import time

from django.core.management import BaseCommand

from common_env.handlers import pool


logger = logging.getLogger(__name__)


# 检查创建池
class Command(BaseCommand):
    def handle(self, *args, **options):
        while True:
            pool.check_pop_pool()
            time.sleep(10)


