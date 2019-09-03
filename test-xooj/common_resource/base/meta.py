# -*- coding: utf-8 -*-

from django.db.models import Model, QuerySet

from common_framework.utils.enum import enum

from .exception import ResourceException
from .utils import try_import


# 解决冲突方案 0抛异常 1替换为冲突对象 2覆盖冲突对象 3忽略冲突
RESOLVE_CONFLICT_TYPE = enum(
    RAISE=0,
    REPLACE=1,
    COVER=2,
    IGNORE=3,
)


# 资源检查选项
class CheckOption(object):
    def __init__(self, cls, root_model=None, **kwargs):
        # 资源表
        self.model = cls
        # 所属的根资源表
        self.root_model = root_model

        # 获取冲突对象方法
        self.get_conflict_obj = kwargs.get('get_conflict_obj', None)
        # 解决冲突方案
        self.resolve_conflict_type = kwargs.get('resolve_conflict_type', RESOLVE_CONFLICT_TYPE.REPLACE)
        # 冲突替换检查
        self.conflict_consistency_check = kwargs.get('conflict_consistency_check', None)


# 资源向上所属的配置选项
class BelongOption(object):
    def __init__(self, cls, root_model, parent_model, **kwargs):
        # 资源表
        self.model = cls
        # 所属的根资源表
        self.root_model = root_model
        # 所属的父资源表
        self.parent_model = parent_model

        # 获取资源的方法
        get = kwargs.get('get', lambda model, obj: model.objects.filter(pk__in=[]))
        self.get = lambda obj: get(self.model, obj)

        # 设置资源关联字段
        self.set = kwargs.get('set', None)


# 资源向上附属或向下拥有的配置选项
class SubsidiaryOption(object):
    def __init__(self, cls, root_model=None, **kwargs):
        # 资源表
        self.model = cls
        # 所属的根资源表, 可为空
        self.root_model = root_model
        # 强制设置字段
        self.force = kwargs.get('force', {})
        # 强制需要读取的字段
        self.markdownfields = kwargs.get('markdownfields',[])
        # 附属资源字段 key资源字段名称 value获取/设置该资源的方法
        self.subsidiary = kwargs.get('subsidiary', {})
        self.normal = {}
        self.many_to_many = {}
        for field_name, operation in self.subsidiary.items():
            if operation.get('many_to_many'):
                self.many_to_many[field_name] = operation
            else:
                self.normal[field_name] = operation

    def get_subsidiary(self, obj):
        subsidiary = {}
        for field_name, operation in self.subsidiary.items():
            res = operation['get'](obj)
            if res and not isinstance(res, (Model, QuerySet)):
                raise ResourceException('Unexcepted subsidiary resource type: %s' % type(res))

            if isinstance(res, QuerySet):
                res = list(res)

            subsidiary[field_name] = res
        return subsidiary


