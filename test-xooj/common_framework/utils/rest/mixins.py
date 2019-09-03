# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import copy
import hashlib
import json

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models
from django.db import transaction
from django.db.models.sql.datastructures import EmptyResultSet
from django.utils import six
from django.utils.module_loading import import_string
from rest_framework import mixins, status, exceptions
from rest_framework.decorators import list_route, detail_route
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from common_auth import api as auth_api
from common_auth import models as auth_model
from common_framework.models import Builtin, AuthAndShare
from common_framework.utils.enum import enum
from common_framework.utils.cache import CacheProduct, delete_cache
from common_framework.utils.constant import Status
from common_framework.utils.rest.pagination import BootstrapPagination
from common_framework.utils.rest.request import RequestData
from common_framework.utils.x_logger import get_x_logger
from system_configuration.models import OperationLog

logger = get_x_logger(__name__)

AuthType = enum(
    FACULTY=2,
    MAJOR=3,
    CLASSES=4
)


class RequestDataMixin(object):
    def initial(self, request, *args, **kwargs):
        super(RequestDataMixin, self).initial(request, *args, **kwargs)
        self.query_data = RequestData(request, is_query=True)
        self.shift_data = RequestData(request, is_query=False)


def _generate_cache_key(view, queryset):
    view_name = view.__class__.__name__
    try:
        key_str = queryset.query.__str__()
    except EmptyResultSet as e:
        # 无查询的空对象
        key_str = 'EmptyResultSet'

    cache_key_prefix = view.get_cache_key_prefix()
    if cache_key_prefix is not None:
        key_str = '%s:%s' % (cache_key_prefix, key_str)

    return hashlib.md5('%s:%s' % (view_name, key_str.encode('utf-8'))).hexdigest()


def _generate_cache_view_name(view_cls):
    return "%s-%s" % (view_cls.__module__, view_cls.__name__)


class CacheModelMixin(object):
    pagination_class = BootstrapPagination
    page_cache = True

    def __new__(cls, *args, **kwargs):
        obj = super(CacheModelMixin, cls).__new__(cls, *args, **kwargs)
        view_name = _generate_cache_view_name(cls)
        obj.cache = CacheProduct(view_name)

        return obj

    # def __init__(self, *args, **kwargs):
    #     self.page_cache = True

    def _default_generate_cache_key(self):
        return _generate_cache_key(self, self.paginator.page_queryset)

    def _default_generate_count_cache_key(self):
        return _generate_cache_key(self, self.paginator.queryset)

    def get_cache_key_prefix(self):
        return None

    def get_cache_flag(self):
        return getattr(self, 'page_cache', False)

    def get_cache_key(self):
        if not hasattr(self, 'generate_cache_key'):
            return self._default_generate_cache_key()
        return self.generate_cache_key()

    def get_cache_age(self):
        return getattr(self, 'page_cache_age', settings.DEFAULT_CACHE_AGE)

    def clear_cache(self):
        # 暂时删除所有缓存
        from django.core.cache import cache
        cache.clear()

        delete_cache(self.cache)
        if hasattr(self, 'related_cache_class'):
            self.clear_cls_cache(self.related_cache_class)

    @classmethod
    def clear_self_cache(cls):
        cls.clear_cls_cache(cls)

    @staticmethod
    def clear_cls_cache(cls):
        # 暂时删除所有缓存
        from django.core.cache import cache
        cache.clear()

        if not isinstance(cls, (list, tuple)):
            cls = [cls]
        for c in cls:
            if isinstance(c, (six.string_types, six.text_type)):
                try:
                    c = import_string(c)
                except:
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
        instance.status = Status.DELETE
        instance.save()
        if hasattr(self, 'clear_cache'):
            self.clear_cache()

    @list_route(methods=['delete'], )
    def batch_destroy(self, request):
        ids = request.data.getlist('ids', [])
        if not ids:
            return Response(status=status.HTTP_204_NO_CONTENT)

        queryset = self.queryset.filter(id__in=ids)
        if hasattr(self, 'clear_cache') and self.perform_batch_destroy(queryset):
            self.clear_cache()

        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_batch_destroy(self, queryset):
        instance_model = self.queryset.model
        if issubclass(instance_model, Builtin):
            if queryset.filter(builtin=True).exists():
                ignore_fields = instance_model.MyMeta._builtin_modify_field

                if 'status' in ignore_fields:
                    pass
                else:
                    raise PermissionDenied()

        if queryset.update(status=Status.DELETE) > 0:
            return True
        return False


