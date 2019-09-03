# -*- coding: utf-8 -*-

import re
import json
import logging
import os
import shutil

from django.db import transaction
from django.utils.translation import ugettext_lazy as _

from common_framework.utils.unique import generate_unique_key
from common_framework.utils.zip import ZFile
from rest_framework import exceptions
from common_resource.base.resource import ModelResource, DataResource
from common_resource.setting import api_settings
from collections import namedtuple

KlassName = namedtuple('KlassName', ['course', 'practice'])
klass_name = KlassName('Course', 'TaskEvent')

ZIP_WITH_PWD = 'ZIP_WITH_PWD.zip'
ZIP_WITH_PWD_NAME = 'ZIP_WITH_PWD'
PWD = '1786f824c9354bf5a8f269b3b422bb83'

logger = logging.getLogger(__name__)


def jump_out_video(path, condition='course/video/'):
    if re.search(r'{}'.format(condition), path):
        logger.info('Video is not copied !')
        return True
    return False


class Dumper(object):
    def __init__(self, root_queryset):
        # 根资源的queryset
        self.root_queryset = root_queryset
        self.root_model = root_queryset.model
        # 生成资源类
        self.model_resource_class = type('ModelResource', (ModelResource,), {})

        # 初始化根资源索引
        self.resource_root = []
        # 初始化资源关联关系索引
        self.resource_index = {}
        # 初始化资源数据
        self.resource_data = {}
        # 初始化资源关联文件
        self.copying_files = {}

        self.execute_key = generate_unique_key()
        self.tmp_dir = os.path.join(api_settings.DUMP_TMP_DIR, self.execute_key, 'password')
        self.tmp_dir_dirname = os.path.dirname(self.tmp_dir)

    def dumps(self, filename):
        self.model_resource_class.reset()

        for obj in self.root_queryset:
            root_resource = self.model_resource_class(obj, self.root_model)
            self.resource_root.append(root_resource.p_key)
            # 解析根资源的资源关联树, 注满资源池
            root_resource.parse_related_tree()

        # 序列化资源池资源，设置关联关系索引，资源数据，关联文件
        for key, resource in self.model_resource_class.resource_pool.items():
            resource.dumps()
            self.resource_index[key] = resource.get_relation_index()
            self.resource_data[key] = resource.data
            self.copying_files.update(resource.copying_files)

        os.makedirs(self.tmp_dir)
        # 资源索引和数据序列化到临时文件
        with open(os.path.join(self.tmp_dir, 'root.json'), 'w') as root_file:
            # root_file.write(json.dumps(self.resource_root, sort_keys=True, indent=4))
            root_file.write(json.dumps(self.resource_root))
        with open(os.path.join(self.tmp_dir, 'index.json'), 'w') as index_file:
            # index_file.write(json.dumps(self.resource_index, sort_keys=True, indent=4))
            index_file.write(json.dumps(self.resource_index))
        with open(os.path.join(self.tmp_dir, 'data.json'), 'w') as data_file:
            # data_file.write(json.dumps(self.resource_data, ensure_ascii=False, sort_keys=True, indent=4))
            data_file.write(json.dumps(self.resource_data, ensure_ascii=False))
        with open(os.path.join(self.tmp_dir_dirname, 'image.txt'), 'w') as image_file:
            # 导出镜像列表
            image_file.write("\n".join(self.model_resource_class.image_name))

        if len(self.root_queryset) > 0 and self.root_model.__name__ == klass_name.course:
            # 添加 课程README.md
            shutil.copyfile(api_settings.COURSE_README, os.path.join(self.tmp_dir_dirname, 'README.md'))

            filter_video_copy_files = set()
            for copy_key, copy_value in self.copying_files.items():
                if jump_out_video(copy_key):
                    self.copying_files.pop(copy_key)
                    # filter_video_copy_files.add(copy_key)
                elif jump_out_video(copy_key, condition='course/video_trans/video_change/'):
                    self.copying_files.pop(copy_key)
                    filter_video_copy_files.add("/".join(copy_key.split('/')[:4]))
            with open(os.path.join(self.tmp_dir_dirname, 'course_video_trans.txt'), 'w') as video_file:
                video_file.write("\n".join(filter_video_copy_files).encode('utf-8'))
        elif len(self.root_queryset) > 0 and self.root_model.__name__ == klass_name.practice:
            shutil.copyfile(api_settings.PRACTICE_README, os.path.join(self.tmp_dir_dirname, 'README.md'))

        # 复制资源关联文件到临时目录
        logger.info('copy files start')
        self.model_resource_class.copy_files(self.tmp_dir, self.copying_files)
        logger.info('copy files end')

        # 打包
        zip_file_path = os.path.join(api_settings.DUMP_TMP_DIR, filename)  # 终极打包目录
        tmp_zip_file_path = os.path.join(self.tmp_dir_dirname, ZIP_WITH_PWD)  # 临时加密打包目录
        # zip_file = ZFile(zip_file_path, 'w')
        # zip_file.putin(self.tmp_dir)
        logger.info('create zip with password !!!')
        flag = ZFile.putin_with_password(tmp_zip_file_path, self.tmp_dir, PWD)
        if not flag:
            raise ValueError('cmd error in create zip with password')

        shutil.rmtree(self.tmp_dir)

        zip_file = ZFile(zip_file_path, 'w')
        zip_file.putin(self.tmp_dir_dirname)
        zip_file.close()

        # 删除临时目录
        shutil.rmtree(self.tmp_dir_dirname)
        return zip_file_path


