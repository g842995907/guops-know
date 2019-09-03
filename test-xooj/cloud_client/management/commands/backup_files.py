# -*- coding: utf-8 -*-
import os
import subprocess

from django.conf import settings
from django.core.management import BaseCommand
import logging

logger = logging.getLogger()


class Command(BaseCommand):
    def handle(self, *args, **options):
        backup_path = os.path.join("/home", "xoj_backup")
        if not os.path.exists(backup_path):
            os.mkdir(backup_path)

        backup_db_path = os.path.join(backup_path, 'backup.sql')
        backup_db_cmd = "mysqldump -ucyberpeace -pcyberpeace cyberpeace > {}".format(backup_db_path)
        process_db = subprocess.Popen(backup_db_cmd, env=os.environ.copy(), stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE,
                                      shell=True)
        output, error = process_db.communicate()

        backup_code_path = os.path.join(backup_path, 'x-oj')
        if not os.path.exists(backup_code_path):
            os.mkdir(backup_code_path)

        files = os.listdir(settings.BASE_DIR)

        if "media" in files:
            files.remove("media")

        cp_dir_cmd = 'cp -r {source} %s' % backup_code_path
        cp_file_cmd = 'cp {source} %s' % backup_code_path

        for file in files:
            source = os.path.join(settings.BASE_DIR, file)
            cmd = cp_dir_cmd if os.path.isdir(source) else cp_file_cmd
            args = cmd.format(source=source)

            process = subprocess.Popen(args, env=os.environ.copy(), stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       shell=True)
            output, error = process.communicate()

            if error:
                raise Exception(error)
