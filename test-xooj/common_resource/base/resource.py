# -*- coding: utf-8 -*-
import cPickle as pickle
import hashlib
import logging
import os
import re
import shutil
import json
import copy

from django.conf import settings
from django.db import models

from .exception import ResourceException
from .meta import RESOLVE_CONFLICT_TYPE
from common_resource.setting import api_settings
from common_env.models import EnvTerminal

logger = logging.getLogger(__name__)


index_key = '_index'
image_key = 'image'
image_model = EnvTerminal


# 无法序列化需要转换为字符串的字段类型
convert_string_fields = (
    models.DateField,
    models.DateTimeField,
)

# 文件字段类型
file_fields = (
    models.FileField,
    models.ImageField,
)


# 从对象生成资源, 序列化导出数据 不需冲突检查
class ModelResource(object):
    # 资源汇总池
    resource_pool = {}
    # 资源表对应的所有资源
    model_resources = {}
    image_name = set()

    def __new__(cls, obj, root_model):
        # 序列化数据对象模型类
        p_model = pickle.dumps(obj._meta.model)
        # 根据模型类和主键生成资源唯一标识
        p_key = hashlib.md5('%s:%s' % (p_model, obj.pk)).hexdigest()
        # 资源池已有资源直接返回不再新建
        if p_key in cls.resource_pool:
            resource = cls.resource_pool[p_key]
        else:
            resource = super(ModelResource, cls).__new__(cls, obj, root_model)
            # 新建的资源加入资源池和资源表
            cls.resource_pool[p_key] = resource
            cls.model_resources.setdefault(p_model, []).append(resource)

            # 预设置资源的模型和唯一标识
            resource.p_model = p_model
            resource.p_key = p_key
            # 预设置资源为未初始化
            resource._inited = False
        return resource

    # 重置类的资源池
    @classmethod
    def reset(cls):
        cls.resource_pool = {}
        cls.model_resources = {}
        cls.image_name = set()

    def __init__(self, obj, root_model):
        if self._inited:
            return
        # 初始化对象属性
        self.obj = obj
        self.model = obj._meta.model
        self.fields = obj._resource_meta.fields

        # 初始化对象关联属性
        self.root_own = obj._resource_meta.root_own
        self.root_model = self.model if self.root_own else root_model
        self.children = obj._resource_meta.get_children(self.root_model)
        self.subsidiary = obj._resource_meta.get_subsidiary(self.root_model)

        # 初始化对象关联资源
        self.child_resources = []
        self.subsidiary_resources = []
        self.subsidiary_resource = {}

        # 初始化对象序列化数据
        self.data = None
        self.copying_files = {}
        self._parsed = False
        self._dumped = False

        # 标识资源已初始化
        self._inited = True

    # 序列化资源
    def dumps(self):
        # 只序列化一次资源
        if self._dumped:
            return

        # 初始化序列化数据的索引
        data = {index_key:  {
            'model': self.p_model,
            'key': self.p_key,
        }}
        # 序列化数据
        for field in self.fields:
            data[field.attname] = self.get_field_serializable_value(field)
        self.data = data
        image_value = self.data.get('image', None)
        if image_value and isinstance(self.obj, image_model):
            type(self).image_name.add(image_value)

        # 标识资源已序列化
        self._dumped = True

    # 获取资源的关联索引(子资源索引和拥有资源索引)
    def get_relation_index(self):
        children = [resource.p_key for resource in self.child_resources]
        subsidiary = {}
        for field_name, resrc in self.subsidiary_resource.items():
            if isinstance(resrc, list):
                subsidiary[field_name] = [resource.p_key for resource in resrc]
            else:
                subsidiary[field_name] = resrc.p_key if resrc else None
        return {
            'children': children,
            'subsidiary': subsidiary
        }

    @staticmethod
    def find_static_file_from_markdown(content, regx=None):
        if content is None or content == '':
            return []
        findall_statices = re.findall(regx, content)
        return findall_statices

    # 字段序列化
    def get_field_serializable_value(self, field):
        obj = self.obj
        # 强置的字段直接设为强置值
        if self.subsidiary and field.attname in self.subsidiary.force:
            return self.subsidiary.force[field.attname]

        # 设置markdown字段的读取
        if self.subsidiary and field.attname in self.subsidiary.markdownfields:
            markdown_content = obj.serializable_value(field.attname)
            regx_paths = self.find_static_file_from_markdown(content=markdown_content, regx=r'\(/media/(.+?)\)')
            for regx_path in regx_paths:
                self.copying_files[regx_path] = os.path.join(settings.MEDIA_ROOT, regx_path)

        if isinstance(field, convert_string_fields):
            value = field.value_to_string(obj) if obj.serializable_value(field.attname) is not None else None
        # 文件字段解析出文件路径待处理
        elif isinstance(field, file_fields):
            real_file = obj.serializable_value(field.attname)
            value = real_file.name
            if value.startswith('/'):
                value = real_file.name = real_file.name[1:]
            if value:
                # 准备复制文件
                self.copying_files[value] = real_file.path
        else:
            value = obj.serializable_value(field.attname)
        return value

    # 递归解析资源的关联树
    def parse_related_tree(self):
        self._parse_related_tree(self)

    # 判断资源是否有相关资源
    def has_related(self):
        return self.children or self.subsidiary

    # 获取关联资源
    def get_related_resources(self):
        self.get_child_resources()
        self.get_subsidiary_resources()

    # 获取附属子资源
    def get_child_resources(self):
        for child in self.children:
            child_queryset = child.get(self.obj)
            for child_obj in child_queryset:
                child_resource = type(self)(child_obj, self.root_model)
                self.child_resources.append(child_resource)

    # 获取拥有子资源
    def get_subsidiary_resources(self):
        if not self.subsidiary:
            return

        subsidiary = self.subsidiary.get_subsidiary(self.obj)
        for field_name, value in subsidiary.items():
            if isinstance(value, list):
                if value:
                    for obj in value:
                        sub_resource = type(self)(obj, self.root_model)
                        self.subsidiary_resource.setdefault(field_name, []).append(sub_resource)
                        self.subsidiary_resources.append(sub_resource)
                else:
                    self.subsidiary_resource[field_name] = []
            else:
                sub_resource = type(self)(value, self.root_model) if value else None
                self.subsidiary_resource[field_name] = sub_resource
                self.subsidiary_resources.append(sub_resource)

    @staticmethod
    def get_html_static_file(html_path, tmp_dir):
        if not os.path.exists(html_path):
            return
        with open(html_path, 'r') as site_resource_file:
            site_resource_file_in_html_data = site_resource_file.read()
        all_media_files = re.findall('["\']/(media/.+?)["\']', site_resource_file_in_html_data)
        for all_media_file in all_media_files:
            base_media_file = os.path.join(settings.BASE_DIR, all_media_file)
            dst_media_file = os.path.join(tmp_dir, all_media_file)
            mume_config_group = re.search('media/course/html/mume_config/_static/', base_media_file)
            if mume_config_group:
                # 不予copy内置好的静态文件
                continue
            if not os.path.exists(base_media_file):
                continue
            if not os.path.exists(os.path.dirname(dst_media_file)):
                os.makedirs(os.path.dirname(dst_media_file))
            try:
                shutil.copyfile(base_media_file, os.path.join(tmp_dir, all_media_file))
            except Exception as e:
                logger.error('copy file [%s] to [%s] error: %s', html_path, tmp_dir, e)

    # 复制资源关联的文件
    @classmethod
    def copy_files(cls, tmp_dir, copying_files):
        tmp_media_dir = os.path.join(tmp_dir, 'media')
        base_tmp_dir = tmp_dir
        # site_flag = True   # site 文件夹只是拷贝一次

        for dst_file_name, src_file_path in copying_files.items():
            tmp_path = os.path.join(tmp_media_dir, dst_file_name)
            tmp_dir = os.path.dirname(tmp_path)
            if not os.path.exists(tmp_dir):
                os.makedirs(tmp_dir)
            logger.info('copy file [%s] to [%s]', src_file_path, tmp_path)
            # 读取每一个html文件，将里面的资源文件进行copy
            find_site = re.findall('.+?media/course/html/', src_file_path)
            if find_site:
                cls.get_html_static_file(src_file_path, base_tmp_dir)

            # dst_find_site = re.findall('.+?media/course/html/', tmp_path)
            # if find_site and dst_find_site and site_flag:
            #     site_path = os.path.join(find_site[0], 'site')
            #     dst_site_path = os.path.join(dst_find_site[0], 'site')
            #     if os.path.exists(dst_site_path):
            #         shutil.rmtree(dst_site_path)
            #     if os.path.exists(site_path):
            #         shutil.copytree(site_path, dst_site_path)
            #     site_flag = False
            try:
                shutil.copyfile(src_file_path, tmp_path)
            except Exception as e:
                logger.error('copy file [%s] to [%s] error: %s', src_file_path, tmp_path, e)
                continue

    # 递归解析资源的关联树
    @classmethod
    def _parse_related_tree(cls, resource):
        if not resource or resource._parsed or not resource.has_related():
            return

        resource.get_related_resources()

        for child_resource in resource.child_resources:
            cls._parse_related_tree(child_resource)

        for subsidiary_resource in resource.subsidiary_resources:
            cls._parse_related_tree(subsidiary_resource)

        resource._parsed = True


