# -*- coding: utf-8 -*-
import hashlib
import json
import logging
import time
import uuid

from django.db.models import Q
from django.utils import timezone

from rest_framework import exceptions, filters, status, viewsets
from rest_framework.decorators import list_route, detail_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common_auth.api import oj_share_teacher
from common_framework.utils.delay_task import new_task
from common_framework.utils.network import probe
from common_framework.utils.rest import mixins as common_mixins
from common_framework.utils.rest import filter as common_filters
from common_framework.utils.rest.permission import IsStaffPermission
from common_framework.utils.unique import generate_delete_flag
from common_remote.managers import RemoteManager

from .. import models as env_models
from ..handlers.common import StandardDeviceTmpVmCreater, get_lastest_image_name
from ..handlers.exceptions import MsgException
from ..handlers.local_lib import scene, proxy
from ..handlers.manager import EnvHandler, admin_delete_env
from ..setting import api_settings
from ..utils.standard_device import delete_tmp_vm
from . import error
from . import serializers as mserializers


logger = logging.getLogger(__name__)


class ActiveEnvViewSet(common_mixins.RequestDataMixin,
                       common_mixins.CacheModelMixin,
                       viewsets.ReadOnlyModelViewSet):
    queryset = env_models.Env.objects.exclude(status=env_models.Env.Status.TEMPLATE)
    serializer_class = mserializers.ActiveEnvSerializer
    permission_classes = (IsAuthenticated, IsStaffPermission,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('name',)
    ordering_fields = ('create_time',)
    ordering = ('create_time',)
    page_cache = False

    def get_queryset(self):
        queryset = self.queryset

        type = self.query_data.get('type', env_models.Env.Type.values())
        if type is not None:
            queryset = queryset.filter(type=type)

        status = self.query_data.get('status', env_models.Env.Status.values())
        if status is not None:
            queryset = queryset.filter(status=status)

        wheres = []
        # 1正常 2异常
        env_status = self.query_data.get('env_status', [1, 2])
        if env_status is None:
            # 所有
            wheres.append('''
                (
                    status = {env_deleted}
                    AND (
                        EXISTS (
                            SELECT id 
                            FROM common_env_envterminal 
                            WHERE common_env_envterminal.env_id = common_env_env.id 
                                AND (common_env_envterminal.status <> {envterminal_template} 
                                     AND common_env_envterminal.status <> {envterminal_deleted})
                        )
                    )
                ) OR (
                    status <> {env_deleted}
                    AND (
                        EXISTS (
                            SELECT id 
                            FROM common_env_envterminal 
                            WHERE common_env_envterminal.env_id = common_env_env.id 
                                AND common_env_envterminal.status <> {envterminal_template} 
                        )
                    )
                )
            '''.format(
                env_deleted=env_models.Env.Status.DELETED,
                envterminal_template=env_models.EnvTerminal.Status.TEMPLATE,
                envterminal_deleted=env_models.EnvTerminal.Status.DELETED,
            ))
        elif env_status == 1:
            # 正常
            queryset = queryset.filter(
                status__in=env_models.Env.ActiveStatusList
            )
            wheres.append('''
                NOT EXISTS (
                    SELECT id 
                    FROM common_env_envterminal 
                    WHERE common_env_envterminal.env_id = common_env_env.id 
                        AND (common_env_envterminal.status = {envterminal_template} 
                            OR common_env_envterminal.status = {envterminal_deleted} 
                            OR common_env_envterminal.status = {envterminal_error})
                )
            '''.format(
                envterminal_template=env_models.EnvTerminal.Status.TEMPLATE,
                envterminal_deleted=env_models.EnvTerminal.Status.DELETED,
                envterminal_error=env_models.EnvTerminal.Status.ERROR,
            ))
        elif env_status == 2:
            # 异常
            wheres.append('''
                status = {env_error}
                OR (
                    status = {env_deleted} AND 
                    EXISTS (
                        SELECT id 
                        FROM common_env_envterminal 
                        WHERE common_env_envterminal.env_id = common_env_env.id 
                            AND (common_env_envterminal.status <> {envterminal_template} 
                                AND common_env_envterminal.status <> {envterminal_deleted})
                    )
                ) 
                OR (
                    (status = {env_creating} OR status = {env_using} OR status = {env_pause}) AND 
                    EXISTS (
                        SELECT id 
                        FROM common_env_envterminal 
                        WHERE common_env_envterminal.env_id = common_env_env.id 
                            AND (common_env_envterminal.status = {envterminal_template} 
                                OR common_env_envterminal.status = {envterminal_deleted} 
                                OR common_env_envterminal.status = {envterminal_error})
                    )
                )
            '''.format(
                env_error=env_models.Env.Status.ERROR,
                env_deleted=env_models.Env.Status.DELETED,
                envterminal_template=env_models.EnvTerminal.Status.TEMPLATE,
                envterminal_deleted=env_models.EnvTerminal.Status.DELETED,
                envterminal_error=env_models.EnvTerminal.Status.ERROR,
                env_creating=env_models.Env.Status.CREATING,
                env_using=env_models.Env.Status.USING,
                env_pause=env_models.Env.Status.PAUSE,
            ))

        queryset = queryset.extra(where=wheres)
        return queryset

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
        if not queryset:
            return False

        user = self.request.user
        for env in queryset:
            env_handler = EnvHandler(user, backend_admin=True)
            env_handler.delete(env)

        return True

    def extra_handle_list_data(self, data):
        monitor_info_ret = mserializers.ActiveEnvSerializer.get_monitor_info(data, ['monitor', 'assistance'])
        env_monitor_info = monitor_info_ret['monitor_info']
        env_assistance_info = monitor_info_ret['assistance_info']

        for row in data:
            row['shared_monitor'] = env_monitor_info.get(row['id'], [])
            row['shared_assistance'] = env_assistance_info.get(row['id'], [])

            # 反向查属于哪个课程 题目
            belong_target = None
            for func in api_settings.GET_ENV_TARGET_FUNCS:
                belong_target = func(row['id'])
                if belong_target:
                    break
            row['belong_target'] = belong_target

        return data


class EnvViewSet(common_mixins.ShareTeachersMixin,
                 common_mixins.CacheModelMixin,
                 common_mixins.DestroyModelMixin,
                 viewsets.ModelViewSet):
    queryset = env_models.Env.objects.filter(status=env_models.Env.Status.TEMPLATE)
    serializer_class = mserializers.EnvSerializer
    permission_classes = (IsAuthenticated, IsStaffPermission,)
    filter_backends = (filters.SearchFilter, common_filters.BootstrapOrderFilter)
    search_fields = ('name',)
    ordering_fields = ('create_time', 'name', 'modify_time')
    ordering = ('-create_time',)
    create_user_filed = 'user'

    @oj_share_teacher
    def get_queryset(self):
        queryset = self.queryset

        type = self.query_data.get('type', env_models.Env.Type.values())
        if type is not None:
            queryset = queryset.filter(type=type)

        return queryset

    @detail_route(methods=['delete'])
    def delete_file(self, request, pk=None):
        env = self.get_object()
        if env.file:
            env.file.delete()
            env.save()
            self.clear_cache()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @detail_route(methods=['post', 'delete'])
    def snapshot(self, request, pk=None):
        if request.method == 'POST':
            backend_admin = bool(request.data.get('from_backend'))
            env = self.get_object()
            try:
                env_handler = EnvHandler(request.user, backend_admin=backend_admin)
                env_handler.create_snapshot(env)
            except MsgException as e:
                raise exceptions.ValidationError(e.message)
            self.clear_cache()
            return Response(status=status.HTTP_200_OK)
        else:
            backend_admin = bool(request.data.get('from_backend'))
            env = self.get_object()
            try:
                env_handler = EnvHandler(request.user, backend_admin=backend_admin)
                env_handler.delete_snapshot(env)
            except MsgException as e:
                raise exceptions.ValidationError(e.message)
            self.clear_cache()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @classmethod
    def _destroy_env_related(cls, env):
        def tmp_task():
            logger.info('delete env[%s] related start', env.pk)
            # 删除关联测试场景
            test_env_map = env_models.TestEnvMap.objects.filter(template_env=env).first()
            if test_env_map:
                try:
                    admin_delete_env(test_env_map.test_env)
                except Exception as e:
                    logger.error('delete env[%s] related test env error: %s', env.pk, e)
            # 删除关联快照场景
            snapshot_env_map = env_models.SnapshotEnvMap.objects.filter(template_env=env).first()
            if snapshot_env_map:
                try:
                    admin_delete_env(snapshot_env_map.tmp_env)
                except Exception as e:
                    logger.error('delete env[%s] related snapshot env error: %s', env.pk, e)
            # 删除快照
            image_ids = [envterminal.image_id for envterminal in env.envterminal_set.all()]
            image_ids = filter(lambda x: x, image_ids)
            for image_id in image_ids:
                try:
                    scene.image.delete(image_id)
                except Exception as e:
                    logger.error('delete env[%s] related snapshot error: %s', env.pk, e)
            logger.info('delete env[%s] related end', env.pk)
        new_task(tmp_task, 0, ())

    def perform_destroy(self, instance):
        self._destroy_env_related(instance)
        super(EnvViewSet, self).perform_destroy(instance)

    def perform_batch_destroy(self, queryset):
        for env in queryset:
            self._destroy_env_related(env)

        return super(EnvViewSet, self).perform_batch_destroy(queryset)


class StandardDeviceViewSet(common_mixins.ShareTeachersMixin,
                            common_mixins.CacheModelMixin,
                            common_mixins.DestroyModelMixin,
                            viewsets.ModelViewSet):
    queryset = env_models.StandardDevice.objects.all()
    serializer_class = mserializers.StandardDeviceSerializer
    permission_classes = (IsAuthenticated, IsStaffPermission,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('name',)
    ordering_fields = ('tmp_vm', 'create_time')
    ordering = ('-tmp_vm', '-create_time')

    @oj_share_teacher
    def get_queryset(self):
        queryset = self.queryset
        image_status = self.query_data.get('image_status', env_models.StandardDevice.ImageStatus.values())
        if image_status is not None:
            queryset = queryset.filter(image_status=image_status)

        role = self.query_data.get('role', env_models.StandardDevice.Role.values())
        if role is not None:
            queryset = queryset.filter(role=role)

            role_type = self.query_data.get('role_type', env_models.StandardDevice.RoleType[role].values())
            if role_type is not None:
                queryset = queryset.filter(role_type=role_type)

        is_real = self.query_data.get('is_real', bool)
        if is_real is not None:
            queryset = queryset.filter(is_real=is_real)

        image_type = self.query_data.get('image_type', env_models.EnvTerminal.ImageType.values())
        if image_type is not None:
            queryset = queryset.filter(image_type=image_type)

        can_use = self.query_data.get('can_use', bool)
        raw_system_type = self.query_data.get('system_type')
        system_type = self.query_data.get('system_type', env_models.EnvTerminal.SystemType.values())
        if system_type is not None:
            queryset = queryset.filter(system_type=system_type)
            if can_use:
                queryset = queryset.filter(image_status=env_models.StandardDevice.ImageStatus.CREATED)
        elif raw_system_type == 'other':
            queryset = queryset.filter(Q(system_type='') | Q(system_type=None))
        elif raw_system_type == 'all':
            if can_use:
                queryset = queryset.filter(Q(system_type='') | Q(system_type=None) | Q(image_status=env_models.StandardDevice.ImageStatus.CREATED))

        system_sub_type = self.query_data.get('system_sub_type', env_models.StandardDevice.SystemSubType.values())
        if system_sub_type is not None:
            queryset = queryset.filter(system_sub_type=system_sub_type)

        flavor = self.query_data.get('flavor', api_settings.FLAVORS)
        if flavor is not None:
            queryset = queryset.filter(flavor=flavor)

        return queryset

    # 文件上传比较大， 添加validate模式先验证基础数据
    def _validate_mode(self):
        return '_validate' in self.request.data

    def _terminal_mode(self, validated_data, instance=None):
        role = validated_data.get('role')
        role_type = validated_data.get('role_type')
        if instance:
            role = role or instance.role
            role_type = role_type or instance.role_type
        return role == env_models.StandardDevice.Role.TERMINAL \
                or (role == env_models.StandardDevice.Role.GATEWAY
                    and role_type not in (env_models.StandardDevice.RoleGatewayType.ROUTER, env_models.StandardDevice.RoleGatewayType.FIREWALL))

    def _check_upload_image(self, image_name, disk_format, creating=False):
        if image_name in api_settings.BASE_IMAGES:
            raise exceptions.ValidationError(error.CONFLICT_WITH_BASE_IMAGE_NAME)

        if not disk_format:
            raise exceptions.ValidationError(error.NO_DISK_FORMAT)

        image_file = self.request.data.get('image_file')
        third_file_name = self.request.data.get('third_file_name')
        if not image_file and not third_file_name:
            if creating:
                raise exceptions.ValidationError(error.NO_IMAGE_FILE)

        if third_file_name:
            if not scene.image.operator.glance_cli.is_image_file_exists(third_file_name):
                raise exceptions.ValidationError(error.NO_IMAGE_FILE)

    def _try_upload_image(self, image_name, image_type, disk_format, meta_data=None):
        image_file = self.request.data.get('image_file')
        third_file_name = self.request.data.get('third_file_name')
        if not image_file and not third_file_name:
            return False

        # 检查镜像是否已存在, 已存在则删除
        image = scene.image.get(image_name=image_name)
        if image:
            scene.image.delete(image_name=image_name)

        upload_data = {
            'image_name': image_name,
        }
        if image_file:
            upload_data.update({
                'image_file': image_file,
                'meta_data': {
                    'disk_format': disk_format,
                    'visibility': 'public',
                    'minimum_disk': 0,
                    'minimum_ram': 0,
                }
            })
        else:
            upload_data.update({
                'ftp_file_name': third_file_name,
                'meta_data': {
                    'disk_format': disk_format,
                }
            })

        def created(image):
            logger.info('image[%s] created', image_name)
            env_models.StandardDevice.objects.filter(name=image_name).update(image_status=env_models.StandardDevice.ImageStatus.CREATED)
            self.clear_cache()
            if meta_data is not None:
                scene.image.update(image_name=image_name, partial_update=False, **meta_data)
            if image_type == env_models.StandardDevice.ImageType.DOCKER:
                scene.image.local_load_container(image)
            # # snapshot
            # else:
            #     scene.image.operator.scene_convert_img_to_disk(image.id)

        def failed(error):
            logger.info('image[%s] failed', image_name)
            env_models.StandardDevice.objects.filter(name=image_name).update(image_status=env_models.StandardDevice.ImageStatus.ERROR)
            self.clear_cache()

        upload_data.update({
            'created': created,
            'failed': failed,
        })

        scene.image.create(**upload_data)
        env_models.StandardDevice.objects.filter(name=image_name).update(image_status=env_models.StandardDevice.ImageStatus.CREATING)
        return True

    def sub_perform_create(self, serializer):
        validated_data = serializer.validated_data
        if not validated_data.has_key('name'):
            raise exceptions.ValidationError({'name': [error.REQUIRED_FIELD]})
        if not validated_data.has_key('logo'):
            raise exceptions.ValidationError({'logo': [error.REQUIRED_FIELD]})

        upload_mode = self._terminal_mode(validated_data) and \
                      not validated_data.get('source_image_name')
        if upload_mode:
            self._check_upload_image(validated_data['name'], validated_data.get('disk_format'), creating=True)

        serializer.save(
            create_user=self.request.user,
            modify_user=self.request.user,
        )

        if upload_mode:
            # 元数据
            meta_data_str = validated_data.get('meta_data')
            meta_data = json.loads(meta_data_str) if meta_data_str else None
            self._try_upload_image(validated_data['name'], serializer.instance.image_type, validated_data.get('disk_format'), meta_data)

        return True

    def sub_perform_update(self, serializer):
        instance = serializer.instance
        validated_data = serializer.validated_data
        name = validated_data.get('name')
        is_terminal_mode = self._terminal_mode(validated_data, instance)
        if is_terminal_mode and name and name != instance.name:
            try:
                scene.image.update(image_name=instance.name, name=name)
            except Exception as e:
                logger.error("change image name error, new name[%s], old name[%s]", name, instance.name)

        upload_mode = is_terminal_mode and \
                      not (validated_data.get('source_image_name') or instance.source_image_name)
        if upload_mode:
            # # snapshot
            # if env_models.StandardDeviceSnapshot.objects.filter(standard_device=instance).exists():
            #     raise exceptions.PermissionDenied(error.SNAPSHOT_BAN_UPLOAD)
            self._check_upload_image(validated_data.get('name') or instance.name, validated_data.get('disk_format'))
            # 待更新元数据
            old_meta_data = serializer.instance.meta_data
            new_meta_data = validated_data.get('meta_data')
        else:
            # 非上传模式无元数据
            validated_data['meta_data'] = None

        serializer.save(
            modify_time=timezone.now(),
            modify_user=self.request.user,
        )

        if upload_mode:
            meta_data_str = new_meta_data or old_meta_data
            meta_data = json.loads(meta_data_str) if meta_data_str else None
            result = self._try_upload_image(validated_data.get('name') or instance.name,
                                            validated_data.get('image_type') or instance.image_type,
                                            validated_data.get('disk_format'), meta_data)
            # 未上传则更新元数据
            if not result and new_meta_data and new_meta_data != old_meta_data:
                scene.image.update(image_name=serializer.instance.name, partial_update=False, **json.loads(new_meta_data))

        return True

    def perform_destroy(self, instance):
        if instance.tmp_vm:
            delete_tmp_vm(instance.tmp_vm)
        scene.image.delete(image_name=instance.name)
        if instance.image_type == env_models.StandardDevice.ImageType.DOCKER:
            try:
                scene.image.local_delete_container(instance.name)
            except Exception as e:
                logger.error('local delete container[%s] error: %s', instance.name, e)
        instance.name = instance.name + generate_delete_flag(fixed=False)
        instance.tmp_vm = None
        instance.status = env_models.StandardDevice.Status.DELETE
        instance.save()
        self.clear_cache()

    def perform_batch_destroy(self, queryset):
        for instance in queryset:
            if instance.tmp_vm:
                delete_tmp_vm(instance.tmp_vm)
            scene.image.delete(image_name=instance.name)
            if instance.image_type == env_models.StandardDevice.ImageType.DOCKER:
                try:
                    scene.image.local_delete_container(instance.name)
                except Exception as e:
                    logger.error('local delete container[%s] error: %s', instance.name, e)
            instance.name = instance.name + generate_delete_flag(fixed=False)
            instance.tmp_vm = None
            instance.status = env_models.StandardDevice.Status.DELETE
            instance.save()
        if queryset:
            return True
        return False

    @detail_route(methods=['get', 'post', 'delete'],)
    def tmp_vm(self, request, pk=None):
        if request.method == 'GET':
            device = self.get_object()
            if device.tmp_vm:
                data = mserializers.StandardDeviceEditServerSerializer(device.tmp_vm).data
            else:
                data = None
            return Response(data)
        elif request.method == 'POST':
            device = self.get_object()
            if device.access_mode not in (
                env_models.EnvTerminal.AccessMode.SSH,
                env_models.EnvTerminal.AccessMode.RDP,
                env_models.EnvTerminal.AccessMode.CONSOLE,
                env_models.EnvTerminal.AccessMode.TELNET,
            ):
                raise exceptions.ValidationError(error.STANDARD_DEVICE_ACCESSMODE_ERROR)

            # # snapshot
            # image_name = get_lastest_image_name(device.name, device)
            # if device.image_type == env_models.StandardDevice.ImageType.VM:
            #     try:
            #         image = scene.volume.get(snapshot_name=image_name)
            #     except Exception:
            #         image = None
            #
            # if not image:
            #     try:
            #         image = scene.image.get(image_name=image_name)
            #     except:
            #         image = None
            #
            # if not image:
            #     if image_name != device.name:
            #         raise exceptions.ValidationError(error.IMAGE_NOT_FOUND)
            #
            #     # 没有镜像则从基础镜像创建
            #     image_name = device.source_image_name

            image_name = device.name
            try:
                image = scene.image.get(image_name=image_name)
            except:
                image = None
            # 没有镜像则从基础镜像创建
            if not image:
                image_name = device.source_image_name
            if not image_name:
                raise exceptions.ValidationError(error.NO_BASE_IMAGE)

            if device.tmp_vm:
                edit_server = device.tmp_vm
                if edit_server.status != env_models.StandardDeviceEditServer.Status.DELETED:
                    raise exceptions.ValidationError(error.TMP_ENV_CONFLICT)
                delete_tmp_vm(edit_server, destroy=False)
                edit_server.status = env_models.StandardDeviceEditServer.Status.CREATING
                edit_server.save()
            else:
                edit_server = env_models.StandardDeviceEditServer.objects.create(
                    create_user=request.user
                )
                device.tmp_vm = edit_server
                device.save()
            self.clear_cache()

            def _create_vm():
                if device.error:
                    env_models.StandardDevice.objects.filter(pk=device.pk).update(error='')

                # 建机器
                try:
                    creater = StandardDeviceTmpVmCreater(image_name, device)
                    ret = creater.create_resource()
                except Exception as e:
                    env_models.StandardDevice.objects.filter(pk=device.pk).update(error=e.message)
                    device.tmp_vm.delete()
                    self.clear_cache()
                    return

                logger.info('create template vm for device[%s] by image[%s] return[%s]: waiting for update' % (device.pk, image_name, ret))
                float_ip = ret['float_ip']
                port = device.access_port or env_models.EnvTerminal.AccessModeDefaultPort.get(device.access_mode)
                update_params = {}

                if device.access_mode in (env_models.EnvTerminal.AccessMode.SSH, env_models.EnvTerminal.AccessMode.RDP):
                    # 建连接
                    remote_manager = RemoteManager(request.user)
                    connection_name = '%s:%s:%s:%s' % (request.user.id, float_ip, port, hashlib.md5(str(uuid.uuid4())).hexdigest())
                    params = {
                        'username': ret['username'],
                        'password': ret['password'],
                    }
                    try:
                        if device.access_mode == env_models.EnvTerminal.AccessMode.SSH:
                            connection_id = remote_manager.create_ssh_connection(connection_name, float_ip, **params).connection_id
                        elif device.access_mode == env_models.EnvTerminal.AccessMode.RDP:
                            params['security'] = device.access_connection_mode or 'rdp'
                            if device.system_type == env_models.StandardDevice.SystemType.LINUX:
                                params['enable-sftp'] = 'true'
                            connection_id = remote_manager.create_rdp_connection(connection_name, float_ip, **params).connection_id
                        update_params['connection_id'] = connection_id
                    except Exception as e:
                        logger.error('create guacamole connection error: %s', e)

                # 建代理
                if port and proxy.PROXY_SWITCH:
                    try:
                        proxy_ports = proxy.create_proxy(float_ip, [port])
                    except Exception as e:
                        logger.error('create tmp_vm[%s] proxy error: %s' % (device.tmp_vm.id, e))
                        env_models.StandardDevice.objects.filter(pk=device.pk).update(error=e.message)
                        creater.rollback_resource()
                        device.tmp_vm.delete()
                        self.clear_cache()
                        raise e
                    logger.info('create template vm for device[%s] by image[%s]: create proxy %s:%s --> %s' % (
                        device.pk, image_name, float_ip, port, proxy_ports))
                    if len(proxy_ports) > 0:
                        update_params['proxy_port'] = proxy_ports[0]
                        proxy.restart_proxy()

                tmp_vm = device.tmp_vm
                # 获取最新的数据
                lastest_tmp_vm = env_models.StandardDeviceEditServer.objects.get(pk=tmp_vm.pk)
                if lastest_tmp_vm.status == env_models.StandardDeviceEditServer.Status.RUNNING:
                    tmp_vm_status = env_models.StandardDeviceEditServer.Status.RUNNING
                else:
                    tmp_vm_status = env_models.StandardDeviceEditServer.Status.STARTING

                update_params.update({
                    'tmp_network_ids': json.dumps(ret['network_ids']),
                    'tmp_router_ids': json.dumps(ret['router_ids']),
                    'tmp_docker_id': ret['docker_id'],
                    'tmp_vm_id': ret['vm_id'],
                    'tmp_net_ports': json.dumps(ret['net_ports']),
                    'protocol': device.access_mode,
                    'float_ip': float_ip,
                    'host_ip': ret['host_ip'],
                    'host_name': ret['host_name'],
                    'port': port,
                    'username': ret['username'],
                    'password': ret['password'],
                    'status': tmp_vm_status,
                })

                try:
                    env_models.StandardDeviceEditServer.objects.filter(pk=tmp_vm.pk).update(**update_params)
                except Exception as e:
                    logger.error('update tmp_vm[%s] error: %s' % (tmp_vm.id, e))
                    delete_tmp_vm(tmp_vm, destroy=False)
                    raise e
                self.clear_cache()
                new_task(self._check_tmp_vm_status, 0, (tmp_vm.id, device))

            new_task(_create_vm, 0, ())
            return Response(mserializers.StandardDeviceEditServerSerializer(edit_server).data)
        elif request.method == 'DELETE':
            device = self.get_object()
            if device.tmp_vm:
                delete_tmp_vm(device.tmp_vm)
            self.clear_cache()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @detail_route(methods=['post'], )
    def restart_tmp_vm(self, request, pk=None):
        device = self.get_object()
        if device.tmp_vm:
            if device.tmp_vm.tmp_vm_id:
                scene.vm.restart(device.tmp_vm.tmp_vm_id)
            elif device.tmp_vm.tmp_docker_id:
                scene.docker.restart(device.tmp_vm.tmp_vm_id)
        return Response(status=status.HTTP_200_OK)

    # ping机器更新状态
    def _check_tmp_vm_status(self, tmp_vm_id, device):
        all_time = 0
        limit_time = 60 * 5
        step_time = 1
        tmp_vm = env_models.StandardDeviceEditServer.objects.get(pk=tmp_vm_id)
        # 强制探测
        # if not device.init_support:
        if True:
            port = None
            # 有对应标靶并且有访问端口的情况检查端口
            if device and device.access_port:
                port = int(device.access_port)
            # 尝试从标靶访问方式获取默认端口
            elif device and device.access_mode:
                port = env_models.EnvTerminal.AccessModeDefaultPort.get(device.access_mode, None)

            def _callback():
                try:
                    tmp_vm.status = env_models.StandardDeviceEditServer.Status.RUNNING
                    tmp_vm.save()
                    self.clear_cache()
                except Exception as e:
                    logger.error('probe check - update tmp_vm status[tmp_vm_id=%s] error: %s' % (tmp_vm.id, e))

            probe(
                tmp_vm.float_ip,
                port,
                limit_time=limit_time,
                step_time=step_time,
                log_prefix='tmp_vm status[tmp_vm_id=%s]' % tmp_vm.id,
                callback=_callback,
                timeout_callback=_callback
            )
        else:
            while True:
                logger.info('normal check - tmp_vm status[tmp_vm_id=%s]: %ss' % (tmp_vm.id, all_time))
                try:
                    latest_tmp_vm = env_models.StandardDeviceEditServer.objects.get(pk=tmp_vm.pk)
                except env_models.StandardDeviceEditServer.DoesNotExist as e:
                    logger.error('normal check - tmp vm[%s] not exist' % tmp_vm.pk)
                    break
                except Exception as e:
                    logger.error('normal check - get tmp vm[%s] error: %s' % (tmp_vm.pk, e))
                    continue

                if latest_tmp_vm.status == env_models.StandardDeviceEditServer.Status.DELETED or \
                    latest_tmp_vm.status == env_models.StandardDeviceEditServer.Status.RUNNING:
                    break
                else:
                    if all_time > limit_time:
                        try:
                            tmp_vm.status = env_models.StandardDeviceEditServer.Status.RUNNING
                            tmp_vm.save()
                            self.clear_cache()
                        except Exception as e:
                            logger.error('normal check - update tmp_vm status[tmp_vm_id=%s] error: %s' % (tmp_vm.id, e))
                        break
                    else:
                        time.sleep(step_time)
                        all_time = all_time + step_time

    @detail_route(methods=['post'], )
    def image(self, request, pk=None):
        if request.method == 'POST':
            device = self.get_object()
            if not device.tmp_vm or (not device.tmp_vm.tmp_vm_id and not device.tmp_vm.tmp_docker_id):
                raise exceptions.ValidationError(error.NO_TMP_ENV)

            if device.image_status == env_models.StandardDevice.ImageStatus.CREATING:
                raise exceptions.ValidationError(error.IMAGE_SAVING)

            device.image_status = env_models.StandardDevice.ImageStatus.CREATING
            device.save()
            self.clear_cache()

            def _create_image():
                image_name = device.name
                # # snapshot
                # image_name = '{}__$__{}'.format(image_name, str(uuid.uuid4()))
                # 删除旧的镜像
                try:
                    old_image_id = scene.image.get(image_name=image_name).id
                except:
                    old_image_id = None

                def created(image):
                    logger.info('device[%s] image created', device.pk)
                    device.image_status = env_models.StandardDevice.ImageStatus.CREATED
                    try:
                        device.save()
                        # # snapshot
                        # env_models.StandardDeviceSnapshot.objects.create(
                        #     standard_device=device,
                        #     name=image_name,
                        # )
                    except Exception as e:
                        logger.error('save standard device[%s] error: %s', device.pk, e)

                    # # snapshot
                    # if device.tmp_vm.tmp_vm_id:
                    #     try:
                    #         delete_tmp_vm(device.tmp_vm)
                    #     except Exception as e:
                    #         logger.error('delete standard device[%s] tmp vm error: %s', device.pk, e)
                    self.clear_cache()
                    # 删除旧的镜像
                    if old_image_id:
                        scene.image.delete(image_id=old_image_id)

                def failed(error):
                    logger.info('device[%s] image failed', device.pk)
                    device.image_status = env_models.StandardDevice.ImageStatus.ERROR
                    try:
                        device.save()
                    except Exception as e:
                        logger.error('save standard device[%s] error: %s', device.pk, e)
                    self.clear_cache()

                    # # snapshot
                    # if device.tmp_vm.tmp_vm_id:
                    #     scene.vm.start(device.tmp_vm.tmp_vm_id)

                try:
                    if device.tmp_vm.tmp_vm_id:
                        # # snapshot
                        # scene.vm.shutdown(device.tmp_vm.tmp_vm_id)
                        scene.image.create(image_name, vm_id=device.tmp_vm.tmp_vm_id, created=created, failed=failed, timeout_callback=created)
                    elif device.tmp_vm.tmp_docker_id:
                        scene.image.create(image_name, container_id=device.tmp_vm.tmp_docker_id, created=created, failed=failed, timeout_callback=created)
                    else:
                        raise exceptions.ValidationError(error.NO_TMP_ENV)
                except Exception as e:
                    logger.error('device[%s] save image error: %s', device.pk, e)
                    device.error = e.message
                    device.image_status = env_models.StandardDevice.ImageStatus.ERROR
                    device.save()
                    self.clear_cache()

            new_task(_create_image, 0, ())
            return Response({})

    @detail_route(methods=['get'], )
    def console_url(self, request, pk=None):
        device = self.get_object()
        vm_id = device.tmp_vm.tmp_vm_id if device.tmp_vm else None
        if not vm_id:
            raise exceptions.ValidationError(error.NO_TMP_ENV)

        url = scene.vm.get_console_url(vm_id)
        return Response({'url': url})

    @detail_route(methods=['get'], )
    def tmp_vm_status(self, request, pk=None):
        device = self.get_object()
        vm_id = device.tmp_vm.tmp_vm_id if device.tmp_vm else None
        if not vm_id:
            raise exceptions.ValidationError(error.NO_TMP_ENV)

        try:
            server = scene.vm.get(vm_id)
            status = getattr(server, 'OS-EXT-STS:power_state', 0)
        except:
            status = -1

        return Response({'status': status})


class EnvAttackerViewSet(common_mixins.RequestDataMixin,
                         common_mixins.CacheModelMixin,
                         common_mixins.DestroyModelMixin,
                         viewsets.ModelViewSet):
    queryset = env_models.EnvAttacker.objects.all()
    serializer_class = mserializers.EnvAttackerSerializer
    permission_classes = (IsAuthenticated, IsStaffPermission,)
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('name',)
    ordering_fields = ('create_time')
    ordering = ('-create_time')

    def get_queryset(self):
        queryset = self.queryset

        type = self.query_data.get('type', env_models.EnvAttacker.Type.values())
        if type is not None:
            queryset = queryset.filter(type=type)

        return queryset

    def perform_destroy(self, instance):
        instance.name = instance.name + generate_delete_flag(fixed=False)
        instance.status = env_models.EnvAttacker.Status.DELETE
        instance.save()
        self.clear_cache()

    def perform_batch_destroy(self, queryset):
        for instance in queryset:
            instance.name = instance.name + generate_delete_flag(fixed=False)
            instance.status = env_models.EnvAttacker.Status.DELETE
            instance.save()
        if queryset:
            return True
        return False

    @detail_route(methods=['delete'])
    def delete_file(self, request, pk=None):
        instance = self.get_object()
        if instance.file:
            instance.file.delete()
            instance.save()
            self.clear_cache()
        return Response(status=status.HTTP_204_NO_CONTENT)
