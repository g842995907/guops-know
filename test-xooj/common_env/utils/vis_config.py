# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django.templatetags.static import static

from ..models import StandardDevice


# 获取对应标靶的信息
def get_device_info(name):
    try:
        device = StandardDevice.objects.get(name=name)
    except:
        return {
            'logo': None,
            'init_support': True,
        }
    return {
        'logo': device.logo.url if device.logo else None,
        'init_support': device.init_support,
    }


class VisConfigHandler(object):
    def __init__(self, config):
        self.scene = config['scene']
        self.nodes = config['nodes']
        self.edges = config['edges']
        self.id_node = {node['id']: node for node in self.nodes}
        network_nodes = filter(lambda node: node['category'] == 'network', self.nodes)
        network_node_ids = [node['id'] for node in network_nodes]
        self.network_edges = filter(lambda edge: edge['from'] in network_node_ids or edge['to'] in network_node_ids, self.edges)

    def _convert_network_node(self, node):
        data = node['data']
        network = {
            'id': data['id'],
            'name': data['name'],
            'range': data.get('cidr', ''),
            'gateway': data.get('gateway', ''),
            'dns': data.get('dns', []),
            'dhcp': data.get('dhcp', True),
        }
        return network

    def _convert_router_node(self, node):
        data = node['data']
        router = {
            'id': data['id'],
            'name': data['name'],
            'staticRouting': data.get('staticRouting', []),
            'canUserConfigure': data.get('canUserConfigure', False),
            'net': self._get_node_nets(node),
        }
        return router

    def _convert_firewall_node(self, node):
        data = node['data']
        router = {
            'id': data['id'],
            'name': data['name'],
            'staticRouting': data.get('staticRouting', []),
            'rule': data['rule'],
            'canUserConfigure': data.get('canUserConfigure', False),
            'net': self._get_node_nets(node),
        }
        return router

    def _convert_server_node(self, node):
        data = node['data']
        server = {
            'id': data['id'],
            'name': data['name'],
            'imageType': data['imageType'],
            'systemType': data['systemType'],
            'systemSubType': data.get('systemSubType') or StandardDevice.SystemSubType.OTHER,
            'image': data['image'],
            'role': data['role'],
            'net': self._get_node_nets(node),
            'wan_number': data.get('wan_number') or 0,
            'lan_number': data.get('lan_number') or 0,
            'external': data.get('external', False),
            'flavor': data.get('flavor', ''),
            'accessMode': data.get('accessMode', []),
            'installers': data.get('installers', []),
            'initScript': data.get('initScript', ''),
            'installScript': data.get('installScript', ''),
            'deployScript': data.get('deployScript', ''),
            'cleanScript': data.get('cleanScript', ''),
            'pushFlagScript': data.get('pushFlagScript', ''),
            'checkScript': data.get('checkScript', ''),
            'attackScript': data.get('attackScript', ''),
            'checker': data.get('checker', ''),
            'attacker': data.get('attacker', ''),
        }

        return server

    def _get_node_nets(self, node):
        nets = []
        if node['category'] == 'server':
            net_configs = node['data'].get('netConfigs', [])
            net_config_dict = {net_config['id']: net_config for net_config in net_configs}

        for edge in self.network_edges:
            if edge['from'] == node['id']:
                network_node_id = edge['to']
            elif edge['to'] == node['id']:
                network_node_id = edge['from']
            else:
                continue
            network_node = self.id_node.get(network_node_id)
            net_id = network_node['data']['id']
            if node['category'] == 'server' and net_id in net_config_dict:
                nets.append(net_config_dict[net_id])
            else:
                nets.append(net_id)
        return nets

    def convert(self):
        json_config = {}
        json_config['scene'] = self.scene

        networks = []
        routers = []
        firewalls = []
        servers = []
        for node in self.nodes:
            category = node['category']
            if category == 'network':
                network = self._convert_network_node(node)
                if network:
                    networks.append(network)
            elif category == 'router':
                router = self._convert_router_node(node)
                routers.append(router)
            elif category == 'firewall':
                firewall = self._convert_firewall_node(node)
                firewalls.append(firewall)
            elif category == 'server':
                server = self._convert_server_node(node)
                servers.append(server)
        if networks:
            json_config['networks'] = networks
        if routers:
            json_config['routers'] = routers
        if firewalls:
            json_config['firewalls'] = firewalls
        if servers:
            json_config['servers'] = servers
        return json_config


DEFAULT_NETWORK_IMG = static('common_env/img/network/edit/cloud.png')
DEFAULT_ROUTER_IMG = static('common_env/img/network/edit/router.png')
DEFAULT_FIREWALL_IMG = static('common_env/img/network/edit/firewall.png')
DEFAULT_SERVER_IMG = static('common_env/img/network/edit/server.png')


