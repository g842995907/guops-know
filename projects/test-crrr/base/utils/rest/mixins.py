# -*- coding: utf-8 -*-

import copy
import json
import logging

from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models.sql.datastructures import EmptyResultSet
from django.utils import six
from django.db import models
from django.utils.module_loading import import_string

from rest_framework import exceptions, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response

from base.utils.cache import CacheProduct, delete_cache
from base.utils.text import md5
from base.utils.rest.pagination import VueTablePagination, CacheVueTablePagination
from base.utils.rest.request import RequestData
from system.models import OperationLog

logger = logging.getLogger(__name__)


class PMixin(object):

    pagination_class = VueTablePagination

    def initial(self, request, *args, **kwargs):
        self.query_data = RequestData(request, is_query=True)
        self.shift_data = RequestData(request, is_query=False)
        self.query_data_fields = self.query_data.getlist('_fields')
        super(PMixin, self).initial(request, *args, **kwargs)

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        context = self.get_serializer_context()
        kwargs['context'] = context
        if self.query_data_fields:
            kwargs['fields'] = self.query_data_fields
        return serializer_class(*args, **kwargs)


def _generate_cache_key(view, queryset):
    view_name = view.__class__.__name__
    try:
        key_str = queryset.query.__str__()
    except EmptyResultSet:
        key_str = 'EmptyResultSet'

    query_data_fields = getattr(view, 'query_data_fields', [])
    query_data_fields.sort()
    key_str = '%s:%s' % (key_str, md5(json.dumps(query_data_fields)))

    cache_key_prefix = view.get_cache_key_prefix()
    if cache_key_prefix is not None:
        key_str = '%s:%s' % (cache_key_prefix, key_str)

    return md5('%s:%s' % (view_name, key_str))


def _generate_cache_view_name(view_cls):
    return "%s-%s" % (view_cls.__module__, view_cls.__name__)


class CacheModelMixin(object):
    pagination_class = CacheVueTablePagination
    page_cache = True

    def __new__(cls, *args, **kwargs):
        obj = super(CacheModelMixin, cls).__new__(cls)
        view_name = _generate_cache_view_name(cls)
        obj.cache = CacheProduct(view_name)

        return obj

    def _default_generate_cache_key(self):
        return _generate_cache_key(self, self.paginator.page_queryset)

    def _default_generate_count_cache_key(self):
        return _generate_cache_key(self, self.paginator.queryset)

    def get_cache_key_prefix(self):
        return None

    def get_cache_flag(self):
        return settings.ENABLE_API_CACHE and getattr(self, 'page_cache', False)

    def get_cache_key(self):
        if not hasattr(self, 'generate_cache_key'):
            return self._default_generate_cache_key()
        return self.generate_cache_key()

    def get_cache_age(self):
        return getattr(self, 'page_cache_age', settings.DEFAULT_CACHE_AGE)

    def clear_cache(self):
        delete_cache(self.cache)
        if hasattr(self, 'related_cache_classes'):
            self.clear_cls_cache(self.related_cache_classes)

    @classmethod
    def clear_self_cache(cls):
        cls.clear_cls_cache(cls)
        if hasattr(cls, 'related_cache_classes'):
            cls.clear_cls_cache(cls.related_cache_classes)

    @staticmethod
    def clear_cls_cache(cls):
        if not isinstance(cls, (list, tuple)):
            cls = [cls]
        for c in cls:
            if isinstance(c, (six.string_types, six.text_type)):
                try:
                    c = import_string(c)
                except Exception:
                    continue
            cache_view_name = _generate_cache_view_name(c)
            cache = CacheProduct(cache_view_name)
            delete_cache(cache)

    def paginate_queryset_flag(self, queryset):
        return self.paginator.paginate_queryset_flag(queryset, self.request, view=self)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        paginate_queryset_flag = self.paginate_queryset_flag(queryset)
        if paginate_queryset_flag:
            if self.get_cache_flag():
                cache_value = self.cache.get(self.cache_key)
                if cache_value:
                    data = cache_value
                else:
                    data = self._get_list_data(queryset)
                    self.cache.set(self.cache_key, data, self.get_cache_age())
            else:
                data = self._get_list_data(queryset)
        else:
            data = []
        return self.get_paginated_response(data)

    def _get_list_data(self, queryset):
        page = self.paginate_queryset(queryset)
        data = self.get_serializer(page, many=True).data
        data = self.extra_handle_list_data(data)
        return data

    def extra_handle_list_data(self, data):
        return data

    def perform_create(self, serializer):
        if self.sub_perform_create(serializer):
            self.clear_cache()

    def perform_update(self, serializer):
        if self.sub_perform_update(serializer):
            self.clear_cache()

    def perform_destroy(self, instance):
        if self.sub_perform_destroy(instance):
            self.clear_cache()

    def sub_perform_create(self, serializer):
        super(CacheModelMixin, self).perform_create(serializer)
        return True

    def sub_perform_update(self, serializer):
        super(CacheModelMixin, self).perform_update(serializer)
        return True

    def sub_perform_destroy(self, instance):
        super(CacheModelMixin, self).perform_destroy(instance)
        return True


class DestroyModelMixin(mixins.DestroyModelMixin):

    def perform_destroy(self, instance):
        if self.sub_perform_destroy(instance) and hasattr(self, 'clear_cache'):
            self.clear_cache()

    def sub_perform_destroy(self, instance):
        instance.status = instance.Status.DELETE
        instance.save()
        return True

    @action(methods=['delete'], detail=False)
    def batch_destroy(self, request):
        ids = self.shift_data.getlist('ids', int)
        if not ids:
            return Response(status=status.HTTP_204_NO_CONTENT)

        queryset = self.queryset.filter(id__in=ids)
        if self.perform_batch_destroy(queryset) and hasattr(self, 'clear_cache'):
            self.clear_cache()

        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_batch_destroy(self, queryset):
        if queryset.update(status=queryset.model.Status.DELETE) > 0:
            return True
        return False


