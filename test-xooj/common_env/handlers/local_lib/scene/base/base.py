# -*- coding: utf-8 -*-


# 场景资源类
class Resource(object):

    def get(self, *args, **kwargs):
        raise NotImplementedError('subclasses of Resource must provide a get() method')

    def create(self, *args, **kwargs):
        raise NotImplementedError('subclasses of Resource must provide a create() method')

    def update(self, *args, **kwargs):
        raise NotImplementedError('subclasses of Resource must provide a update() method')

    def delete(self, *args, **kwargs):
        raise NotImplementedError('subclasses of Resource must provide a delete() method')