class JsonConfigHandler(object):
    def __init__(self, config, backend=True):
        # 后台返回完整的数据
        self.backend = backend
        self.scene = config['scene']
        self.networks = config.get('networks', [])
        self.routers = config.get('routers', [])
        self.firewalls = config.get('firewalls', [])
        self.servers = config.get('servers', [])

    def _convert_network(self, network):
        network_node = self._convert_common_info(network)
        name = network['name']
        img_url = get_device_info(name)['logo']
        img_url = img_url if img_url else DEFAULT_NETWORK_IMG

        network_node.update({
            'image': img_url,
            'category': 'network',
        })

        network_data = network_node['data']
        network_data.update({
            'cidr': network.get('range', ''),
            'gateway': network.get('gateway', ''),
            'dns': network.get('dns', []),
            'dhcp': network.get('dhcp', True),
        })

        return network_node

    def _convert_router(self, router):
        router_node = self._convert_common_info(router)
        name = router['name']
        img_url = get_device_info(name)['logo']
        img_url = img_url if img_url else DEFAULT_ROUTER_IMG

        router_node.update({
            'image': img_url,
            'category': 'router',
        })

        router_data = router_node['data']
        router_data.update({
            'staticRouting': router.get('staticRouting', []),
            'canUserConfigure': router.get('canUserConfigure', False),
        })

        return router_node

    def _convert_firewall(self, firewall):
        firewall_node = self._convert_common_info(firewall)
        name = firewall['name']
        img_url = get_device_info(name)['logo']
        img_url = img_url if img_url else DEFAULT_FIREWALL_IMG

        firewall_node.update({
            'image': img_url,
            'category': 'firewall',
        })

        firewall_data = firewall_node['data']
        firewall_data.update({
            'staticRouting': firewall.get('staticRouting', []),
            'rule': firewall['rule'],
            'canUserConfigure': firewall.get('canUserConfigure', False),
        })

        return firewall_node

    def _convert_server(self, server):
        server_node = self._convert_common_info(server)
        device_info = get_device_info(server['image'])
        img_url = device_info['logo']
        img_url = img_url if img_url else DEFAULT_SERVER_IMG

        server_node.update({
            'image': img_url,
            'category': 'server',
        })

        server_data = server_node['data']
        server_data.update({
            'role': server['role'],
        })

        raw_nets = []
        net_configs = []
        for net in server.get('net', []):
            if isinstance(net, dict):
                net_configs.append(net)
                raw_nets.append(net['id'])
            else:
                raw_nets.append(net)
        server_node.update({'raw_nets': raw_nets})

        if self.backend:
            server_data.update({
                'imageType': server['imageType'],
                'systemType': server['systemType'],
                'systemSubType': server.get('systemSubType') or StandardDevice.SystemSubType.OTHER,
                'image': server['image'],
                'initSupport': device_info['init_support'],

                'wan_number': server.get('wan_number') or 0,
                'lan_number': server.get('lan_number') or 0,
                'external': server.get('external', False),
                'flavor': server.get('flavor', ''),
                'accessMode': server.get('accessMode', []),
                'installers': server.get('installers', []),
                'initScript': server.get('initScript', ''),
                'installScript': server.get('installScript', ''),
                'deployScript': server.get('deployScript', ''),
                'cleanScript': server.get('cleanScript', ''),
                'pushFlagScript': server.get('pushFlagScript', ''),
                'checkScript': server.get('checkScript', ''),
                'attackScript': server.get('attackScript', ''),
                'checker': server.get('checker', ''),
                'attacker': server.get('attacker', ''),
                'netConfigs': net_configs,
            })

        return server_node

    def _convert_common_info(self, source):
        node = {
            'data': {
                'id': source['id'],
                'name': source['name'],
            },
            'id': source['id'],
            'label': source['name'],
            'shape': 'circularImage',
            'readonly': False,
            'connections': set(),
            'raw_nets': source.get('net', [])
        }
        return node

    def _generate_edges(self, node_id_map):
        edges = []
        # 已经添加过边的节点组
        connected_node_groups = []
        for node_id, node in node_id_map.items():
            connected_node_ids = node['connections']
            for connected_node_id in connected_node_ids:
                node_group = {node_id, connected_node_id}
                if node_group in connected_node_groups:
                    continue
                else:
                    connected_node_groups.append(node_group)
                edge = {
                    'from': node_id,
                    'to': connected_node_id,
                    "dashes": False
                }
                edges.append(edge)
        return edges

    def convert(self):
        # 转换节点信息
        network_nodes = []
        for network in self.networks:
            network_node = self._convert_network(network)
            network_nodes.append(network_node)

        router_nodes = []
        for router in self.routers:
            router_node = self._convert_router(router)
            router_nodes.append(router_node)

        firewall_nodes = []
        for firewall in self.firewalls:
            firewall_node = self._convert_firewall(firewall)
            firewall_nodes.append(firewall_node)

        server_nodes = []
        for server in self.servers:
            server_node = self._convert_server(server)
            server_nodes.append(server_node)

        nodes = []
        nodes.extend(network_nodes)
        nodes.extend(router_nodes)
        nodes.extend(firewall_nodes)
        nodes.extend(server_nodes)

        # 处理连接关系
        node_id_map = {}
        for node in nodes:
            node_id_map[node['id']] = node

        for node in nodes:
            node_id = node['id']
            connections = set()
            nets = node.pop('raw_nets')
            for net_id in nets:
                connected_node = node_id_map.get(net_id)
                if connected_node:
                    connections.add(connected_node['id'])
                    connected_node['connections'].add(node_id)
            node['connections'] = connections

        for node in nodes:
            node['connections'] = list(node['connections'])

        edges = self._generate_edges(node_id_map)

        data = {
            'nodes': nodes,
            'edges': edges,
        }
        if self.backend:
            data['scene'] = self.scene

        return data


def vis_to_backend(vis_config):
    handler = VisConfigHandler(vis_config)
    json_config = handler.convert()
    return json_config


def backend_to_vis(json_config, backend=True):
    handler = JsonConfigHandler(json_config, backend)
    vis_config = handler.convert()
    return vis_config