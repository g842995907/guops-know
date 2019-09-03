# -*- coding: utf-8 -*-
import logging
import os
import zipfile
import shutil
import time

from django.db import connection
from django.core.cache import cache
from django.utils import timezone

from common_framework.utils.django_cmd import django_dumpdata, django_loaddata, django_flush
from oj import settings

from system_configuration.models import Backup

logger = logging.getLogger(__name__)


def dump_sql(backup_id):
    logger.info('dump_sql start')
    logger.info(timezone.now())
    code, output, error = django_dumpdata(
        args=' --exclude=common_remote --exclude=auth.permission --exclude=contenttypes')
    logger.info('dump_sql end')
    logger.info(timezone.now())
    if code != 0:
        logger.error('dump_sql error info:%s' % (error))
    backup = Backup.original_objects.get(id=backup_id)
    cache.clear()
    if code == 0:
        path = backup.backup_name
        with open(path, 'w') as file_obj:
            file_obj.write(output)
        backup.status = Backup.Status.DONE
        backup.save()
    else:
        backup.status = Backup.Status.FAIL
        backup.save()


def load_sql(backup_id):
    backup = Backup.objects.get(id=backup_id)
    path = backup.backup_name
    if os.path.exists(path):
        logger.info('flush start')
        django_flush()
        logger.info('flush end')
        logger.info('load start')
        code, output, error = django_loaddata(path)
        logger.info('load end')
        if code == 0:
            backup.load_status = Backup.LoadStatus.DONE
            backup.save()
        else:
            backup.load_status = Backup.LoadStatus.FAIL
            backup.save()


def get_last_migrate_time():
    sql = '''
                       SELECT applied
                       FROM django_migrations
                       ORDER BY applied DESC
                   '''
    cursor = connection.cursor()
    cursor.execute(sql)
    migration_list = cursor.fetchall()
    migration_time = migration_list[0][0]
    return migration_time


def dir_backup(backup_id):
    backup = Backup.original_objects.get(id=backup_id)
    backup_pre = hex(int(time.mktime(backup.create_time.timetuple())))
    for path in settings.BACKUP_DIRS:
        if os.path.exists(os.path.join(settings.MEDIA_ROOT, path)):
            backup_path = '%s_%s.zip' % (path, str(backup_pre))
            make_zip(os.path.join(settings.MEDIA_ROOT, path), os.path.join(settings.MEDIA_ROOT, backup_path))


def dir_recover(backup_id):
    backup = Backup.original_objects.get(id=backup_id)
    backup_pre = hex(int(time.mktime(backup.create_time.timetuple())))
    for path in settings.BACKUP_DIRS:
        if os.path.exists(os.path.join(settings.MEDIA_ROOT, path)):
            for doc in os.listdir(os.path.join(settings.MEDIA_ROOT, path)):
                filepath = os.path.join(os.path.join(settings.MEDIA_ROOT, path), doc)
                os.remove(filepath)
            shutil.rmtree(os.path.join(settings.MEDIA_ROOT, path))
            zip_path = '%s_%s.zip' % (path, str(backup_pre))
            zipfiles = zipfile.ZipFile(os.path.join(settings.MEDIA_ROOT, zip_path), "r")
            if len(path.split('/')) > 1:
                path = path.split('/')
                path = "/".join(path[0:len(path) - 1])
                extract_path = os.path.join(settings.MEDIA_ROOT, path)
            else:
                extract_path = settings.MEDIA_ROOT
            zipfiles.extractall(extract_path)
            zipfiles.close()


def make_zip(source_dir, output_filename):
    zipf = zipfile.ZipFile(output_filename, 'w')
    pre_len = len(os.path.dirname(source_dir))
    for doc in os.listdir(source_dir):
        pathfile = os.path.join(source_dir, doc)
        arcname = pathfile[pre_len:].strip(os.path.sep)
        zipf.write(pathfile, arcname)
    zipf.close()
