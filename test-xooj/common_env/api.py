# -*- coding: utf-8 -*-
import copy
import json
import logging

from rest_framework import permissions, exceptions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from common_remote.managers import RemoteManager

from .error import error
from .handlers.exceptions import MsgException
from .handlers.manager import EnvHandler, Creater, AttackerHandler
from .models import *
from .setting import api_settings
from .handlers.local_lib import scene


logger = logging.getLogger(__name__)


# 虚拟机上报状态
@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def update_vm_status(request):
    try:
        env_id = int(request.data['env_id'])
        vm_id = request.data['vm_id']
        vm_status = int(request.data['vm_status'])
    except Exception as e:
        logger.error('invalid params[%s]: %s' % (request.data, e))
        raise exceptions.ParseError(error.INVALID_PARAMS)

    if vm_status not in EnvTerminal.Status.values():
        logger.error('updating vm status [env_id=%s, vm_id=%s, vm_status=%s] error: invalid vm_status' % (env_id, vm_id, vm_status))
        raise exceptions.ValidationError(error.INVALID_VM_STATUS)
    else:
        logger.info('updating vm status [env_id=%s, vm_id=%s, vm_status=%s]' % (env_id, vm_id, vm_status))

    try:
        envterminal = EnvTerminal.objects.get(env=env_id, sub_id=vm_id)
    except EnvTerminal.DoesNotExist as e:
        # 尝试去除引号
        if vm_id.startswith("'") and vm_id.endswith("'"):
            try:
                envterminal = EnvTerminal.objects.get(env=env_id, sub_id=vm_id[1:-1])
            except EnvTerminal.DoesNotExist as e:
                logger.error('envterminal[env_id=%s, vm_id=%s] not exist: %s' % (env_id, vm_id, e))
                raise exceptions.NotFound(error.VM_NOT_EXIST)
        else:
            raise exceptions.APIException(error.UPDATE_ERROR)

    try:
        Creater.update_envterminal_status(envterminal, vm_status)
    except Exception as e:
        logger.error('envterminal[vm_id=%s] save error: %s' % (vm_id, e))
        raise exceptions.APIException(error.UPDATE_ERROR)

    return Response({})


# 模板虚拟机上报状态
@api_view(['POST'])
@permission_classes((permissions.AllowAny,))
def tmp_vm_running(request, pk):
    try:
        device = StandardDevice.objects.get(pk=pk)
    except StandardDevice.DoesNotExist as e:
        raise exceptions.NotFound(error.VM_NOT_EXIST)

    if device.tmp_vm and device.tmp_vm.status == StandardDeviceEditServer.Status.STARTING:
        logger.info('updating standard device[%s] tmp vm running' % pk)
        tmp_vm = device.tmp_vm
        tmp_vm.status = StandardDeviceEditServer.Status.RUNNING
        tmp_vm.save()
    else:
        logger.info('updating standard device[%s] tmp vm running: no tmp vm or status error' % pk)

    from common_framework.utils.rest.mixins import CacheModelMixin
    from .cms.api import StandardDeviceViewSet
    CacheModelMixin.clear_cls_cache(StandardDeviceViewSet)
    return Response({})


@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated,))
def login_guacamole(request):
    response = Response({})
    RemoteManager(request.user).login_guacamole(response)
    return response


@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated,))
def env_status(request):
    try:
        env_id = int(request.query_params['env_id'])
    except Exception as e:
        raise exceptions.ParseError(error.INVALID_PARAMS)

    try:
        env = Env.objects.get(pk=env_id)
    except Env.DoesNotExist as e:
        raise exceptions.NotFound(error.ENV_NOT_EXIST)

    data = {
        'status': env.status,
        'error': env.error,
        'log': env.log,
    }
    return Response(data)