class PublicModelMixin(object):
    @list_route(methods=['patch'], )
    def batch_public(self, request):
        ids = request.data.getlist('ids', [])
        if not ids:
            return Response(status=status.HTTP_204_NO_CONTENT)

        public = int(request.data.get('public', 0))

        queryset = self.queryset.filter(id__in=ids)
        if hasattr(self, 'clear_cache') and self.perform_batch_public(queryset, public):
            self.clear_cache()

        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_batch_public(self, queryset, public):
        if queryset.update(public=public) > 0:
            return True
        return False

    @list_route(methods=['patch'], )
    def batch_public_exercise(self, request):
        ids = request.data.getlist('ids', [])
        if not ids:
            return Response(status=status.HTTP_204_NO_CONTENT)

        public = int(request.data.get('public', 0))

        queryset = self.queryset.filter(id__in=ids)
        if hasattr(self, 'clear_cache') and self.perform_batch_public_exercise(queryset, public):
            self.clear_cache()

        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_batch_public_exercise(self, queryset, public):
        if queryset.update(exercise_public=public) > 0:
            return True
        return False


class ObligatoryModelMixin(object):
    @list_route(methods=['patch'], )
    def batch_obligatory(self, request):
        ids = request.data.getlist('ids', [])
        if not ids:
            return Response(status=status.HTTP_204_NO_CONTENT)

        obligatory = int(request.data.get('obligatory', 0))

        queryset = self.queryset.filter(id__in=ids)
        if hasattr(self, 'clear_cache') and self.perform_batch_obligatory(queryset, obligatory):
            self.clear_cache()

        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_batch_obligatory(self, queryset, obligatory):
        if queryset.update(obligatory=obligatory) > 0:
            return True
        return False


