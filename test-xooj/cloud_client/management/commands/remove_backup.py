# -*- coding: utf-8 -*-
import os
import subprocess

import logging

from django.core.management import BaseCommand

logger = logging.getLogger()


class Command(BaseCommand):
    def handle(self, *args, **options):
        backup_path = os.path.join("/home", "xoj_backup")

        rm_dir_cmd = 'rm -r {}'.format(backup_path)

        process = subprocess.Popen(rm_dir_cmd, env=os.environ.copy(), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   shell=True)
        output, error = process.communicate()

        if error:
            raise Exception(error)
