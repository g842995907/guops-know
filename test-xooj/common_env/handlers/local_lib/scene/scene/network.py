# -*- coding: utf-8 -*-


from common_scene.complex.views import BaseScene

from ..base.base import Resource
from .utils import str_filter


class Network(Resource):

    def __init__(self, operator=None):
        self.operator = operator or BaseScene()

    def create(self, name, cidr=None, gateway_ip=None, dns=None, dhcp=True):
        params = {
            'name': str_filter(name),
            'cidr': cidr,
            'gateway_ip': gateway_ip,
            'dns_nameservers': dns or [],
            'enable_dhcp': dhcp,
        }
        if cidr and not gateway_ip:
            params['gateway_ip'] = cidr[:-4] + '254'

        network, subnet = self.operator.scene_create_network(**params)

        return network, subnet

    def delete(self, network_id):
        try:
            self.operator.delete_network(network_id)
            self.operator.scene_delete_docker_network(network_id)
        except Exception as e:
            pass

    def create_subnet(self, network_id, **kwargs):
        if kwargs.get("name"):
            kwargs['name'] = str_filter(kwargs.get("name"))
        subnet = self.operator.create_subnet(network_id, **kwargs)
        return subnet

    def update_subnet(self, subnet_id, **kwargs):
        if kwargs.get("name"):
            kwargs['name'] = str_filter(kwargs.get("name"))
        self.operator.update_subnet(subnet_id, **kwargs)

    def get_port(self, network_id=None, instance=None, container=None):
        return self.operator.scene_get_port(network_id, instance, container)

    def preallocate_fips(self, count=None, pre_fips=None):
        if count:
            if count == 0:
                return {}

            fips = self.operator.preallocate_fips(count)
            if count > 0 and len(fips.keys()) < count:
                raise Exception('no enough floating ips')
            return fips
        elif pre_fips:
            fips = self.operator.preallocate_fips(pre_fips)
            if len(fips.keys()) < len(pre_fips):
                raise Exception('no enough floating ips')
            return fips
        else:
            return {}

    def preallocate_ports(self, network_id, count=None, pre_ips=None):
        if count:
            ports = self.operator.preallocate_ports(network_id, count)
        elif pre_ips:
            ports = self.operator.preallocate_ports(network_id, pre_ips)
        else:
            ports = []
        port_map = {}
        for port in ports:
            ip = port['fixed_ips'][0]['ip_address']
            port_map[ip] = port['id']

        return port_map

    def clean_used_fips(self, pre_fips):
        self.operator.clean_used_fips(pre_fips)

    def delete_fip(self, fip_id):
        self.operator.delete_fip(fip_id)

    def delete_port(self, port_id):
        self.operator.delete_port(port_id)