@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated,))
def env_flow_data(request):
    try:
        env_id = int(request.query_params['env_id'])
        count = int(request.query_params['count'])
        last_time = request.query_params.get('last_time')
        backend_admin = bool(request.query_params.get('from_backend'))
    except Exception as e:
        raise exceptions.ParseError(error.INVALID_PARAMS)

    try:
        env = Env.objects.get(pk=env_id)
    except Env.DoesNotExist as e:
        raise exceptions.NotFound(error.ENV_NOT_EXIST)

    env_handler = EnvHandler(request.user, backend_admin=backend_admin)
    flow_data = env_handler.get_flow_data(env, count, last_time)
    data = {
        'flow_data': flow_data,
    }
    return Response(data)


@api_view(['POST', 'DELETE'])
@permission_classes((permissions.IsAuthenticated,))
def envgateway_static_route(request):
    if request.method == 'POST':
        try:
            env_id = int(request.data['env_id'])
            gateway_id = request.data['gateway_id']
            static_route = json.loads(request.data['static_route'])
            backend_admin = bool(request.data.get('from_backend'))
        except Exception as e:
            raise exceptions.ParseError(error.INVALID_PARAMS)

        try:
            envgateway = EnvGateway.objects.get(env__pk=env_id, sub_id=gateway_id)
        except EnvNet.DoesNotExist as e:
            raise exceptions.NotFound(error.GATEWAY_NOT_EXIST)

        env_handler = EnvHandler(request.user, backend_admin=backend_admin)
        try:
            env_handler.add_static_routing(envgateway, static_route)
        except MsgException as e:
            raise exceptions.PermissionDenied(e.message)

        return Response(status=status.HTTP_201_CREATED)
    elif request.method == 'DELETE':
        try:
            env_id = int(request.data['env_id'])
            gateway_id = request.data['gateway_id']
            static_route = json.loads(request.data['static_route'])
            backend_admin = bool(request.data.get('from_backend'))
        except Exception as e:
            raise exceptions.ParseError(error.INVALID_PARAMS)

        try:
            envgateway = EnvGateway.objects.get(env__pk=env_id, sub_id=gateway_id)
        except EnvNet.DoesNotExist as e:
            raise exceptions.NotFound(error.GATEWAY_NOT_EXIST)

        env_handler = EnvHandler(request.user, backend_admin=backend_admin)
        try:
            env_handler.remove_static_routing(envgateway, static_route)
        except MsgException as e:
            raise exceptions.PermissionDenied(e.message)

        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST', 'DELETE'])
@permission_classes((permissions.IsAuthenticated,))
def envgateway_firewall_rule(request):
    if request.method == 'POST':
        try:
            env_id = int(request.data['env_id'])
            gateway_id = request.data['gateway_id']
            firewall_rule = json.loads(request.data['firewall_rule'])
            backend_admin = bool(request.data.get('from_backend'))
        except Exception as e:
            raise exceptions.ParseError(error.INVALID_PARAMS)

        try:
            envgateway = EnvGateway.objects.get(env__pk=env_id, sub_id=gateway_id)
        except EnvNet.DoesNotExist as e:
            raise exceptions.NotFound(error.GATEWAY_NOT_EXIST)

        env_handler = EnvHandler(request.user, backend_admin=backend_admin)
        try:
            env_handler.add_firewall_rule(envgateway, firewall_rule)
        except MsgException as e:
            raise exceptions.PermissionDenied(e.message)

        return Response(status=status.HTTP_201_CREATED)
    elif request.method == 'DELETE':
        try:
            env_id = int(request.data['env_id'])
            gateway_id = request.data['gateway_id']
            firewall_rule = json.loads(request.data['firewall_rule'])
            backend_admin = bool(request.data.get('from_backend'))
        except Exception as e:
            raise exceptions.ParseError(error.INVALID_PARAMS)

        try:
            envgateway = EnvGateway.objects.get(env__pk=env_id, sub_id=gateway_id)
        except EnvNet.DoesNotExist as e:
            raise exceptions.NotFound(error.GATEWAY_NOT_EXIST)

        env_handler = EnvHandler(request.user, backend_admin=backend_admin)
        try:
            env_handler.remove_firewall_rule(envgateway, firewall_rule)
        except MsgException as e:
            raise exceptions.PermissionDenied(e.message)

        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated,))