class AuthsMixin(RequestDataMixin):
    @detail_route(methods=['get'], )
    def get_auths(self, request, pk=None):
        faculty = self.query_data.get('faculty', int)
        major = self.query_data.get('major', int)
        auth_type = self.query_data.get('auth_type', int)

        obj = self.get_faculty_major_objs(request, pk)
        if hasattr(obj, "auth"):
            auth = obj.auth
            if auth == AuthAndShare.AuthMode.ALL_AUTH_MODE:
                return Response({'auth_mode': AuthAndShare.AuthMode.ALL_AUTH_MODE})

        if auth_type == AuthType.FACULTY:
            has_auth_class = self.get_faculty_major_objs(request, pk, faculty=faculty, major=major).auth_faculty.all()
            all_auth_class = self.get_all_faculty(request, faculty=faculty, major=major)
        if auth_type == AuthType.MAJOR:
            has_auth_class = self.get_faculty_major_objs(request, pk, faculty=faculty, major=major).auth_major.all()
            all_auth_class = self.get_all_major(request, faculty=faculty, major=major)
        if auth_type == AuthType.CLASSES:
            has_auth_class = self.get_faculty_major_objs(request, pk, faculty=faculty, major=major).auth_classes.all()
            all_auth_class = self.get_all_class(request, faculty=faculty, major=major)

        # 已有权限的对象转为字典
        auth_dict = {}
        for auth in has_auth_class:
            auth_dict[auth.id] = 1

        class Serializer:
            def __init__(self, raw):
                self.data = {
                    'id': raw.id,
                    'name': raw.name,
                    'auth': 0,
                }

                if auth_dict.get(raw.id):
                    self.data['auth'] = 1

        ret = [Serializer(row).data for row in all_auth_class]
        return Response(
            {
                'auth_mode': AuthAndShare.AuthMode.CUSTOM_AUTH_MODE,
                'class': ret
            }
        )

    @detail_route(methods=['get'], )
    def get_all_auth(self, request, pk=None):
        obj = self.get_faculty_major_objs(request, pk)
        if hasattr(obj, "auth"):
            auth = obj.auth
            if auth == AuthAndShare.AuthMode.ALL_AUTH_MODE:
                return Response({'auth_mode': AuthAndShare.AuthMode.ALL_AUTH_MODE})

        has_auth_faculty = self.get_faculty_major_objs(request, pk).auth_faculty.all()
        has_auth_major = self.get_faculty_major_objs(request, pk).auth_major.all()
        has_auth_classes = self.get_faculty_major_objs(request, pk).auth_classes.all()

        class Serializer:
            def __init__(self, row, type):
                self.data = {
                    'id': row.id,
                    'name': row.name
                }
                if type == AuthType.MAJOR:
                    self.data['name'] = row.faculty.name + '/' + row.name
                elif type == AuthType.CLASSES:
                    self.data['name'] = row.major.faculty.name + '/' + row.major.name + '/' + row.name

        ret_faculty = [Serializer(row, AuthType.FACULTY).data for row in has_auth_faculty]
        ret_major = [Serializer(row, AuthType.MAJOR).data for row in has_auth_major]
        ret_classes = [Serializer(row, AuthType.CLASSES).data for row in has_auth_classes]

        return Response(
            {
                'auth_faculty': ret_faculty,
                'auth_major': ret_major,
                'auth_classes': ret_classes,
            }
        )

    def get_all_faculty(self, request, faculty=None, major=None):
        return auth_api.get_faculty()

    def get_all_major(self, request, faculty=None, major=None):
        return auth_api.get_major(faculty=None)

    def get_all_class(self, request, faculty=None, major=None):
        return auth_api.get_all_class(faculty=None, major=major)

    def get_faculty_major_objs(self, request, faculty=None, major=None):
        return []

    def after_set_auth(self, obj, ac_to_add, ac_to_del):
        pass

    @detail_route(methods=['post'], )
    def set_auths(self, request, pk=None):
        auth_mode = self.shift_data.get('auth_mode', int)
        auth_type = self.shift_data.get('auth_type', int)

        obj = self.get_faculty_major_objs(request, pk)
        if hasattr(obj, "auth"):
            obj.auth = auth_mode
            obj.save()

        if auth_mode == AuthAndShare.AuthMode.ALL_AUTH_MODE:
            if hasattr(self, 'clear_cache') and callable(getattr(self, 'clear_cache')):
                self.clear_cache()

            return Response({'auth_class': 'ok'})

        new_auth_classes = request.POST.getlist("auth_classes")
        new_auth_classes = [long(c_id) for c_id in new_auth_classes]
        old_auth_classes = self.get_old_auth_classes(auth_type, obj)
        common_classes = set(new_auth_classes) & set(old_auth_classes)

        ac_to_add = list(set(new_auth_classes) - common_classes)
        ac_to_del = list(set(old_auth_classes) - common_classes)

        for c_id in ac_to_del:
            if auth_type == AuthType.FACULTY:
                _t = auth_model.Faculty.objects.filter(id=c_id).first()
                if _t:
                    obj.auth_faculty.remove(_t)
            if auth_type == AuthType.MAJOR:
                _t = auth_model.Major.objects.filter(id=c_id).first()
                if _t:
                    obj.auth_major.remove(_t)
            if auth_type == AuthType.CLASSES:
                _t = auth_model.Classes.objects.filter(id=c_id).first()
                if _t:
                    obj.auth_classes.remove(_t)

        for c_id in ac_to_add:
            if auth_type == AuthType.FACULTY:
                _t = auth_model.Faculty.objects.filter(id=c_id).first()
                if _t:
                    obj.auth_faculty.add(_t)
            if auth_type == AuthType.MAJOR:
                _t = auth_model.Major.objects.filter(id=c_id).first()
                if _t:
                    obj.auth_major.add(_t)
            if auth_type == AuthType.CLASSES:
                _t = auth_model.Classes.objects.filter(id=c_id).first()
                if _t:
                    obj.auth_classes.add(_t)

        if hasattr(self, 'after_set_auth') and callable(getattr(self, 'after_set_auth')):
            self.after_set_auth(obj, ac_to_add, ac_to_del)

        if hasattr(self, 'clear_cache') and callable(getattr(self, 'clear_cache')):
            self.clear_cache()

        return Response({'auth_class': 'ok'})

    def get_old_auth_classes(self, auth_type, obj):
        if auth_type == AuthType.FACULTY:
            return [ac.id for ac in obj.auth_faculty.all()]
        if auth_type == AuthType.MAJOR:
            return [ac.id for ac in obj.auth_major.all()]
        if auth_type == AuthType.CLASSES:
            return [ac.id for ac in obj.auth_classes.all()]