class Loader(object):
    def __init__(self):
        # 生成资源类
        self.data_resource_class = type('DataResource', (DataResource,), {})

        self.execute_key = generate_unique_key()
        self.tmp_dir = os.path.join(api_settings.LOAD_TMP_DIR, self.execute_key)
        self.tmp_dir_deep = os.path.join(self.tmp_dir, ZIP_WITH_PWD)
        self.tmp_dir_deep_no_suffix = os.path.join(self.tmp_dir, ZIP_WITH_PWD_NAME)

    def loads(self, path=None, filename=None, mfile=None):
        if not path and not filename and not mfile:
            return
        if path:
            zfile = path
            if not os.path.exists(path):
                return
        elif filename:
            zfile = os.path.join(api_settings.LOAD_TMP_DIR, filename)
            if not os.path.exists(zfile):
                return
        else:
            zfile = mfile
            if not hasattr(zfile, 'read'):
                return

        # 解压数据
        # 第一层解压
        flag = ZFile.extract_to_use_system(
            dir=self.tmp_dir,
            zipFilePath=zfile)
        if not flag:
            raise exceptions.ValidationError(_('x_unzip_fail'))
        # 第二层解压
        flag = ZFile.extract_to_use_system_with_pwd(
            dir=self.tmp_dir_deep_no_suffix,
            zipFilePath=self.tmp_dir_deep,
            pwd=PWD)
        if not flag:
            raise exceptions.ValidationError(_('x_unzip_password_error'))
        # 解析数据
        with open(os.path.join(self.tmp_dir_deep_no_suffix, 'root.json'), 'r') as root_file:
            resource_root = json.loads(root_file.read())
        with open(os.path.join(self.tmp_dir_deep_no_suffix, 'index.json'), 'r') as index_file:
            resource_index = json.loads(index_file.read())
        with open(os.path.join(self.tmp_dir_deep_no_suffix, 'data.json'), 'r') as data_file:
            resource_data = json.loads(data_file.read())

        self.data_resource_class.reset(resource_index, resource_data)

        sample_root_data = resource_data[resource_root[0]]
        root_model = self.data_resource_class.parse_model(sample_root_data)

        # 从根资源解析资源树
        root_resources = []
        for root_key in resource_root:
            root_data = resource_data[root_key]
            resource = self.data_resource_class(root_data, root_model)
            resource.parse_related_tree()
            root_resources.append(resource)

        # 从根资源开始递归导入数据
        with transaction.atomic():
            for root_resource in root_resources:
                logger.info('save root resource[%s] start', root_resource.p_key)
                root_resource.save()
                logger.info('save root resource[%s] end', root_resource.p_key)

        # 复制资源关联文件
        logger.info('copy files start')
        self.data_resource_class.copy_files(self.tmp_dir_deep_no_suffix)
        logger.info('copy files end')

        # 解压攻防文件
        resource_env_attack_defense_obj = self.data_resource_class.resource_env_attack_defense_obj
        if resource_env_attack_defense_obj:
            from common_env.utils.resource import extract_env_file
            for obj in resource_env_attack_defense_obj:
                extract_env_file(obj)

        # 删除临时目录
        shutil.rmtree(self.tmp_dir)
        # 删除上传的压缩包
        os.remove(path)