class BatchSetModelMixin(object):

    batch_set_fields = {}

    @action(methods=['patch'], detail=False)
    def batch_set(self, request):
        ids = self.shift_data.getlist('ids', int)
        if not ids:
            return Response(status=status.HTTP_200_OK)

        field = self.shift_data.get('field')
        if field not in self.batch_set_fields:
            raise exceptions.PermissionDenied()

        filter_config = self.batch_set_fields[field]
        allow_null = False
        if isinstance(filter_config, dict):
            filter_params = filter_config.get('filter')
            allow_null = filter_config.get('null')
        else:
            filter_params = filter_config
        value = self.shift_data.get('value', filter_params)
        if value is None and not allow_null:
            raise exceptions.PermissionDenied()

        queryset = self.queryset.filter(id__in=ids)
        if self.perform_batch_set(queryset, field, value) and hasattr(self, 'clear_cache'):
            self.clear_cache()

        return Response(status=status.HTTP_200_OK)

    def perform_batch_set(self, queryset, field, value):
        if queryset.update(**{field: value}) > 0:
            return True
        return False


class PublicModelMixin(object):
    @action(methods=['patch'], detail=False)
    def batch_public(self, request):
        ids = self.shift_data.getlist('ids', int)
        if not ids:
            return Response(status=status.HTTP_204_NO_CONTENT)

        public = self.shift_data.get('public', int) or 0

        queryset = self.queryset.filter(id__in=ids)
        if hasattr(self, 'clear_cache') and self.perform_batch_public(queryset, public):
            self.clear_cache()

        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_batch_public(self, queryset, public):
        if queryset.update(public=public) > 0:
            return True
        return False


class RecordMixin(object):
    def _get_module(self):
        from system.utils.module import get_app_name
        from system.utils.module import get_module

        app_name = get_app_name(self)

        module_name = get_module(app_name)
        if not module_name:
            logger.error('[%s] has no module name', app_name)

        return app_name, module_name

    def perform_create(self, serializer):
        if self.sub_perform_create(serializer):
            self.clear_cache()

            try:
                instance = serializer.instance
                app_name, module_name = self._get_module()

                from system.utils.logset import add_operate_log
                content = None

                if hasattr(self, 'serializer_class'):
                    try:
                        data_dict = self.serializer_class(instance).data
                        if data_dict:
                            content = json.dumps(data_dict, cls=DjangoJSONEncoder)
                    except Exception as e:
                        logger.warning('serialier instace error instance[%s]', str(instance))

                add_operate_log(self.request.user, module_name.get('id'), content, instance.id, str(instance))

            except Exception as e:
                logger.error("RecordMixin perform create exception msg[%s]", str(e))
                raise exceptions.ValidationError({'module': 'error'})

    def perform_update(self, serializer):
        old_instance = copy.deepcopy(serializer.instance)
        if self.sub_perform_update(serializer):
            self.clear_cache()

            new_instance = serializer.instance

            modify_list = self._get_modify_filed(old_instance, new_instance)

            # 修改的值用json表示
            content = json.dumps(modify_list, ensure_ascii=False)

            app_name, module_name = self._get_module()
            from system.utils.logset import add_operate_log

            add_operate_log(self.request.user, module_name.get('id'), content,
                            new_instance.id, str(new_instance),
                            operation_type=OperationLog.OType.UPDATE,
                            )

    def _get_modify_filed(self, old, new):
        if type(old) != type(new):
            logger.error("RecordMixin perform update get_modify_filed exception, new[%s] old[%s]", type(new), type(old))
            return

        modify_list = []
        _fields = new._meta.concrete_fields
        ignore_fields = ['id', 'create_time', 'update_time', 'last_edit_time']

        for field in _fields:
            field_name = field.attname
            if field_name in ignore_fields:
                continue

            origin_value = self._get_field_serializable_value(old, field)
            new_value = self._get_field_serializable_value(new, field)

            if origin_value != new_value:
                modify_list.append({'field': field_name, 'old_value': origin_value, 'new_value': new_value})

        return modify_list

    def _get_field_serializable_value(self, obj, field):
        if isinstance(field, (
                models.DateField,
                models.DateTimeField
        )):
            value = field.value_to_string(obj) if obj.serializable_value(field.attname) is not None else None
        # 文件字段解析出文件路径待处理
        elif isinstance(field, (
                models.FileField,
                models.ImageField
        )):
            real_file = obj.serializable_value(field.attname)
            value = real_file.name
        else:
            value = obj.serializable_value(field.attname)
        return value

    @action(methods=['delete'], detail=False)
    def batch_destroy(self, request):
        ids = self.shift_data.getlist('ids', int)
        if not ids:
            return Response(status=status.HTTP_204_NO_CONTENT)

        queryset = self.queryset.filter(id__in=ids)
        app_name, module_name = self._get_module()

        from system.utils.logset import add_operate_log
        for q in queryset:
            add_operate_log(self.request.user, module_name.get('id'), None,
                            q.id, str(q),
                            operation_type=OperationLog.OType.DELETE,
                            )

        if hasattr(self, 'clear_cache') and self.perform_batch_destroy(queryset):
            self.clear_cache()

        return Response(status=status.HTTP_204_NO_CONTENT)
