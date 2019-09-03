import logging

from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from common_env.cms import serializers
from common_framework.utils.rest.list_view import list_view
from common_framework.utils.rest.permission import IsStaffPermission
from common_framework.utils.shortcuts import AppRender
from common_scene.compute.views import InstanceAction
from common_scene.docker.views import ContainerAction
from common_scene.image.views import ImageAction
from common_scene.network.views import NetworkAction
from common_scene.utils import to_dict
from oj import settings
from common_scene.setting import api_settings
from common_scene.clients import docker_client
from common_scene.utils import get_ip_by_hostname

from common_env import models as env_models


LOCAL_CONTAINER_STATUS = {
    "running": "Running",
    "exited": "Stopped"
}

render = AppRender('common_scene', 'cms').render
LOG = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def instance_api_list(request):
    context = {'DEBUG': settings.DEBUG}
    return render(request, 'instance_api_list.html', context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def image_api_list(request):
    context = {'DEBUG': settings.DEBUG}
    return render(request, 'image_api_list.html', context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def network_api_list(request):
    context = {'DEBUG': settings.DEBUG}
    return render(request, 'network_api_list.html', context)


# @api_view(['GET'])
# @permission_classes((IsAuthenticated, IsStaffPermission,))
# def firewall_api_list(request):
#     context = {'DEBUG': settings.DEBUG}
#     return render(request, 'firewall_api_list.html', context)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def get_instance_list(request):
    try:

        if settings.PLATFORM_TYPE == 'ALL':
            data = InstanceAction().get_instance_list_by_name('XOJ')
            data.extend(InstanceAction().get_instance_list_by_name('XAD'))
        else:
            data = InstanceAction().get_instance_list_by_name('X'+settings.PLATFORM_TYPE)
        res_list = []

        if not len(data) == 0:

            for instance in data:
                try:
                    env_instance = env_models.EnvTerminal.objects.filter(vm_id=instance.id).first()

                    if env_instance is not None:
                        create_user = env_instance.env.user.first_name
                    else:
                        env_instance = env_models.StandardDeviceEditServer.objects.filter(tmp_vm_id=instance.id).first()

                        if env_instance is not None:
                            create_user = env_instance.create_user.first_name
                        else:
                            create_user = ''

                except Exception as e:
                    create_user = ''

                networks_contain = hasattr(instance, 'networks')

                if networks_contain:

                    network_list = instance.networks
                    if network_list:
                        for key in network_list:
                            address = "&nbsp;".join(instance.networks.get(key, None))
                    else:
                        address = ''

                else:
                    address = ''

                node = instance._info.get('OS-EXT-SRV-ATTR:host', 'None')
                res_dict = {
                    'id': instance.id,
                    'status': instance.status,
                    'name': instance.name,
                    'server_ip': address,
                    'create_time': instance.created,
                    'node': node,
                    'create_user': create_user,

                }
                image_id = instance.image.get('id', None)
                if image_id:
                    # image = ImageAction().get_image(id=image_id)
                    # image_name = image.name
                    image_name = None
                else:
                    image_name = None
                res_dict['server_image'] = image_name
                res_list.append(res_dict)
    except Exception as e:
        raise e
    return list_view(request, res_list, serializers.InstanceListSerializer)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def get_instance_detail_by_id(request):
    try:
        id = request.GET['id']
        data = InstanceAction().get_server(id)
        _attrs = ['id', 'created', 'name', 'networks', 'status', 'OS-EXT-AZ:availability_zone', 'metadata',
                  ]
        security_group = ''
        res_data = to_dict(data, _attrs)
        group_contain = hasattr(data, 'security_groups')

        if group_contain:
            security_group_list = data.security_groups
            if security_group_list:

                for security in security_group_list:
                    security_group = security_group + '&nbsp;' + security['name']

        else:
            security_group = ''

        networks_contain = hasattr(data, 'networks')
        if networks_contain:

            network_list = data.networks

            if network_list:
                for key in network_list:
                    address = "&nbsp;".join(data.networks.get(key, None))
            else:
                address = ''
        else:
            address = ''

        res_data['security_groups'] = security_group
        res_data['address'] = address
    except Exception as e:
        raise e
    return Response(res_data)


@api_view(['DELETE'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def delete_instance_by_id(request):
    try:
        ids = request.data.getlist('ids', [])

        for instance_id in ids:
            data = InstanceAction().delete_instance(instance_id)

    except Exception as e:
        raise e

    return Response(data)


@api_view(['DELETE'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def delete_image_by_id(request):
    try:
        ids = request.data.getlist('ids', [])

        for image_id in ids:
            data = ImageAction().delete_image(image_id)

    except Exception as e:
        raise e

    return Response(data)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def get_image_list(request):
    try:
        res_list = []
        data = ImageAction().list_image()
        dont_show_list = api_settings.DONT_SHOW['image_list']
        for da in data:

            if da.name not in dont_show_list:

                if da.size:
                    size = proc_size(da.size)
                else:
                    size = ''

                image_type = ''
                if da.container_format == 'docker':
                    image_type = 'docker'
                else:
                    image_type = da.container_format

                res_dict = {
                    'id': da.id,
                    'status': da.status,
                    'name': da.name,
                    'size': da.size,
                    'created_at': da.created_at,
                    'image_format': da.disk_format,
                    'image_size': size,
                    'image_type': image_type,
                }

                res_list.append(res_dict)
    except Exception as e:
        raise e
    return list_view(request, res_list, serializers.ImageListSerializer)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def get_image_detail_by_id(request):
    try:
        id = request.GET['id']
        data = ImageAction().get_image(id=id)
        _attrs = ['id', 'name', 'disk_format', 'status', 'size',
                  'container_format', 'created_at', 'updated_at', 'protected', 'visibility']
        data = to_dict(data, _attrs)
    except Exception as e:
        raise e
    return Response(data)


def get_local_dockers(docker_id=None):
    res_list = []

    dk_cli = docker_client.Client(base_url='tcp://controller:2375')
    local_containers = dk_cli.list_containers()

    for local_cont in local_containers:
        names = local_cont.get("Names")
        if len(names) > 1 or names[0].startswith("/zun-"):
            continue
        cont_name = names[0]

        if docker_id and docker_id != local_cont["Id"]:
            continue

        ports = local_cont.get("Ports") or []
        env_docker = env_models.EnvTerminal.objects.filter(vm_id=cont_name[1:]).first()
        if env_docker is not None:
            create_user = env_docker.env.user.first_name
        else:
            create_user = ""

        res_list.append({
            'id': local_cont["Id"],
            'uuid': local_cont["Id"],
            'name': cont_name[1:],
            'command': local_cont["Command"],
            'image': local_cont["Image"].split(":")[0],
            'status': LOCAL_CONTAINER_STATUS.get(local_cont.get("State")),
            'status_detail': local_cont.get("Status"),
            'ports': ["{}->{}/{} ".format(p.get("PublicPort"),
                                         p.get("PrivatePort"),
                                         p.get("Type")) for p in ports],
            'create_user': create_user,
            'address_list': [get_ip_by_hostname("controller")],
            'host': "controller",
            'image_driver': "docker"
        })
    return res_list

@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def get_docker_server_list(request):
    try:
        data = ContainerAction().list_container()
        res_list = []
        _attrs = ['uuid', 'name', 'command', 'image', 'status', 'ports', 'host']

        for docker in data:
            create_user = ''
            # get docker instance networks
            docker_net_list = docker.addresses.values()
            address_list = []
            if docker_net_list:
                for net_list in docker_net_list:
                    # get one of network ips
                    address_str = ''
                    for net in net_list:
                        address_str = address_str+'&nbsp;' + net['addr']
                    address_list.append(address_str)

            try:
                env_docker = env_models.EnvTerminal.objects.filter(vm_id=docker.uuid).first()

                if env_docker is not None:
                    create_user = env_docker.env.user.first_name
                else:
                    env_docker = env_models.StandardDeviceEditServer.objects.filter(tmp_docker_id=docker.uuid).first()
                    if env_docker is not None:
                        create_user = env_docker.create_user.first_name
                    else:
                        create_user = ''

            except Exception as e:
                create_user = ''
            res_dict = to_dict(docker, _attrs)
            res_dict['id'] = res_dict['uuid']
            res_dict['address_list'] = address_list
            res_dict['create_user'] = create_user
            res_list.append(res_dict)

    except Exception as e:
        raise e

    local_dockers = get_local_dockers()
    if local_dockers:
        res_list.extend(local_dockers)

    return list_view(request, res_list, serializers.DockerListSerializer)


@api_view(['DELETE'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def delete_docker_by_id(request):
    try:
        ids = request.data.getlist('ids', [])

        for id in ids:
            data = ContainerAction().delete_container(container_id=id,force=False)

    except Exception as e:
        raise e

    return Response(data)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def get_docker_detail_by_id(request):
    _attrs = ['uuid', 'name', 'command', 'cpu', 'disk', 'image', 'image_driver', 'status', 'status_detail',
              'status_reason', 'ports', 'memory']
    try:
        id = request.GET['id']
        data = ContainerAction().get_container(container_id=id)
        res_dict = to_dict(data, _attrs)
        port_list = data.ports
        res_port = ''
        for port in port_list:
            res_port = res_port + '&nbsp;' + str(port)
        res_dict['ports'] = res_port
        res_dict['id'] = res_dict['uuid']

        return Response(res_dict)
    except Exception as e:
        try:
            cont_list = get_local_dockers(docker_id=request.GET['id'])
            if cont_list:
                res_dict = cont_list[0]
                for attr in _attrs:
                    if attr not in res_dict.keys():
                        res_dict.update({attr: None})
                return Response(res_dict)
        except Exception as e:
            raise e
        raise e


@api_view(['DELETE'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def delete_network_by_id(request):
    try:
        ids = request.data.getlist('ids', [])

        for network_id in ids:
            data = NetworkAction().delete_network(network_id)

    except Exception as e:
        raise e

    return Response(data)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def get_network_list(request):
    try:
        res_list = []
        # get all network
        if settings.PLATFORM_TYPE == 'ALL':
            data = NetworkAction().list_network_by_name('XOJ')
            data.extend(NetworkAction().list_network_by_name('XAD'))
        else:
            data = NetworkAction().list_network_by_name('X' + settings.PLATFORM_TYPE)
        # get all subnet
        subnet_all = NetworkAction().list_subnet()

        for da in data:
            res_sub_list = []
            network_id = da.get('id', int)
            # subnet_list = NetworkAction().get_subnet_by_network_id(network_id)

            # get all subnet under this network
            for subnet in subnet_all:
                if subnet['network_id'] == network_id:
                    res_sub_list.append(subnet)

            res_dict = {
                'id': da.get('id', None),
                'status': da.get('status', None),
                'net_name': da.get('name', None),
                'created_at': da.get('created_at', None),
                'subnets': res_sub_list,
                'router:external': da.get('router:external', None),
                'provider:network_type': da.get('provider:network_type', None),
            }
            res_list.append(res_dict)

    except Exception as e:
        raise e
    return list_view(request, res_list, serializers.NetListSerializer)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def get_subnet_detail_by_id(request):
    try:
        id = request.GET['id']
        data = NetworkAction().get_subnet_detail(id)
        allocation_pool = data.get('allocation_pools', None)

        if allocation_pool:
            data['allocation_pools'] = allocation_pool[0]['start'] + '--' + allocation_pool[0]['end']

        dns_nameserver_list = data.get('dns_nameservers', None)

        if dns_nameserver_list:

            for name_servers in dns_nameserver_list:
                name_server = name_server + '&nbsp' + name_servers
                data['dns_nameservers'] = name_server

    except Exception as e:
        raise e
    return Response(data)


@api_view(['DELETE'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def delete_router_by_id(request):
    try:
        ids = request.data.getlist('ids', [])

        for id in ids:
            data = NetworkAction().delete_router(id)

    except Exception as e:
        raise e

    return Response(data)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def get_router_list(request):
    try:
        res_list = []
        data = NetworkAction().list_router()

        for da in data:
            res_dict = {
                'id': da.get('id', None),
                'status': da.get('status', None),
                'name': da.get('name', None),
                'created_at': da.get('created_at', None),
            }
            res_list.append(res_dict)

    except Exception as e:
        raise e
    return list_view(request, res_list, serializers.RouterListSerializer)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def get_router_detail_by_id(request):
    try:
        id = request.GET['id']
        data = NetworkAction().get_router(id)
        external_gateway_info = data.get('external_gateway_info', None)

        if external_gateway_info:
            data['network_id'] = external_gateway_info.get('network_id', None)
            data['enable_snat'] = external_gateway_info.get('enable_snat', None)
            external_fixed_ips = external_gateway_info.get('external_fixed_ips', None)

            address = ''
            if external_fixed_ips:
                for fixed_ip in external_fixed_ips:
                    address = address + '&nbsp;' + fixed_ip.get('ip_address', None)

                data['external_fixed_ips'] = address

    except Exception as e:
        raise e
    return Response(data)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def get_float_ip_list(request):
    try:
        res_list = []
        data = NetworkAction().list_floating_ip()
        # floating_list = data['floatingips']

        for da in data:
            res_dict = {
                'id': da.get('id', None),
                'status': da.get('status', None),
                'created_at': da.get('created_at', None),
                'fixed_ip_address': da.get('fixed_ip_address', None),
                'floating_ip_address': da.get('floating_ip_address', None),
            }
            res_list.append(res_dict)

    except Exception as e:
        raise e
    return list_view(request, res_list, serializers.FloatIpListSerializer)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def get_fwaas_group_list(request):
    try:
        res_list = []
        data = NetworkAction().list_firewall()

        for da in data:
            ingress_policy_id = da.get('ingress_firewall_policy_id', '')
            egress_policy_id = da.get('egress_firewall_policy_id', '')
            res_ingress_policy_name = ''
            res_egress_policy_name = ''

            if ingress_policy_id:
                res_ingress_policy = NetworkAction().get_firewall_policy(ingress_policy_id)
                res_ingress_policy_name = res_ingress_policy.get('name', '')
            else:
                res_ingress_policy_name = ''

            if egress_policy_id:
                res_egress_policy = NetworkAction().get_firewall_policy(egress_policy_id)
                res_egress_policy_name = res_egress_policy.get('name', '')
            else:
                res_egress_policy_name = ''

            res_dict = {
                'id': da.get('id', None),
                'status': da.get('status', None),
                'name': da.get('name', None),
                'description': da.get('description', None),
                'ingress_name': res_ingress_policy_name,
                'engress_name': res_egress_policy_name,
                'ingress_id': ingress_policy_id,
                'engress_id': egress_policy_id,
            }
            res_list.append(res_dict)

    except Exception as e:
        raise e
    return list_view(request, res_list, serializers.FwaasGroupListSerializer)


@api_view(['DELETE'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def delete_fwaas_group_by_id(request):
    try:
        ids = request.data.getlist('ids', [])

        for id in ids:
            data = NetworkAction().delete_firewall(id)

    except Exception as e:
        raise e

    return Response(data)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def get_fwaas_rules_list(request):
    try:

        res_list = []
        data = NetworkAction().list_firewall_rule()

        for da in data:
            res_dict = {
                'id': da.get('id', None),
                'action': da.get('action', None),
                'name': da.get('name', None),
                'description': da.get('description', None),
                'protocol': da.get('protocol', None),
                'enabled': da.get('enabled', None),
                'source_ip': da.get('source_ip_address', None),
                'destination_ip': da.get('destination_ip_address', None),
                'source_port': da.get('source_port', None),
                'destination_port': da.get('destination_port', None),
            }
            res_list.append(res_dict)

    except Exception as e:
        raise e
    return list_view(request, res_list, serializers.FwaasRuleListSerializer)


@api_view(['GET'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def get_fwaas_group_detail_by_id(request):
    try:
        id = request.GET.get('id', None)
        res_list = []
        if not id or id == '|':
            return Response(None)

        id_list = id.split('|')
        index = 1
        for item in id_list:

            if item != 'null' and item != None:
                data = NetworkAction().get_firewall_policy(item)
                rules_list = data.get('firewall_rules', None)

                if rules_list:

                    for rule_id in rules_list:
                        rule_dict = NetworkAction().get_firewall_rule(rule_id)
                        if index == 1:
                            type = 'ingress'
                        else:
                            type = 'engress'
                        res_dict = {
                            'id': rule_dict.get('id', None),
                            'description': rule_dict.get('description', None),
                            'name': rule_dict.get('name', None),
                            'protocol': rule_dict.get('protocol', None),
                            'shared': rule_dict.get('shared', None),
                            'enabled': rule_dict.get('enabled', None),
                            'action': rule_dict.get('action', None),
                            'type': type,
                            'source_ip_address': rule_dict.get('source_ip_address', 'All'),
                            'destination_ip_address': rule_dict.get('destination_ip_address', 'All'),
                            'destination_port': rule_dict.get('destination_port', 'All'),
                            'source_port': rule_dict.get('source_port', 'All'),

                        }
                        res_list.append(res_dict)

            index = index + 1

    except Exception as e:
        raise e
    return list_view(request, res_list, serializers.FwaasRuleListSerializer)


@api_view(['DELETE'])
@permission_classes((IsAuthenticated, IsStaffPermission,))
def delete_floatip_by_id(request):
    try:
        ids = request.data.getlist('ids', [])

        for flp_id in ids:
            data = NetworkAction().delete_fip(flp_id)

    except Exception as e:
        raise e

    return Response(data)


# proc image size
def proc_size(size):
    if size is None:
        return 0

    se = size / 1024
    if se > (1024 * 1024):
        sg = se / 1024
        res = str(round(sg / float(1024), 2)) + 'G'
        return res
    elif se > 1024:
        res = str(round(se / float(1024), 2)) + 'M'
        return res
    else:
        res = str(se) + 'K'
        return res