class ResourceOption(object):
    def __init__(self, cls, meta=None):
        # 解析fields, pk不可移除
        fields_map = {field.name: field for field in cls._meta.fields}
        field_names = getattr(meta, 'fields', fields_map.keys())
        # 过滤不序列化的字段
        exclude_field_names = getattr(meta, 'exclude_fields', ())
        serialize_field_names = set(field_names) - set(exclude_field_names)
        self.fields = [fields_map[field_name] for field_name in serialize_field_names]
        # 反序列化字段去除默认主键id, 如有需求再扩展
        deserialize_field_names = serialize_field_names - {'id'}
        self.data_fields = [fields_map[field_name] for field_name in deserialize_field_names]

        # 初始化所有子资源, 只有根资源有
        self.root_own = []
        # 初始化直接子资源
        self.children = {}
        # 初始化belong关系
        self.belong = {}
        # 初始化直接附属资源
        self.subsidiary = {}

        # 解析资源属于谁
        belong_to = getattr(meta, 'belong_to', ())
        for parent in belong_to:
            # 所属根资源表
            root_model = try_import(parent['root'])
            if not hasattr(root_model, '_resource_meta'):
                raise ResourceException('model %s is not resource model' % parent['root'])

            # 所属父资源表
            parent_model = try_import(parent['parent'])
            if not hasattr(parent_model, '_resource_meta'):
                raise ResourceException('model %s is not resource model' % parent['parent'])

            # 解析belong选项
            belong_option = BelongOption(cls, root_model, parent_model, **parent)
            # 根资源root_own添加子资源选项
            root_model._resource_meta.root_own.append(belong_option)
            # 父资源root_own添加子资源选项
            parent_model._resource_meta.add_chidren(belong_option)
            self.set_belong(belong_option)

        # 解析资源拥有谁
        subsidiary = getattr(meta, 'subsidiary', ())
        for sub in subsidiary:
            # 所属根资源表, 拥有的资源可以无所属根资源作为默认拥有资源
            root_model = try_import(sub.get('root', None))
            if root_model and not hasattr(root_model, '_resource_meta'):
                raise ResourceException('model %s is not resource model' % sub['root'])

            subsidiary_option = SubsidiaryOption(cls, root_model, **sub)
            if root_model:
                root_model._resource_meta.root_own.append(subsidiary_option)
            self.set_subsidiary(subsidiary_option)

        # 解析检查选项
        self.check = {}
        check = getattr(meta, 'check', ())
        for check_conf in check:
            # 所属根资源表, 可以无所属根资源作为默认检查选项
            root_model = try_import(check_conf.get('root', None))
            if root_model and not hasattr(root_model, '_resource_meta'):
                raise ResourceException('model %s is not resource model' % check_conf['root'])

            check_option = CheckOption(cls, root_model, **check_conf)
            self.set_check(check_option)

    # 根资源表的唯一映射, 表名
    def generate_root_model_key(self, root_model=None):
        return root_model._meta.db_table if root_model else '_default'

    # 父资源表的唯一映射, 表名
    def generate_root_parent_model_key(self, root_model, parent_model):
        return '%s:%s' % (root_model._meta.db_table, parent_model._meta.db_table)

    def add_chidren(self, belong_option):
        root_model_key = self.generate_root_model_key(belong_option.root_model)
        self.children.setdefault(root_model_key, []).append(belong_option)

    def get_children(self, root_model):
        root_model_key = self.generate_root_model_key(root_model)
        return self.children.get(root_model_key, [])

    def set_belong(self, belong_option):
        parent_model_key = self.generate_root_parent_model_key(belong_option.root_model, belong_option.parent_model)
        self.belong[parent_model_key] = belong_option

    def get_belong(self, root_model, parent_model):
        parent_model_key = self.generate_root_parent_model_key(root_model, parent_model)
        return self.belong.get(parent_model_key, None)

    def set_subsidiary(self, subsidiary_option):
        root_model_key = self.generate_root_model_key(subsidiary_option.root_model)
        self.subsidiary[root_model_key] = subsidiary_option

    def get_subsidiary(self, root_model=None):
        root_model_key = self.generate_root_model_key(root_model)
        subsidiary = self.subsidiary.get(root_model_key, None)
        # 如果根据根资源表找不到对应的拥有资源，寻找默认的拥有资源
        if root_model and not subsidiary:
            subsidiary = self.subsidiary.get(self.generate_root_model_key(), None)
        return subsidiary

    def set_check(self, check_option):
        root_model_key = self.generate_root_model_key(check_option.root_model)
        self.check[root_model_key] = check_option

    def get_check(self, root_model=None):
        root_model_key = self.generate_root_model_key(root_model)
        check = self.check.get(root_model_key, None)
        # 如果根据根资源表找不到对应的检查选项，寻找默认的检查选项
        if root_model and not check:
            check = self.check.get(self.generate_root_model_key(), None)
        return check



