# -*- coding: utf-8 -*-

from django.db.models.base import ModelBase
from django.utils import six

from .meta import ResourceOption


resource_classes = set()


# model 资源表元类
class ResourceBase(ModelBase):
    def __new__(cls, name, bases, attrs):
        super_new = super(ResourceBase, cls).__new__

        parents = [b for b in bases if isinstance(b, ResourceBase)]
        if not parents:
            return super_new(cls, name, bases, attrs)

        new_class = super_new(cls, name, bases, attrs)
        if new_class._meta.abstract:
            return new_class

        # 解析资源配置选项
        meta = getattr(new_class, 'ResourceMeta', None)
        new_class._resource_meta = ResourceOption(new_class, meta)

        resource_classes.add(new_class)
        return new_class


# model 资源表父类
class Resource(six.with_metaclass(ResourceBase)):
    pass