def envterminal_status(request):
    try:
        env_id = int(request.query_params['env_id'])
        vm_id = request.query_params['vm_id']
    except Exception as e:
        raise exceptions.ParseError(error.INVALID_PARAMS)

    try:
        envterminal = EnvTerminal.objects.get(env__pk=env_id, sub_id=vm_id)
    except EnvTerminal.DoesNotExist as e:
        raise exceptions.NotFound(error.VM_NOT_EXIST)

    data = {
        'status': envterminal.status,
    }
    return Response(data)


@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated,))
def envterminal(request):
    try:
        env_id = int(request.query_params['env_id'])
        vm_id = request.query_params['vm_id']
        backend_admin = bool(request.query_params.get('from_backend'))
    except Exception as e:
        raise exceptions.ParseError(error.INVALID_PARAMS)

    try:
        envterminal = EnvTerminal.objects.get(env__pk=env_id, sub_id=vm_id)
    except EnvTerminal.DoesNotExist as e:
        raise exceptions.NotFound(error.VM_NOT_EXIST)

    env_handler = EnvHandler(request.user, backend_admin=backend_admin)
    data = env_handler.get_envterminal(envterminal)

    return Response(data)


@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,))
def pause_env(request):
    try:
        env_id = int(request.data['env_id'])
        backend_admin = bool(request.data.get('from_backend'))
    except Exception as e:
        raise exceptions.ParseError(error.INVALID_PARAMS)

    try:
        env = Env.objects.get(pk=env_id)
    except Env.DoesNotExist as e:
        raise exceptions.NotFound(error.ENV_NOT_EXIST)

    env_handler = EnvHandler(request.user, backend_admin=backend_admin)
    env_handler.pause(env)

    return Response({})


@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,))
def recover_env(request):
    try:
        env_id = int(request.data['env_id'])
        backend_admin = bool(request.data.get('from_backend'))
    except Exception as e:
        raise exceptions.ParseError(error.INVALID_PARAMS)

    try:
        env = Env.objects.get(pk=env_id)
    except Env.DoesNotExist as e:
        raise exceptions.NotFound(error.ENV_NOT_EXIST)

    env_handler = EnvHandler(request.user, backend_admin=backend_admin)
    env_handler.recover(env)

    return Response({})


@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,))
def recreate_envterminal(request):
    try:
        env_id = int(request.data['env_id'])
        vm_id = request.data['vm_id']
        backend_admin = bool(request.data.get('from_backend'))
    except Exception as e:
        raise exceptions.ParseError(error.INVALID_PARAMS)

    try:
        envterminal = EnvTerminal.objects.get(env__pk=env_id, sub_id=vm_id)
    except EnvTerminal.DoesNotExist as e:
        raise exceptions.NotFound(error.VM_NOT_EXIST)

    env_handler = EnvHandler(request.user, backend_admin=backend_admin)
    env_handler.recreate_envterminal(envterminal)

    return Response({})


@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,))
def restart_envterminal(request):
    try:
        env_id = int(request.data['env_id'])
        vm_id = request.data['vm_id']
        backend_admin = bool(request.data.get('from_backend'))
    except Exception as e:
        raise exceptions.ParseError(error.INVALID_PARAMS)

    try:
        envterminal = EnvTerminal.objects.get(env__pk=env_id, sub_id=vm_id)
    except EnvTerminal.DoesNotExist as e:
        raise exceptions.NotFound(error.VM_NOT_EXIST)

    env_handler = EnvHandler(request.user, backend_admin=backend_admin)
    env_handler.restart_envterminal(envterminal)

    return Response({})