# 从资源生成对象, 反序列化导入数据 需要冲突检查
class DataResource(object):
    resource_pool = {}
    model_resources = {}
    resource_index_pool = {}
    resource_data_pool = {}
    resource_env_attack_defense_obj = []

    def __new__(cls, data, root_model):
        index = data[index_key]
        p_key = index['key']
        # 资源池已有资源直接返回不再新建
        if p_key in cls.resource_pool:
            resource = cls.resource_pool[p_key]
        else:
            resource = super(DataResource, cls).__new__(cls, data, root_model)
            # 新建的资源加入资源池和资源表
            cls.resource_pool[p_key] = resource
            cls.model_resources.setdefault(index['model'], []).append(resource)

            # 预设置资源的模型和唯一标识
            resource.p_model = index['model']
            resource.p_key = p_key
            # 预设置资源为未初始化
            resource._inited = False
        return resource

    def __init__(self, data, root_model):
        if self._inited:
            return

        self.data = data
        self.model = pickle.loads(str(self.p_model))
        self.data_fields = self.model._resource_meta.data_fields

        # 初始化对象关联属性
        self.root_own = self.model._resource_meta.root_own
        # TODO: 拥有的资源是根模型可能会导致问题
        self.root_model = self.model if self.root_own else root_model
        self.children = self.model._resource_meta.get_children(self.root_model)
        self.subsidiary = self.model._resource_meta.get_subsidiary(self.root_model)
        self.check = self.model._resource_meta.get_check(self.root_model)

        # 初始化对象关联资源
        related_index = self.resource_index_pool[self.p_key]
        self.child_index = related_index['children']
        self.subsidiary_index = related_index['subsidiary']

        self.child_resources = []
        self.subsidiary_resources = []
        self.subsidiary_normal_resources = []
        self.subsidiary_many_to_many_resources = []
        self.subsidiary_resource = {}

        # 初始化对象父属者(只能有一个)
        self.parent_resource = None
        # 初始化对象拥有者(可以是多个)
        self.owner_resources = []

        self.obj = None
        self._parsed = False
        self._saved = False

        self._inited = True

    # 重置资源池
    @classmethod
    def reset(cls, resource_index_pool, resource_data_pool):
        cls.resource_pool = {}
        cls.model_resources = {}
        cls.resource_index_pool = resource_index_pool
        cls.resource_data_pool = resource_data_pool
        cls.resource_env_attack_defense_obj = []

    @classmethod
    def parse_model(cls, data):
        index = data[index_key]
        p_model = index['model']
        return pickle.loads(str(p_model))

    def load_data(self):
        data = self.data
        obj = self.model()
        obj._check_builtin = False
        for field in self.data_fields:
            if hasattr(field, 'foreign_related_fields') and field.foreign_related_fields[0].model.__name__ == 'User' \
                    and data[field.attname] is not None:
                data[field.attname] = api_settings.DEFAULT_USER_ID
            setattr(obj, field.attname, data[field.attname])
        self.obj = obj

    def load_parent(self):
        if self.parent_resource:
            parent_obj = self.parent_resource.obj
            belong_option = self.model._resource_meta.get_belong(self.root_model, parent_obj._meta.model)
            if belong_option and belong_option.set:
                belong_option.set(self.obj, parent_obj)

    def load_subsidiary(self, subsidiary_type='normal'):
        if not self.subsidiary:
            return

        for field_name, operation in getattr(self.subsidiary, subsidiary_type).items():
            set = operation.get('set', None)
            if set:
                subsidiary_resource = self.subsidiary_resource[field_name]
                if isinstance(subsidiary_resource, list):
                    subsidiary_obj = [resource.obj for resource in subsidiary_resource]
                else:
                    subsidiary_obj = subsidiary_resource.obj if subsidiary_resource else None

                set(self.obj, subsidiary_obj)

    def change_playlist(self):
        playlist_m3u8 = self.obj.video_change.name
        course_name_json_file = "{}.json".format(self.obj.course.name)
        new_playlist_m3u8 = 'course/video_trans/video_change/' + str(self.obj.id) + '/playlist.m3u8'
        self.obj.video_change = new_playlist_m3u8
        self.obj.save()
        old_course_and_new_course_json_path = os.path.join(api_settings.VIDEO_TRANS, course_name_json_file)
        if not os.path.exists(old_course_and_new_course_json_path):
            os.mknod(old_course_and_new_course_json_path)

        with open(old_course_and_new_course_json_path, "r") as jsonFile:
            try:
                data = json.load(jsonFile)
            except:
                data = {}
        data[playlist_m3u8] = new_playlist_m3u8
        with open(old_course_and_new_course_json_path, 'w') as playlist_m3u8_file:
            json.dump(data, playlist_m3u8_file)

    def checker_obj(self, obj):
        if obj.__class__.__name__ == 'Env' and hasattr(obj, 'is_attack_defense'):
            if getattr(obj, 'is_attack_defense') is True:
                self.resource_env_attack_defense_obj.append(obj)

    # 递归资源的关系导入数据
    def save(self):
        if self._saved:
            return

        # 先导入资源拥有的资源（依赖的资源(非多对多)）
        for subsidiary_resource in self.subsidiary_normal_resources:
            if subsidiary_resource:
                subsidiary_resource.save()

        # 再导入资源本身
        logger.info('save resource[%s]', self.p_key)
        self.load_data()
        self.load_parent()
        self.load_subsidiary('normal')
        self.obj = self.save_obj()
        # if hasattr(self.obj, 'video_change'):
        #     if self.obj.video_change:
        #         self.change_playlist()
        self._saved = True
        self.checker_obj(self.obj)
        # 再导入资源拥有的资源（依赖的资源(多对多)）
        for subsidiary_resource in self.subsidiary_many_to_many_resources:
            if subsidiary_resource:
                subsidiary_resource.save()
        # 保存后设置多对多关系
        self.load_subsidiary('many_to_many')

        # 最后导入资源的子资源（被依赖的资源）
        for child_resource in self.child_resources:
            child_resource.save()

    def save_obj(self):
        check = self.check
        obj = self.obj
        if not check or not check.get_conflict_obj:
            obj.save()
            return obj

        conflict_obj = check.get_conflict_obj(self)
        if conflict_obj:
            # 冲突存在，抛异常
            if check.resolve_conflict_type == RESOLVE_CONFLICT_TYPE.RAISE:
                raise ResourceException('conflict obj exists!')
            # 替换为冲突对象检查(冲突对象可能不一致)
            elif check.resolve_conflict_type == RESOLVE_CONFLICT_TYPE.REPLACE:
                if check.conflict_consistency_check:
                    if check.conflict_consistency_check(obj, conflict_obj):
                        return conflict_obj
                    else:
                        # 替换已有的对象，会造成本地修改的数据消失
                        tmp = copy.copy(obj.__dict__)
                        tmp.pop('id', None)
                        conflict_obj.__dict__.update(tmp)
                        conflict_obj.save()
                        return conflict_obj
                        # raise ResourceException('obj[%s] cannot replace conflict obj[%s], relation inconsistency!' % (obj.__dict__, conflict_obj.__dict__))
                else:
                    return conflict_obj
            # 覆盖冲突对象检查(冲突对象可能不一致) TODO: 可能外键删不掉
            elif check.resolve_conflict_type == RESOLVE_CONFLICT_TYPE.COVER:
                if check.conflict_consistency_check:
                    if check.conflict_consistency_check(obj, conflict_obj):
                        obj.pk = conflict_obj.pk
                        conflict_obj.delete()
                        obj.save()
                        return obj
                    else:
                        raise ResourceException('obj[%s] cannot cover conflict obj[%s], relation inconsistency!' % (obj.__dict__, conflict_obj.__dict__))
                else:
                    obj.pk = conflict_obj.pk
                    conflict_obj.delete()
                    obj.save()
                    return obj
            elif check.resolve_conflict_type == RESOLVE_CONFLICT_TYPE.IGNORE:
                obj.save()
        else:
            obj.save()

        return obj

    def parse_related_tree(self):
        self._parse_related_tree(self)

    # 判断资源是否有相关资源
    def has_related(self):
        return self.child_index or self.subsidiary_index

    # 获取关联资源
    def get_related_resources(self):
        self.get_child_resources()
        self.get_subsidiary_resources()

    # 获取附属子资源
    def get_child_resources(self):
        for child_key in self.child_index:
            child_data = self.resource_data_pool[child_key]
            child_resource = type(self)(child_data, self.root_model)
            if child_resource.parent_resource and child_resource.parent_resource != self:
                raise ResourceException('resource[%s] has more than one parent resource: origin[%s] now[%s]' %
                                        (child_key, child_resource.parent_resource.p_key, self.p_key))
            child_resource.parent_resource = self
            self.child_resources.append(child_resource)

    # 获取拥有子资源
    def get_subsidiary_resources(self):
        for field_name, sub_index in self.subsidiary_index.items():
            if field_name in self.subsidiary.many_to_many:
                collector = self.subsidiary_many_to_many_resources
            else:
                collector = self.subsidiary_normal_resources
            if isinstance(sub_index, list):
                if sub_index:
                    for sub_key in sub_index:
                        sub_data = self.resource_data_pool[sub_key]
                        sub_resource = type(self)(sub_data, self.root_model)
                        sub_resource.owner_resources.append(self)

                        self.subsidiary_resource.setdefault(field_name, []).append(sub_resource)
                        self.subsidiary_resources.append(sub_resource)
                        collector.append(sub_resource)
                else:
                    self.subsidiary_resource[field_name] = []
            else:
                sub_data = self.resource_data_pool[sub_index] if sub_index else None
                sub_resource = type(self)(sub_data, self.root_model) if sub_data else None
                if sub_resource:
                    sub_resource.owner_resources.append(self)

                self.subsidiary_resource[field_name] = sub_resource
                self.subsidiary_resources.append(sub_resource)
                collector.append(sub_resource)

    # 复制资源文件
    @classmethod
    def copy_files(cls, tmp_dir):
        tmp_media_dir = os.path.join(tmp_dir, 'media')
        if not os.path.exists(tmp_media_dir):
            return

        media_dir = settings.MEDIA_ROOT
        pre_len = len(tmp_media_dir)
        for dirpath, dirnames, filenames in os.walk(tmp_media_dir):
            for filename in filenames:
                src_path = os.path.join(dirpath, filename)
                arcname = src_path[pre_len:].strip(os.path.sep)
                dst_path = os.path.join(media_dir, arcname)
                if dst_path.endswith('playlist.m3u8'):
                    # 手动处理该类型的文件
                    continue
                logger.info('copy file [%s] to [%s]', src_path, dst_path)
                dir_dst_path = os.path.dirname(dst_path)
                if not os.path.exists(dir_dst_path):
                    os.makedirs(dir_dst_path)
                try:
                    shutil.copyfile(src_path, dst_path)
                except Exception as e:
                    logger.error('copy file [%s] to [%s] error: %s', src_path, dst_path, e)

    # 递归解析资源的关联树
    @classmethod
    def _parse_related_tree(cls, resource):
        if not resource or resource._parsed or not resource.has_related():
            return

        resource.get_related_resources()

        for child_resource in resource.child_resources:
            cls._parse_related_tree(child_resource)

        for subsidiary_resource in resource.subsidiary_resources:
            cls._parse_related_tree(subsidiary_resource)

        resource._parsed = True
