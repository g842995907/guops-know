# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import logging
import os
import shutil
import StringIO
import uuid
import zipfile
from io import BytesIO

from django.utils import timezone
from django.core.files.uploadedfile import InMemoryUploadedFile
from common_framework.utils.zip import Ziper
from common_resource.execute import Dumper, Loader
from common_resource.setting import api_settings as resource_api_settings

from .vis_config import vis_to_backend, backend_to_vis
from ..setting import api_settings


logger = logging.getLogger(__name__)


# 从在线编辑配置转换配置信息
def convert_vis_config(vis_config):
    return vis_to_backend(vis_config)

# 从配置信息转换在线编辑配置
def convert_json_config(json_config):
    return backend_to_vis(json_config)


def empty_zip_file():
    return StringIO.StringIO()


# 从资源文件读取配置信息
def read_json_config_from_file(zip_file):
    zip_env_file = zipfile.ZipFile(zip_file)
    if api_settings.CONFIG_FILE_NAME in zip_env_file.namelist():
        json_config = zip_env_file.read(api_settings.CONFIG_FILE_NAME)
        json_config = json_config if isinstance(json_config, unicode) else json_config.decode('utf-8-sig')
        return json_config
    return None


# 配置文件合并到资源文件中, 返回可存储的上传对象
def merge_config_to_file(zip_file, json_config):
    json_config = json.dumps(json.loads(json_config), ensure_ascii=False, sort_keys=True, indent=4).encode('utf-8')
    zip_file.seek(0)
    ziper = Ziper(zip_file.read())
    ziper.add(api_settings.CONFIG_FILE_NAME, json_config)
    merged_zip_content = ziper.read()
    merged_zip = InMemoryUploadedFile(
        BytesIO(merged_zip_content),
        'file',
        '%s.zip' % uuid.uuid4(),
        'application/zip',
        len(merged_zip_content),
        None,
        {}
    )
    return merged_zip


# 解压环境文件
def extract_env_file(env):
    if not env.file:
        return None
    extract_path = get_extract_path(env)
    try:
        if os.path.exists(extract_path):
            shutil.rmtree(extract_path)
        os.makedirs(extract_path)
        zf = zipfile.ZipFile(env.file)
        zf.extractall(extract_path)
    except Exception as e:
        logger.error('extract env[%s] file error: %s', env.pk, e)
        return False

    return True

def get_extract_path(env):
    return os.path.join(api_settings.EXTRACT_PATH, str(env.pk))


def dump_env(queryset):
    dumper = Dumper(queryset)
    filename = 'env_{}.zip'.format(timezone.now().strftime('%Y%m%d%H%M%S'))
    file_path = dumper.dumps(filename)
    return file_path


def load_env(filename):
    path = os.path.join(resource_api_settings.LOAD_TMP_DIR, filename)
    loader = Loader()
    loader.loads(path)