@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated,))
def envterminal_console_url(request):
    try:
        env_id = int(request.query_params['env_id'])
        vm_id = request.query_params['vm_id']
        backend_admin = bool(request.query_params.get('from_backend'))
    except Exception as e:
        raise exceptions.ParseError(error.INVALID_PARAMS)

    try:
        envterminal = EnvTerminal.objects.get(env__pk=env_id, env__user=request.user, sub_id=vm_id)
    except EnvTerminal.DoesNotExist as e:
        raise exceptions.NotFound(error.VM_NOT_EXIST)

    env_handler = EnvHandler(request.user, backend_admin=backend_admin)
    url = env_handler.get_envterminal_console_url(envterminal)

    return Response({'url': url})


@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated,))
def envterminal_first_boot(request):
    try:
        env_id = int(request.query_params['env_id'])
        vm_id = request.query_params['vm_id']
        backend_admin = bool(request.query_params.get('from_backend'))
    except Exception as e:
        raise exceptions.ParseError(error.INVALID_PARAMS)

    try:
        envterminal = EnvTerminal.objects.get(env__pk=env_id, sub_id=vm_id)
    except EnvTerminal.DoesNotExist as e:
        raise exceptions.NotFound(error.VM_NOT_EXIST)

    env_handler = EnvHandler(request.user, backend_admin=backend_admin)
    result = env_handler.is_envterminal_first_boot(envterminal)

    return Response({'result': result})


@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated,))
def envnet(request):
    try:
        env_id = int(request.query_params['env_id'])
        net_id = request.query_params['net_id']
        backend_admin = bool(request.query_params.get('from_backend'))
    except Exception as e:
        raise exceptions.ParseError(error.INVALID_PARAMS)

    try:
        envnet = EnvNet.objects.get(env__pk=env_id, sub_id=net_id)
    except EnvNet.DoesNotExist as e:
        raise exceptions.NotFound(error.NET_NOT_EXIST)

    env_handler = EnvHandler(request.user, backend_admin=backend_admin)
    data = env_handler.get_network(envnet)

    return Response(data)


@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated,))
def base_images(request):
    data = scene.get_base_images()
    return Response(data)


@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated,))
def flavors(request):
    data = api_settings.FLAVOR_INFO
    return Response(data)


@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated,))
def using_env_objects(request):
    all_using_env_objects = []
    for get_using_env_objects in api_settings.GET_USING_ENV_OBJECTS_FUNCS:
        using_env_objects = get_using_env_objects(request.user)
        all_using_env_objects.extend(using_env_objects)
    return Response(all_using_env_objects)


@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated,))
def envattacker_status(request):
    try:
        instance_id = int(request.query_params['instance_id'])
    except Exception as e:
        raise exceptions.ParseError(error.INVALID_PARAMS)

    try:
        instance = EnvAttackerInstance.objects.get(pk=instance_id)
    except EnvAttackerInstance.DoesNotExist as e:
        raise exceptions.NotFound(error.ENVATTACKER_NOT_EXIST)

    data = {
        'status': instance.status,
        'error': instance.error,
    }
    return Response(data)