class ShareTeachersMixin(RequestDataMixin):
    @detail_route(methods=['get'], )
    def get_shares(self, request, pk=None):
        obj = self.get_object()
        if hasattr(obj, "share"):
            share = obj.share
            if share == AuthAndShare.ShareMode.ALL_SHARE_MODE:
                return Response({'share_mode': AuthAndShare.ShareMode.ALL_SHARE_MODE})

        has_share_teachers = obj.share_teachers.all()
        all_share_teachers = self.get_all_teachers()

        # 已有权限的对象转为字典
        share_dict = {}
        for share in has_share_teachers:
            share_dict[share.id] = 1

        class Serializer:
            def __init__(self, raw):
                self.data = {
                    'id': raw.id,
                    'name': raw.first_name,
                    'share': 0,
                }

                if share_dict.get(raw.id):
                    self.data['share'] = 1

        ret = [Serializer(row).data for row in all_share_teachers]
        return Response(
            {
                'share_mode': AuthAndShare.ShareMode.CUSTOM_SHARE_MODE,
                'teachers': ret
            }
        )

    def get_all_teachers(self):
        return auth_api.get_all_teachers()

    def after_set_share(self, obj, ac_to_add, ac_to_del):
        pass

    @detail_route(methods=['post'], )
    def set_shares(self, request, pk=None):
        share_mode = self.shift_data.get('share_mode', int)

        obj = self.get_object()
        if hasattr(obj, "share"):
            obj.share = share_mode
            obj.save()

        if share_mode == AuthAndShare.ShareMode.ALL_SHARE_MODE:
            if hasattr(self, 'clear_cache') and callable(getattr(self, 'clear_cache')):
                self.clear_cache()

            return Response({'share_teacher': 'ok'})

        new_share_teachers = request.POST.getlist("share_teachers")
        new_share_teachers = [long(c_id) for c_id in new_share_teachers]
        old_share_teachers = [ac.id for ac in obj.share_teachers.all()]
        common_teachers = set(new_share_teachers) & set(old_share_teachers)

        ac_to_add = list(set(new_share_teachers) - common_teachers)
        ac_to_del = list(set(old_share_teachers) - common_teachers)

        for c_id in ac_to_del:
            _t = auth_model.User.objects.filter(id=c_id).first()
            if _t:
                obj.share_teachers.remove(_t)

        for c_id in ac_to_add:
            _t = auth_model.User.objects.filter(id=c_id).first()
            if _t:
                obj.share_teachers.add(_t)

        if hasattr(self, 'after_set_share') and callable(getattr(self, 'after_set_share')):
            self.after_set_share(obj, ac_to_add, ac_to_del)

        if hasattr(self, 'clear_cache') and callable(getattr(self, 'clear_cache')):
            self.clear_cache()

        return Response({'share_teacher': 'ok'})


class ActiveModelMixin(object):
    @list_route(methods=['patch'], )
    def batch_active(self, request):
        ids = request.data.getlist('ids', [])
        if not ids:
            return Response(status=status.HTTP_204_NO_CONTENT)

        is_active = int(request.data.get('is_active', 0))

        queryset = self.queryset.filter(id__in=ids)
        if hasattr(self, 'clear_cache') and self.perform_batch_active(queryset, is_active):
            self.clear_cache()

        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_batch_active(self, queryset, is_active):
        if queryset.update(is_active=is_active) > 0:
            return True
        return False


class PromoteTeacherModelMixin(object):
    @list_route(methods=['patch'], )
    def batch_promote(self, request):
        ids = request.data.getlist('ids', [])
        if not ids:
            return Response(status=status.HTTP_204_NO_CONTENT)

        is_teacher = int(request.data.get('is_teacher', 0))

        queryset = self.queryset.filter(id__in=ids)
        if self.perform_batch_active(queryset, is_teacher):
            self.clear_cache()

        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_batch_promote(self, queryset, is_teacher):
        if is_teacher:
            group = Group.objects.filter(id=3)
        else:
            group = Group.objects.filter(id=4)
        with transaction.atomic():
            queryset.update(is_staff=is_teacher, groups=group)
            return True


class RecordMixin(object):
    def _get_module(self, instance):
        from common_framework.utils.app import get_app_name
        from common_product.module import get_module

        app_name = get_app_name(self)

        module_name = get_module(app_name)
        if not module_name:
            logger.error('[%s] has no module name', app_name)
            # raise exceptions.ValidationError({'module': 'error'})

        return app_name, module_name

    def perform_create(self, serializer):
        if self.sub_perform_create(serializer):
            self.clear_cache()

            try:
                instance = serializer.instance
                app_name, module_name = self._get_module(instance)

                from system_configuration.cms.api import add_operate_log
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

            app_name, module_name = self._get_module(new_instance)
            from system_configuration.cms.api import add_operate_log

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

    @list_route(methods=['delete'], )
    def batch_destroy(self, request):
        ids = request.data.getlist('ids', [])
        if not ids:
            return Response(status=status.HTTP_204_NO_CONTENT)

        queryset = self.queryset.filter(id__in=ids)
        app_name, module_name = self._get_module(queryset.model)

        from system_configuration.cms.api import add_operate_log
        for q in queryset:
            add_operate_log(self.request.user, module_name.get('id'), None,
                            q.id, str(q),
                            operation_type=OperationLog.OType.DELETE,
                            )

        if hasattr(self, 'clear_cache') and self.perform_batch_destroy(queryset):
            self.clear_cache()

        return Response(status=status.HTTP_204_NO_CONTENT)
