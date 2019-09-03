# -*- coding: utf-8 -*-
import base64
import json
import os
import uuid
import logging

from django.core.files import File
from django.http import StreamingHttpResponse
from rest_framework import filters, viewsets, exceptions, response
from rest_framework.decorators import detail_route, list_route
from rest_framework.permissions import IsAuthenticated

from common_cloud import models as cloud_models
from common_cloud.cms import serializers
from common_cloud.response import TaskCategoryError
from common_framework.utils import views as default_views
from common_framework.utils import x_rsa
from common_framework.utils.constant import Status
from common_framework.utils.license import License
from common_framework.utils.rest import mixins as common_mixins
from common_framework.utils.rest.request import RequestData
from common_framework.utils.zip import ZFile
from oj import settings

from common_cloud.setting import api_settings

logger = logging.getLogger(__name__)


class DepartmentViewSet(common_mixins.RequestDataMixin,
                        common_mixins.CacheModelMixin,
                        common_mixins.DestroyModelMixin,
                        viewsets.ModelViewSet):
    queryset = cloud_models.Department.objects.filter(status=Status.NORMAL)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.DepartmentSerializer
    related_cache_class = ()

    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    ordering_fields = ('id',)
    ordering = ('-id',)
    search_fields = ('name',)

    def sub_perform_create(self, serializer):
        name = serializer.validated_data['name']
        if cloud_models.Department.objects.filter(name=name).exclude(status=Status.DELETE):
            raise exceptions.ValidationError({'name': [TaskCategoryError.NAME_HAVE_EXISTED]})

        # if not api_settings.USE_SAME_KEY:
        #     team_key_dir = os.path.join('/tmp', 'key', name)
        #
        #     if os.path.exists(team_key_dir):
        #         team_key_dir = os.path.join('/tmp', 'key', 'name' + str(uuid.uuid4()))
        #     key_path = os.path.join('/tmp', 'key')
        #     if not os.path.exists(key_path):
        #         os.mkdir(key_path)
        #
        #     os.mkdir(team_key_dir)
        #
        #     private_key_path = os.path.join(team_key_dir, 'private_key')
        #     public_key_path = os.path.join(team_key_dir, 'public_key')
        #
        #     x_rsa.generate_key_file(private_key_path, public_key_path)
        #
        #     private_key = open(private_key_path, 'r')
        #     public_key = open(public_key_path, 'r')
        #
        #     file_private = File(private_key)
        #     file_public = File(public_key)
        #     file_private.name = name + '_private_key'
        #     file_public.name = name + '_public_key'
        #
        #     serializer.save(
        #         private_key=file_private,
        #         public_key=file_public,
        #     )
        #
        #     private_key.close()
        #     public_key.close()
        #     file_private.close()
        #     file_public.close()
        # else:
        #     private_key_path = os.path.join(settings.MEDIA_ROOT, 'key', 'private_key')
        #     public_key_path = os.path.join(settings.MEDIA_ROOT, 'key', 'public_key')
        #
        #     if not os.path.exists(private_key_path) or not os.path.exists(public_key_path):
        #         x_rsa.generate_key_file(private_key_path, public_key_path)
        #
        #     serializer.save(
        #         private_key='key/private_key',
        #         public_key='key/public_key',
        #     )
        serializer.save()
        return True

    def sub_perform_destroy(self, instance):
        instance.status = Status.DELETE
        instance.save()
        return True

    @detail_route(methods=['get'], )
    def license(self, request, pk):
        department = cloud_models.Department.objects.get(pk=pk)

        encrypt_full_path = License.genera_license_file(department)
        if encrypt_full_path is None:
            raise exceptions.NotFound("some thing error")

        _ret_response = StreamingHttpResponse(file_iterator(encrypt_full_path))
        _ret_response['Content-Type'] = 'application/octet-stream'
        _ret_response['Content-Disposition'] = 'attachment;filename="license"'
        _ret_response['Content-Length'] = os.path.getsize(encrypt_full_path)

        return _ret_response

    @list_route(methods=['get'])
    def get_hardware_info(self, request):
        hex_encrypt_info = str(self.query_data.get('encrypt'))
        if hex_encrypt_info is None or len(hex_encrypt_info) == 0:
            return response.Response({"encrypt": "error"})

        try:
            # hex -> string
            encrypt_info = hex_encrypt_info.decode('hex')
            info_key_file_path = os.path.join(settings.MEDIA_ROOT, 'key/info/key.pem')

            # encrypt -> string
            string_base_info = x_rsa.rsa_decrypt(info_key_file_path, encrypt_info)

            # string -> load
            dict_base_info = json.loads(string_base_info)
        except Exception as e:
            logger.error("json loads error. msg[%s]", str(e))
            return response.Response({"encrypt": "error"})

        return response.Response(dict_base_info)


def file_iterator(file_name, chunk_size=512):
    with open(file_name) as f:
        while True:
            c = f.read(chunk_size)
            if c:
                yield c
            else:
                break


class UpdateViewSet(common_mixins.CacheModelMixin,
                    common_mixins.DestroyModelMixin,
                    viewsets.ModelViewSet):
    queryset = cloud_models.UpdateInfo.objects.filter(status=Status.NORMAL)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.UpdateSerializer
    related_cache_class = ()

    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    ordering_fields = ('id',)
    ordering = ('-id',)
    search_fields = ('name',)

    def sub_perform_create(self, serializer):
        name = serializer.validated_data['name']
        if cloud_models.UpdateInfo.objects.filter(name=name).exclude(status=Status.DELETE):
            raise exceptions.ValidationError({'name': [TaskCategoryError.NAME_HAVE_EXISTED]})
        serializer.save()
        return True

    def sub_perform_destroy(self, instance):
        instance.status = Status.DELETE
        instance.save()
        return True

    @detail_route(methods=['get'], )
    def down_zip(self, request, pk):
        update = cloud_models.UpdateInfo.objects.get(id=pk)

        data = RequestData(self.request, is_query=True)
        depart = data.get('department', str)
        if depart is None or len(depart) == 0:
            return default_views.Http404Page(request, Exception())

        departments = depart.split(",")
        encrypt_file_list = []
        for department in departments:
            department = cloud_models.Department.objects.get(id=department)

            # 查找有没有加密过的更新包
            encrypt_path = update.zip.path + "_%s.%s" % (department.name, 'encrypt')

            if not os.path.exists(encrypt_path):
                x_rsa.x_encrypt(update.zip.path, encrypt_path, os.path.join(settings.BASE_DIR, "media", "key", "lic", "key_pub.pem"))

            encrypt_file_list.append(encrypt_path)

        encrypt_path = encrypt_file_list[0]
        file_name = ""

        if len(encrypt_file_list) > 1:
            # zip压缩一下
            encrypt_path = "/tmp/%s.zip" % str(uuid.uuid4())
            z = ZFile(encrypt_path, 'w')
            for efile in encrypt_file_list:
                z.addfile(efile, efile[efile.rfind('/') + 1:])
            z.close()

            file_name = "%s.zip" % depart
        else:
            file_name = "%s.encrypt" % department.name.encode("utf-8")

        response = StreamingHttpResponse(file_iterator(encrypt_path))
        response['Content-Type'] = 'application/octet-stream'
        response['Content-Disposition'] = 'attachment;filename="{0}"'.format(file_name)

        return response


class LicenseConfigViewSet(common_mixins.CacheModelMixin, viewsets.ReadOnlyModelViewSet):
    queryset = cloud_models.LicenseConfig.objects.all()
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.LicenseConfigSerializer
