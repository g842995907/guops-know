# -*- coding: utf-8 -*-
import logging
import os

from django.conf import settings
from django.core.management import BaseCommand

from common_env.models import Env


logger = logging.getLogger(__name__)


# 清除没有被使用的场景配置文件
class Command(BaseCommand):
    def handle(self, *args, **options):
        # 所有环境配置
        envs = Env.objects.filter(status=Env.Status.TEMPLATE)

        file_dir_name = Env.file.field.get_directory_name()
        file_dir = os.path.join(settings.MEDIA_ROOT, file_dir_name)
        all_filenames = os.listdir(file_dir)

        using_filenames = []
        for env in envs:
            if env.file:
                using_filenames.append(os.path.basename(env.file.name))

        nouse_filenames = list(set(all_filenames) - set(using_filenames))
        for filename in nouse_filenames:
            file_path = os.path.join(file_dir, filename)
            os.remove(file_path)
            print 'remove file: %s' % file_path

