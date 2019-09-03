# -*- coding: utf-8 -*-
from django.core.management import BaseCommand

from dashboard.utils.checker import checker_oj


class Command(BaseCommand):
    """
    检查oj配置服务
    """

    def handle(self, *args, **options):
        print '=================oj配置服务检查开始================='
        checker_oj.OJ().checker()

        print '====================检查结束======================='

    # def add_arguments(self, parser):
    #     parser.add_argument('-p', dest='mysql_root_password', help='mysql root password', default=None)