@api_view(['POST', 'PATCH', 'DELETE'])
@permission_classes((permissions.IsAuthenticated,))
def envattacker(request):
    if request.method == 'POST':
        try:
            env_id = int(request.data['env_id'])
            envattacker_id = int(request.data['envattacker_id'])
            attach_net_id = request.data['attach_net_id']
            target_ips = request.data['target_ips']
            attack_intensity = request.data['attack_intensity']
            if attack_intensity not in EnvAttackerInstance.AttackIntensity.values():
                raise Exception()
            backend_admin = bool(request.data.get('from_backend'))
        except Exception as e:
            raise exceptions.ParseError(error.INVALID_PARAMS)

        try:
            env = Env.objects.get(pk=env_id)
        except Env.DoesNotExist as e:
            raise exceptions.NotFound(error.ENV_NOT_EXIST)

        try:
            envnet = EnvNet.objects.get(env__pk=env_id, sub_id=attach_net_id)
        except EnvNet.DoesNotExist as e:
            raise exceptions.NotFound(error.NET_NOT_EXIST)

        try:
            envattacker = EnvAttacker.objects.get(pk=envattacker_id)
        except EnvNet.DoesNotExist as e:
            raise exceptions.NotFound(error.ENVATTACKER_NOT_EXIST)

        handler = AttackerHandler(request.user, backend_admin=backend_admin)
        try:
            instance = handler.create(envattacker, env, envnet, target_ips, attack_intensity)
        except MsgException as e:
            raise exceptions.PermissionDenied(e.message)
        except Exception as e:
            logger.error('create env attacker error[env_id=%s, envattacker_id=%s, user_id=%s]: %s' % (env_id, envattacker_id, request.user.id, e))
            raise exceptions.APIException(error.CREATE_ENVATTACKER_ERROR)

        data = {
            'id': instance.id,
            'status': instance.status,
            'envattacker_id': instance.envattacker.id,
            'attach_env_id': instance.attach_env.id if instance.attach_env else None,
            'attach_net_id': instance.attach_net.sub_id if instance.attach_net else None,
            'target_ips': instance.target_ips,
            'attack_intensity': instance.attack_intensity,
        }
        return Response(data)
    elif request.method == 'PATCH':
        try:
            instance_id = int(request.data['instance_id'])
            status = int(request.data['status'])
            if status not in (EnvAttackerInstance.Status.USING, EnvAttackerInstance.Status.PAUSE):
                raise Exception()
            backend_admin = bool(request.data.get('from_backend'))
        except Exception as e:
            raise exceptions.ParseError(error.INVALID_PARAMS)

        try:
            instance = EnvAttackerInstance.objects.get(pk=instance_id)
        except EnvAttackerInstance.DoesNotExist as e:
            raise exceptions.NotFound(error.ENVATTACKER_NOT_EXIST)

        handler = AttackerHandler(request.user, backend_admin=backend_admin)
        try:
            if status == EnvAttackerInstance.Status.USING:
                instance = handler.recover(instance)
            elif status == EnvAttackerInstance.Status.PAUSE:
                instance = handler.pause(instance)
        except MsgException as e:
            raise exceptions.PermissionDenied(e.message)
        except Exception as e:
            logger.error('change env attacker error[instance_id=%s, user_id=%s]: %s' % (instance_id, request.user.id, e))
            raise exceptions.APIException(error.DELETE_ENVATTACKER_ERROR)

        return Response({'status': instance.status})
    elif request.method == 'DELETE':
        try:
            instance_id = int(request.data['instance_id'])
            backend_admin = bool(request.data.get('from_backend'))
        except Exception as e:
            raise exceptions.ParseError(error.INVALID_PARAMS)

        try:
            instance = EnvAttackerInstance.objects.get(pk=instance_id)
        except EnvAttackerInstance.DoesNotExist as e:
            raise exceptions.NotFound(error.ENVATTACKER_NOT_EXIST)

        handler = AttackerHandler(request.user, backend_admin=backend_admin)
        try:
            handler.delete(instance)
        except MsgException as e:
            raise exceptions.PermissionDenied(e.message)
        except Exception as e:
            logger.error('delete env attacker error[instance_id=%s, user_id=%s]: %s' % (instance_id, request.user.id, e))
            raise exceptions.APIException(error.DELETE_ENVATTACKER_ERROR)

        return Response({})


@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated,))
def installers(request):
    system_sub_type = request.query_params.get('system_sub_type')
    if not system_sub_type \
        or not system_sub_type in EnvTerminal.SystemSubType.values() \
        or system_sub_type == EnvTerminal.SystemSubType.OTHER:
        return Response([])

    name = request.query_params.get('name') or ''
    all_installers = copy.deepcopy(api_settings.INSTALLERS)
    filter_installers = []
    for installer in all_installers:
        if installer['name'].lower().find(name.lower()) >= 0:
            resources = installer['resources']
            avaliable_versions = [resource['version'] for resource in resources if system_sub_type in resource['platforms']]
            if avaliable_versions:
                filter_installers.append({
                    'name': installer['name'],
                    'versions': avaliable_versions,
                })

    return Response(filter_installers)
