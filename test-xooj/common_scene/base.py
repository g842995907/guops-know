from __future__ import unicode_literals

import functools
import logging
import memcache
import os
import random
from retry import retry
import threading
import time
import urlparse

from django.utils.translation import ugettext as _

from neutronclient.common.exceptions import Conflict

from common_scene.clients.glance_client import Client as gl_client
from common_scene.clients.neutron_client import Client as nt_client
from common_scene.clients.nova_client import Client as nv_client
from common_scene.clients.zun_client import Client as zun_client
from common_scene.exception import FriendlyException
from common_scene.setting import api_settings
from common_scene import utils as project_utils


LOG = logging.getLogger(__name__)
ATTEMPTS = 600
ROLE_OPERATOR = "operator"
FLOATING_ROLE = [ROLE_OPERATOR, 'target']
EXTERNAL_NET = "external"
SNAPAHOT_PREFIX = "snapshot"
RESOURCE_TYPES = ['network', 'server', 'container', 'router', 'subnet', 'firewall']

USED_CIDR_KEY = "used_cidrs"
ALL_CIDR_KEY = "all_cidrs"
AVAILABLE_CIDR_KEY = "available_cidrs"
AVAILABLE_FIPS_KEY = "avialable_fips"
CPU_RATIO = api_settings.COMPLEX_MISC.get("cpu_allocation_ratio", 16.0)
RAM_RATIO = api_settings.COMPLEX_MISC.get("ram_allocation_ratio", 1.5)
DISK_RATIO = api_settings.COMPLEX_MISC.get("disk_allocation_ratio", 1.0)


def logger_decorator(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        func_name = func.__name__
        LOG.debug("Start {}(): args={}, kwargs={}".format(func_name,
                                                          args, kwargs))
        ff = func(self, *args, **kwargs)
        LOG.debug("End {}()".format(func_name))
        return ff
    return wrapper


def check_kwargs(*keys):
    def wrapper(func):
        @functools.wraps(func)
        def wrapped(self, *args, **kwargs):
            func_name = func.__name__
            LOG.debug("{}(): Check '{}' in kwargs ={}".format(func_name,
                                                              keys, kwargs))
            for key in keys:
                if not kwargs.has_key(key):
                    err_msg = "{}(): '{}' not in kwargs " \
                              "{}".format(func_name, key, kwargs.keys())
                    raise FriendlyException(err_msg)
            LOG.debug("{}(): Check success.".format(func_name))
            return func(self, *args, **kwargs)
        return wrapped
    return wrapper


class BaseSceneCreator(object):
    def __init__(self, request_id, **kwargs):
        self.request_id = request_id

        self.nova_cli = nv_client()
        self.glance_cli = gl_client()
        self.neutron_cli = nt_client()
        self.zun_cli = zun_client()
        self.mc = memcache.Client(api_settings.COMPLEX_MISC.get("memcache_host"))

        self.prefix = kwargs.get("prefix") or ""
        self.flags = kwargs.get("flags", [])
        self.attach_url = kwargs.get("attach_url")
        self.by_admin = kwargs.get("by_admin", False)

        self.roles = []
        self.temp_ips = []
        self.temp_users = {}
        self.temp_fw_ports = []
        self.pre_allocation_ips = {}
        self.pre_allocation_fips = []
        self.resources = {
            'routers': {},
            'networks': {},
            'subnets': {},
            'servers': {},
            'containers': {},
            'qoses': {},
            'firewalls': {}
        }
        self.errors = []

    def _handle_error(self, err_msg=None, e=None):
        if not err_msg:
            err_msg = _("Unknown error occurred, Please try again later.")
        if e:
            err_msg = "{}\n{}".format(err_msg, getattr(e, "message", ""))
        LOG.error(err_msg)
        self.errors.append(err_msg)
        raise FriendlyException(err_msg)

    @logger_decorator
    @check_kwargs("id")
    def create_router(self, **kwargs):
        rt_id = kwargs.get("id")
        name = kwargs.get("name")
        try:
            router = self.neutron_cli.router_create(name=name,
                                                    admin_state_up=True)
        except Exception, e:
            err_msg = _("Unable to create router {}.").format(name)
            self._handle_error(err_msg, e)

        LOG.info("Created router {} .".format(name))
        self.resources['routers'].update({rt_id: router})

        net_ids = kwargs.get("net")
        if net_ids:
            subnets = []
            for net_id in net_ids:
                if net_id == "openstack":
                    continue
                subnets.extend(self.resources.get("subnets").get(net_id))
            if subnets:
                params = {
                    "subnets": subnets,
                    "router": router
                }
                self.bind_subnets_to_router(**params)

        self.bind_extnet_to_router(router_id=router.get("id"))
        return router

    @logger_decorator
    def sync_cidr(self, cidr):
        used_cidrs = self.mc.get(USED_CIDR_KEY) or []
        if cidr in used_cidrs:
            used_cidrs.remove(cidr)
        else:
            used_cidrs.append(cidr)
        self.mc.set(USED_CIDR_KEY, used_cidrs)

        all_cidrs = self.mc.get(ALL_CIDR_KEY) or []
        self.mc.set(AVAILABLE_CIDR_KEY, list(set(all_cidrs) - set(used_cidrs)))
        LOG.info("cidr %s has been synced." % cidr)

    def _generate_cidr(self):
        cidrs = self.mc.get(AVAILABLE_CIDR_KEY)
        if cidrs:
            cidr = random.choice(cidrs)
            LOG.info("Get cidr {} from memcache".format(cidr))
            return cidr
        err_msg = _("Unable to get cidr from memcache.")
        self._handle_error(err_msg)

    def _get_default_dns(self):
        return api_settings.COMPLEX_MISC.get("dns_nameservers")

    def _generate_fixed_ips(self, servers):
        LOG.info("Gernate fixed ips ...")
        for server in servers:
            srv_nets = server.get("net") or ["openstack"]
            for srv_net in srv_nets:
                if srv_net.lower() == "openstack":
                    continue
                self.pre_allocation_ips.update(
                    {"{}.{}.ip".format(server.get("id"), srv_net):
                     self._get_fixed_ip(self.resources['networks'].get(srv_net))}
                )

    def _analysis_networks(self, res_id, nets, global_network=None, v4_ip=None):
        default_net = self._get_network_id(api_settings.COMPLEX_MISC.get("default_net"))
        if global_network:
            # ad model
            net_id = self._get_network_id(global_network)
            v4_ip = v4_ip if global_network != default_net else ""
            return [{"net-id": net_id, "v4-fixed-ip": v4_ip}]

        nics = []
        for net in nets:
            if isinstance(net, str) or isinstance(net, unicode):
                net_key = net
            elif isinstance(net, dict):
                net_key = net.get("id")

            if net_key.lower() == "openstack":
                net_id = default_net
                v4_ip = ""
            else:
                net_id = self.resources['networks'].get(net_key).get("id")
                v4_ip = self.pre_allocation_ips.get("{}.{}.ip".format(res_id, net)) \
                            or self._get_fixed_ip(net_id)
            nics.append({"net-id": net_id, "v4-fixed-ip": v4_ip})
        return nics

    @logger_decorator
    @check_kwargs("id")
    def create_network(self, **kwargs):
        id = kwargs.get("id")
        name = kwargs.get("name")
        try:
            net = self.neutron_cli.network_create(name=name,
                            admin_state=kwargs.get("admin_state") or "True",
                            shared=kwargs.get("shared") or False)
        except Exception, e:
            err_msg = _("Unable to create network {}.").format(name)
            self._handle_error(err_msg, e)

        LOG.info("Created network {} .".format(name))
        self.resources['networks'].update({id: net})

        subnet = None
        if kwargs.get("create_subnet", True):
            params = {
                'name': name + "_sub",
                'cidr': kwargs.get("cidr") or self._generate_cidr(),
                'enable_dhcp': kwargs.get("enable_dhcp"),
                'dns_nameservers': kwargs.get("dns_nameservers") or \
                                   self._get_default_dns()
            }
            subnet = self.create_subnet(net, **params)
            self.resources['subnets'].update({id: [subnet]})
        return net, subnet

    @logger_decorator
    def create_subnet(self, network, **kwargs):
        net_id = network.get("id")
        name = kwargs.get("name")
        cidr = kwargs.get("cidr")
        try:
            subnet = self.neutron_cli.subnet_create(
                            net_id, name=name, cidr=cidr,
                            enable_dhcp=kwargs.get("enable_dhcp") or True,
                            dns_nameservers=kwargs.get("dns_nameservers"))
        except Exception, e:
            if e.message.find("overlaps with another subnet.") >= 0:
                self.sync_cidr(cidr)
                err_msg = _("Network {} with cidr {} "
                            "already exists.").format(net_id, cidr)
            else:
                err_msg = _("Unable to create subnet {}.").format(cidr)
            self._handle_error(err_msg, e)

        LOG.info("Subnet {} with cidr{} created.".format(name, cidr))
        self.resources['subnets'].update({net_id: subnet})
        self.sync_cidr(cidr)
        return subnet

    def _is_compute_target(self, port):
        if port['device_owner'].startswith('compute:') and \
                not port['device_owner'].startswith('compute:kuryr'):
            return True
        return False

    def _is_docker_target(self, port):
        if port['device_owner'].startswith('compute:kuryr'):
            return True
        return False

    def _is_router_if_target(self, port):
        if port['device_owner'].startswith('network:router_interface'):
            return True
        return False

    def _get_ports(self, instance=None, network=None):
        params = {}
        if instance:
            params.update({"device_id":instance.id})
        if network:
            params.update({"network_id": network.get("id")})

        try:
            return self.neutron_cli.port_list(**params)
        except Exception, e:
            err_msg = _("Unable to get ports for resource "
                        "{}.").format(network.get("id", getattr(instance, "id")))
            self._handle_error(err_msg, e)

    def get_scene_router_ifs(self, net_keys):
        router_ifs = []
        for key in net_keys:
            net = self.resources["networks"].get(key)
            ports = self._get_ports(network=net)
            router_ifs.extend([p.get("id") for p in ports
                               if self._is_router_if_target(p)])
        return router_ifs

    @logger_decorator
    def create_firewall_rules(self, rules):
        fw_rules = []
        for rule in rules:
            try:
                rule = self.neutron_cli.firewall_rule_create(**rule)
                fw_rules.append(rule)
            except Exception, e:
                err_msg = _("Unable to create firewall "
                            "rule {}.").format(rule.get("name"))
                self._handle_error(err_msg, e)
        return fw_rules

    @logger_decorator
    def create_firewall_policy(self, **policy):
        try:
            return self.neutron_cli.firewall_policy_create(**policy)
        except Exception, e:
            err_msg = _("Unable to create firewall "
                        "policy {}.").format(policy.get("name"))
            self._handle_error(err_msg, e)

    @logger_decorator
    def insert_firewall_rules(self, policy_id, rules):
        for rule in rules:
            try:
                self.neutron_cli.firewall_policy_insert_rule(
                    policy_id, firewall_rule_id=rule.get("id"))
            except Exception, e:
                err_msg = _("Unable to create insert firewall rule {} "
                            "to policy {}.").format(rule.get("id"), policy_id)
                self._handle_error(err_msg, e)

    @logger_decorator
    def create_firewall(self, **kwargs):
        fw_id = kwargs.get("id")
        name = kwargs.get("name", "firewall-{}".format(fw_id))

        ingress_rules_list = []
        egress_rules_list = []

        rules = kwargs.get("rule")
        for idx, rule in enumerate(rules):
            direction = rule.get("direction")
            rule_name = "{}-rule-{}".format(fw_id, idx)
            rule = {
                "protocol": rule.get("protocol"),
                "action": rule.get("action"),
                "source_ip_address": rule.get("sourceIP"),
                "source_port": rule.get("sourcePort"),
                "destination_ip_address": rule.get("destIP"),
                "destination_port": rule.get("destPort")
            }
            if direction == "ingress":
                rule.update({"name": "{}-ingress".format(rule_name)})
                ingress_rules_list.append(rule)
            elif direction == "egress":
                rule.update({"name": "{}-egress".format(rule_name)})
                egress_rules_list.append(rule)
            else:
                rule.update({"name": "{}-ingress".format(rule_name)})
                ingress_rules_list.append(rule)
                rule.update({"name": "{}-egress".format(rule_name)})
                egress_rules_list.append(rule)

        ingress_policy_dict = {"name": "{}-policy-ingress".format(fw_id)}
        egress_policy_dict = {"name": "{}-policy-egress".format(fw_id)}
        firewall_dict = {"name": name}

        ingress_rules = self.create_firewall_rules(ingress_rules_list)
        if ingress_rules:
            ingress_policy_dict.update({"firewall_rules": [r.get("id") for r in ingress_rules]})
            ingress_policy = self.create_firewall_policy(**ingress_policy_dict)
            firewall_dict.update({"ingress_firewall_policy_id": ingress_policy.get("id")})

        egress_rules = self.create_firewall_rules(egress_rules_list)
        if egress_rules:
            egress_policy_dict.update({"firewall_rules": [r.get("id") for r in egress_rules]})
            egress_policy = self.create_firewall_policy(**egress_policy_dict)
            firewall_dict.update({"egress_firewall_policy_id": egress_policy.get("id")})

        ports = self.get_scene_router_ifs(kwargs.get("net"))
        if ports:
            firewall_dict.update({"ports": ports})

        try:
            firewall = self.neutron_cli.firewall_create(**firewall_dict)
            self.resources['firewalls'].update({fw_id: firewall})
            return firewall
        except Exception, e:
            err_msg = _("Unable to create firewall {}").format(id)
            self._handle_error(err_msg, e)

    def bind_port_qos_policy(self, port_id, policy_id):
        try:
            self.neutron_cli.port_update(
                        port_id, qos_policy_id=policy_id)
        except Exception, e:
            err_msg = _("Unable to bind qos policy {} "
                        "to port {}").format(policy_id, port_id)
            self._handle_error(err_msg, e)

    def bind_ports_qos_policy(self, port_ids, policy_id):
        for port_id in port_ids:
            self.bind_port_qos_policy(port_id, policy_id)

    def _get_image(self, image_name, snapshot=None):
        if snapshot:
            LOG.info('snapshot name: {}'.format(snapshot))
            image_obj = self.glance_cli.image_get_by_name(snapshot)
            if image_obj and image_obj.status.lower() == "active":
                return True, image_obj
            LOG.debug("Snapshot {} status not active, "
                      "Use image {} instead.".format(snapshot, image_name))

        image_obj = self.glance_cli.image_get_by_name(image_name)
        if not image_obj:
            err_msg = _("Image {} not found.").format(image_name)
            self._handle_error(err_msg)
        if image_obj.status.lower() != "active":
            err_msg = _("Image {} status not active.").format(image_name)
            self._handle_error(err_msg)
        return False, image_obj

    def _get_flavor(self, image_type=None, flavor_name=None):
        flavor = None
        if flavor_name:
            flavor = self.nova_cli.flavor_get_by_name(flavor_name)

        if not flavor:
            LOG.info("Flavor not found, use default flavor.")
            if image_type and image_type == "windows":
                flavor = self.nova_cli.flavor_get_by_name(
                            api_settings.COMPLEX_MISC.get("windows_flavor"))
            else:
                flavor = self.nova_cli.flavor_get_by_name(
                            api_settings.COMPLEX_MISC.get("linux_flavor"))
        return flavor

    def _get_security_groups(self):
        return api_settings.COMPLEX_MISC.get("security_groups", ['default'])

    def _get_network_id(self, net):
        if project_utils.is_uuid_like(net):
            return net

        network = self.neutron_cli.network_get_by_name(net)
        if network:
            return network.get("id")
        return None

    def _get_fixed_ip(self, net):
        if hasattr(net, "has_key"):
            net_id = net.get("id")
        else:
            net_id = net.id if hasattr(net, "id") else net
        subnets = self.neutron_cli.subnet_get_all(network_id=net_id)

        if subnets:
            # default use subnet 0
            subnet = subnets[0]
            cidr = subnet.get("cidr")
            host_bit_range = range(50, 200)
            attemps = 1
            while attemps < 20:
                host_bit = random.choice(host_bit_range)
                fixed_ip = "{}{}".format(cidr[:-4], host_bit)

                if fixed_ip not in self.temp_ips:
                    LOG.info("Get a fixed ip {}.".format(fixed_ip))
                    self.temp_ips.append(fixed_ip)
                    return fixed_ip
                host_bit_range.remove(host_bit)
                attemps += 1
        err_msg = _("Unable to get fixed ip for net {}.").format(net_id)
        self._handle_error(err_msg)

    def _delete_port(self, port):
        try:
            self.neutron_cli.port_delete(port.get("id"))
        except Exception, e:
            err_msg = _('Failed to delete port {}').format(port.get("id"))
            self._handle_error(err_msg, e)

    def _add_interface_by_subnet(self, router_id, subnet_id):
        try:
            router_inf = self.neutron_cli.router_interface_add(
                                        router_id, subnet_id=subnet_id)
        except Exception as e:
            raise
        try:
            port = self.neutron_cli.port_get(router_inf['port_id'])
        except Exception:
            port = None
        return port

    @retry(tries=20, delay=1)
    def _add_interface_by_port(self, router_id, subnet_id):
        ip_address = self._generate_gw_addr(subnet_id)

        try:
            subnet = self.neutron_cli.subnet_get(subnet_id)
        except Exception, e:
            err_msg = _('Unable to get subnet {}').format(subnet_id)
            self._handle_error(err_msg, e)
        try:
            body = {'network_id': subnet.get("network_id"),
                    'fixed_ips': [{'subnet_id': subnet.get("id"),
                                   'ip_address': ip_address}]}
            port = self.neutron_cli.port_create(**body)
        except Exception as e:
            err_msg = _('Unable to create port for '
                        'subnet {}.').forrmat(subnet_id)
            self._handle_error(err_msg, e)

        try:
            self.neutron_cli.router_interface_add(router_id,
                                                  port_id=port.get("id"))
        except Exception as e:
            err_msg = _('Unable to bind port {} to router '
                        '{} .').format(port.get("id"), router_id)
            self._delete_port(port)
            self._handle_error(err_msg, e)
        return port

    def _generate_gw_addr(self, subnet_id):
        subnet = self.neutron_cli.subnet_get(subnet_id)
        cidr_net_seg = subnet.get("cidr")[:-4]

        ports = self.neutron_cli.port_list(network_id=subnet.get("network_id"))
        used_ips = []
        for port in ports:
            for fixed_ip in port.get("fixed_ips"):
                used_ips.append(fixed_ip.get("ip_address"))

        gw_addr = 254
        while gw_addr > 0:
            gw_ip = "{}{}".format(cidr_net_seg, gw_addr)
            if gw_ip not in used_ips:
                return gw_ip
            gw_addr -= 1

        err_msg = _("No more address can be used for "
                    "gateway in subnet {}.").format(subnet_id)
        self._handle_error(err_msg)

    @logger_decorator
    @check_kwargs("router_id", "subnet_id")
    def bind_subnet_to_router(self, **kwargs):
        router_id = kwargs.get("router_id")
        subnet_id = kwargs.get("subnet_id")
        try:
            port = self._add_interface_by_subnet(router_id, subnet_id)
            LOG.info("Connected subnet {} to "
                     "router {} .".format(subnet_id, router_id))
            return port
        except Conflict:
            return self._add_interface_by_port(router_id, subnet_id)
        except Exception, e:
            err_msg = _("Unable to connect subnet {} "
                        "to router {}.").format(subnet_id, router_id)
            self._handle_error(err_msg, e)
        return None

    @logger_decorator
    @check_kwargs("router_id")
    @retry(tries=3, delay=1)
    def bind_extnet_to_router(self, **kwargs):
        router_id = kwargs.get("router_id")
        extnet_id = kwargs.get("net_id") or \
                    api_settings.COMPLEX_MISC.get("external_net")
        try:
            self.neutron_cli.router_add_gateway(router_id, extnet_id)
            LOG.info("Router {} connected to the extrenal network .".format(router_id))
        except Exception, e:
            err_msg = _("Unable to connect external network "
                        "for router {}").format(router_id)
            self._handle_error(err_msg, e)

    def _need_floating_ip(self, role):
        if self.by_admin or role == ROLE_OPERATOR or \
                (role in FLOATING_ROLE and ROLE_OPERATOR not in self.roles):
            return True
        return False

    def _load_available_fips(self):
        avialable_fips = {}
        fips = self.neutron_cli.floating_ip_list()
        for fip in fips:
            if not fip.get("instance_id"):
                avialable_fips.update({fip.get("floating_ip_address"): fip})
        self.mc.set(AVAILABLE_FIPS_KEY, avialable_fips)

    def _generate_fip(self):
        self._load_available_fips()

        try:
            pools = self.neutron_cli.floating_ip_pools_list()
        except Exception, e:
            err_msg = _("Unable to retrieve floating IP pools.")
            self._handle_error(err_msg, e)

        try:
            return self.neutron_cli.floating_ip_allocate(pools[0].get("id")).get("id")
        except Exception, e:
            err_msg = _("Unable to generate floating ip. {}").format(e)
            self._handle_error(err_msg, e)

    @retry(tries=3, delay=1)
    def _get_fip(self):
        fips = self.mc.get(AVAILABLE_FIPS_KEY)
        if fips:
            fip = fips.popitem()
            self.mc.set(AVAILABLE_FIPS_KEY, fips)
            return fip

        return self._generate_fip()

    def _bind_fip(self, fip, port=None, instance=None):
        type = "port" if port else "instance"
        try:
            port_id = port or self.neutron_cli.get_target_id_by_instance(instance.id)
            fip_obj = self.neutron_cli.floating_ip_associate(fip.get("id"),
                                                             port_id)
            LOG.info("Bind floating ip {} to {} {}.".format(
                            fip.get("floating_ip_address"), type, port or instance.id))
            return fip_obj
        except Exception, e:
            err_msg = _("Unable to bind fip {} for {} {}").format(
                            fip.get("floating_ip_address"), type, port or instance.id)
            self._handle_error(err_msg, e)

    @logger_decorator
    def bind_floating_ip(self, port=None, instance=None):
        return self._bind_fip(self._get_fip(), port=port, instance=instance)

    @logger_decorator
    def create_resources_async(self, type, resources):
        if type not in RESOURCE_TYPES:
            err_msg = _("Type ({}) not in legal resource "
                        "types ({})").format(type, RESOURCE_TYPES)
            self._handle_error(err_msg)

        create_threads = []
        for resource in resources:
            try:
                create_threads.append(threading.Thread(
                    target=getattr(self, "create_{}".format(type)), kwargs=resource))
            except Exception as e:
                err_msg = _("Unable to create resource : {}").format(resource)
                self._handle_error(err_msg, e)

        for t in create_threads:
            t.start()

        for t in create_threads:
            t.join()

        while 1:
            running_threads = [t for t in create_threads if t.isAlive()]
            if running_threads:
                time.sleep(0.1)
                continue
            else:
                break

        if self.errors:
            pass

    @logger_decorator
    @check_kwargs("servers")
    def quota_check(self, **kwargs):
        servers = kwargs.get("servers", [])
        vcpu_allowance = 0
        ram_allowance = 0
        disk_allowance = 0
        fip_allowance = 0

        ext_nets = self.neutron_cli.ext_networks_list()
        for ext_net in ext_nets:
            net_availability = self.neutron_cli.show_network_ip_availability(ext_net.get("id"))
            fip_allowance += (net_availability.get("total_ips", 0) -
                              net_availability.get("used_ips", 0))
        avail_fips = self.mc.get("avialable_fips")
        if not avail_fips:
            self._load_available_fips()
            avail_fips = self.mc.get("avialable_fips")
        fip_allowance += len(avail_fips)

        try:
            hypervisors = self.nova_cli.hypervisor_list()
        except Exception, e:
            err_msg = _("Unable to retire hypervisors.")
            self._handle_error(err_msg, e)

        for hyperv in hypervisors:
            vcpu_allowance += (hyperv.vcpus * CPU_RATIO - hyperv.vcpus_used)
            ram_allowance += (hyperv.memory_mb * RAM_RATIO - hyperv.memory_mb_used)
            disk_allowance += (hyperv.local_gb * DISK_RATIO - hyperv.local_gb_used)

        cpu_count = 0
        ram_count = 0
        disk_count = 0
        fip_count = 0
        for vm in servers:
            if self.by_admin or vm.get("role") in FLOATING_ROLE:
                fip_count += 1
            image_type = vm.get("imageType")
            flavor = self._get_flavor(image_type, vm.get("flavor"))
            cpu_count += flavor.vcpus
            ram_count += flavor.ram
            disk_size = flavor.disk
            if not disk_size:
                image = self._get_image(image_name=vm.get("image"))
                disk_size = getattr(image, "min_disk", 0)
            disk_count += disk_size

        if fip_allowance >= fip_count:
            LOG.debug("Check floating ip quota: OK .")
        else:
            err_msg = _("Check floating ip quota: Error . Required ({}) > "
                        "Allowance ({}))").format(fip_count, fip_allowance)
            LOG.error(err_msg)
            self.errors.append(err_msg)
            raise FriendlyException(err_msg)

        if vcpu_allowance >= cpu_count:
            LOG.debug("Check vcpu quota: OK")
        else:
            err_msg = _("Check vcpu quota: Error . Required ({}) > "
                        "Allowance ({}))").format(cpu_count, vcpu_allowance)
            self._handle_error(err_msg)

        if ram_allowance >= ram_count:
            LOG.debug("Check memory quota: OK")
        else:
            err_msg = _("Check memory quota: Error . Required ({}) > "
                        "Allowance ({}))").format(ram_count, ram_allowance)
            self._handle_error(err_msg)

        if disk_allowance >= disk_count:
            LOG.debug("Check disk quota: OK")
        else:
            err_msg = _("Check disk quota: Error . Required ({}) > "
                        "Allowance ({}))").format(disk_count, disk_allowance)
            self._handle_error(err_msg)
        LOG.info("Check quota: Success")

    @logger_decorator
    def create_networks(self, **kwargs):
        self.create_resources_async("network", kwargs.get("networks", []))

    @logger_decorator
    def create_routers(self, **kwargs):
        self.create_resources_async("router", kwargs.get("routers", []))

    @logger_decorator
    @check_kwargs("subnets", "router")
    def bind_subnets_to_router(self, **kwargs):
        bind_threads = []
        for subnet in kwargs.get("subnets", []):
            params = {"router_id": kwargs.get("router").get("id"),
                      "subnet_id": subnet.get("id")}
            bind_threads.append(threading.Thread(target=self.bind_subnet_to_router,
                                                 kwargs=params))

        for t in bind_threads:
            t.start()

        for t in bind_threads:
            t.join()

    @logger_decorator
    def create_firewalls(self, **kwargs):
        self.create_resources_async("firewall", kwargs.get("firewalls", []))

    @logger_decorator
    def create_servers(self, **kwargs):
        servers = kwargs.get("servers", [])
        self.roles = [srv.get("role") for srv in servers]
        self.create_resources_async("server", servers)

    @logger_decorator
    def create_containers(self, **kwargs):
        containers = kwargs.get("containers", [])
        self.roles = [cont.get("role") for cont in containers]
        self.create_resources_async("container", containers)


class BaseSceneDeleter(object):
    resource_types = ['server', 'image', 'router', 'network', 'container', 'firewall', 'qos']

    def __init__(self, *args, **kwargs):
        self.glance_cli = gl_client()
        self.neutron_cli = nt_client()

        self.mc = memcache.Client(api_settings.COMPLEX_MISC.get("memcache_host"))

    def _sync_cidr(self, cidr):
        used_ips = self.mc.get(USED_CIDR_KEY) or []
        if cidr in used_ips:
            used_ips.remove(cidr)
        else:
            used_ips.append(cidr)
        self.mc.set(USED_CIDR_KEY, used_ips)

        all_ips = self.mc.get(ALL_CIDR_KEY) or []
        self.mc.set(AVAILABLE_CIDR_KEY, list(set(all_ips) - set(used_ips)))
        LOG.info("cidr %s has been synced." % cidr)

    @logger_decorator
    def delete_image(self, image_id):
        try:
            self.glance_cli.image_delete(image_id)
            LOG.info("Successfully deleted image {}".format(image_id))
        except Exception, e:
            err_msg = _("Unable to delete image {}.").format(image_id)
            LOG.error(err_msg)
            LOG.error(e)

    @logger_decorator
    def delete_network(self, network_id):
        try:
            self.neutron_cli.network_delete(network_id)
            LOG.info("Successfully deleted network {}".format(network_id))
        except Exception, e:
            err_msg = _("Unable to delete network {}.").format(network_id)
            LOG.error(err_msg)
            LOG.error(e)

    @logger_decorator
    def disconnect_ports(self, router_id):
        ports = self.neutron_cli.port_list(device_id=router_id)
        for port in ports:
            try:
                if port['device_owner'] == 'network:router_gateway':
                    self.neutron_cli.router_remove_gateway(router_id)
                else:
                    self.neutron_cli.router_interface_delete(
                        router_id, port_id=port.get("id"))
                LOG.info("Successfully deleted port {} in "
                         "router {}".format(port.get("id"), router_id))
            except Exception, e:
                err_msg = _("Unable to delete "
                            "port {}.").format(port.get("id"))
                LOG.error(err_msg)
                LOG.error(e)

    @logger_decorator
    def delete_router(self, router_id):
        self.disconnect_ports(router_id)

        try:
            self.neutron_cli.router_delete(router_id)
            LOG.info("Successfully deleted router {}".format(router_id))
        except Exception, e:
            err_msg = _("Unable to delete router {}.").format(router_id)
            LOG.error(err_msg)
            LOG.error(e)

    def delete_firewall_rule(self, rule_id):
        try:
            self.neutron_cli.firewall_rule_delete(rule_id)
        except Exception, e:
            err_msg = _("Unable to delete firewall rule {}.").format(rule_id)
            LOG.error(err_msg)
            LOG.error(e)

    def delete_firewall_policy(self, policy_id):
        try:
            policy = self.neutron_cli.firewall_policy_get(policy_id)
            rules = policy.get("rules")
            for rule in rules:
                self.delete_firewall_rule(rule.get("id"))
            self.neutron_cli.firewall_policy_delete(policy.get("id"))
        except Exception, e:
            err_msg = _("Unable to delete firewall policy {}.").format(policy_id)
            LOG.error(err_msg)
            LOG.error(e)

    @logger_decorator
    def delete_firewall(self, firewall_id):
        try:
            firewall = self.neutron_cli.firewall_get(firewall_id)
            ingress_policy = firewall.get("ingress_policy")
            egress_policy = firewall.get("egress_policy")
            if ingress_policy:
                self.delete_firewall_policy(ingress_policy.get("id"))
            if egress_policy:
                self.delete_firewall_policy(egress_policy.get("id"))
            self.neutron_cli.firewall_delete(firewall_id)
        except Exception, e:
            err_msg = _("Unable to delete firewall {}.").format(firewall_id)
            LOG.error(err_msg)
            LOG.error(e)

    @logger_decorator
    def delete_qos(self, policy_id):
        try:
            rules = self.neutron_cli.qos_bandwidth_limit_rule_list(policy_id)
            for rule in rules:
                self.neutron_cli.qos_bandwidth_limit_rule_delete(rule.get("id"), policy_id)
            self.neutron_cli.qos_policy_delete(policy_id)
        except Exception, e:
            err_msg = _("Unable to delete qos policy {}.").format(policy_id)
            LOG.error(err_msg)
            LOG.error(e)

    @logger_decorator
    def delete_resources_async(self, type, resources):
        if type in self.resource_types:
            err_msg = _("Type ({}) not in legal resource "
                        "types ({})").format(type, RESOURCE_TYPES)
            LOG.error(err_msg)
            return False

        delete_threads = []
        for resource in resources:
            try:
                delete_threads.append(threading.Thread(
                    target=getattr(self, "delete_{}".format(type)), args=(resource)))
            except Exception as e:
                err_msg = _("Unable to delete resource : {}").format(resource)
                LOG.error(err_msg)

        for t in delete_threads:
            t.start()

        for t in delete_threads:
            t.join()

    @logger_decorator
    def delete_images(self, image_ids):
        self.delete_resources_async("image", image_ids)

    @logger_decorator
    def delete_servers(self, server_ids):
        self.delete_resources_async("server", server_ids)

    @logger_decorator
    def delete_routers(self, router_ids):
        self.delete_resources_async("router", router_ids)

    @logger_decorator
    def delete_networks(self, network_ids):
        self.delete_resources_async("network", network_ids)

    @logger_decorator
    def delete_firewalls(self, firewall_ids):
        self.delete_resources_async("firewall", firewall_ids)

    @logger_decorator
    def delete_qoses(self, qos_ids):
        self.delete_resources_async("qos", qos_ids)

    @logger_decorator
    def delete_containers(self, container_ids):
        self.delete_resources_async("container", container_ids)


class BaseSceneRollbacker(BaseSceneDeleter):
    def __init__(self, *args, **kwargs):
        super(BaseSceneRollbacker, self).__init__(*args, **kwargs)

    @logger_decorator
    def rollback_images(self, images):
        image_ids = []
        for image_key, image in images.items():
            image_ids.append(image.get("id"))
        self.delete_resources_async("image", image_ids)

    @logger_decorator
    def rollback_servers(self, servers):
        server_ids = []
        for server_key, server in servers.items():
            server_ids.append(server.get("id"))
        self.delete_resources_async("server", server_ids)

    @logger_decorator
    def rollback_routers(self, routers):
        router_ids = []
        for router_key, router in routers.items():
            router_ids.append(router.get("id"))
        self.delete_resources_async("router", router_ids)

    @logger_decorator
    def rollback_networks(self, networks):
        network_ids = []
        for network_key, network in networks.items():
            network_ids.append(network.get("id"))
        self.delete_resources_async("network", network_ids)

    @logger_decorator
    def rollback_firewalls(self, firewalls):
        firewall_ids = []
        for firewall_key, firewall in firewalls.items():
            firewall_ids.append(firewall.get("id"))
        self.delete_resources_async("firewall", firewall_ids)

    @logger_decorator
    def rollback_qoses(self, qoses):
        qos_ids = []
        for qos_key, qos in qoses.items():
            qos_ids.append(qos.get("id"))
        self.delete_resources_async("qos", qos_ids)

    @logger_decorator
    def rollback_containers(self, containers):
        container_ids = []
        for container_key, container in containers.items():
            container_ids.append(container.get("uuid"))
        self.delete_resources_async("container", container_ids)


class BaseSceneTemplater(object):
    resource_types = ['server', 'image', 'router', 'network', 'container', 'firewall']
    actions = ['delete', 'create', 'snapshot']

    def __init__(self, *args, **kwargs):
        self.glance_cli = gl_client()
        self.nova_cli = nv_client()
        self.errors = []

    def _handle_error(self, err_msg=None, e=None):
        if not err_msg:
            err_msg = _("Unknown error occurred, Please try again later.")
        if e:
            err_msg = "{}\n{}".format(err_msg, getattr(e, "message", ""))
        LOG.error(err_msg)
        raise FriendlyException(err_msg)

    def _get_flavor(self, name=None, image_type=None):
        if not name:
            if image_type:
                name = api_settings.COMPLEX_MISC.get("%s_flavor" % image_type)
                LOG.debug("Flavor not set, use default flavor {}.".format(name))
            else:
                err_msg = "Flavor not set, image_type need"
                self._handle_error(err_msg)

        flavor = self.nova_cli.flavor_get_by_name(name)
        if not flavor:
            if image_type:
                LOG.debug("Flavor {} not found, use "
                          "default flavor.".format(name))
                flavor = self.nova_cli.flavor_get_by_name(
                            api_settings.COMPLEX_MISC.get("%s_flavor" % image_type))
            else:
                err_msg = "Flavor {} not found".format(name)
                self._handle_error(err_msg)
        return flavor

    def operate_resources_async(self, action, type, resources):
        if action not in self.actions:
            err_msg = _("Action ({}) not allowed. "
                        "({})").format(action, self.actions)
            self._handle_error(err_msg)

        if type not in self.resource_types:
            err_msg = _("Type ({}) not in legal resource "
                        "types ({})").format(type, self.resource_types)
            self._handle_error(err_msg)

        action_threads = []
        for resource in resources:
            try:
                action_threads.append(threading.Thread(
                    target=getattr(self, "{}_template_{}".format(action, type)),
                    kwargs=resource))
            except Exception as e:
                err_msg = _("Unable to {} {} resource : "
                            "{}").format(action, type, resource)
                self._handle_error(err_msg, e)

        for t in action_threads:
            t.start()

        for t in action_threads:
            t.join()

    def create_template_servers(self, **kwargs):
        self.operate_resources_async("create", "server", kwargs.get("servers"))

    def create_template_containers(self, **kwargs):
        self.operate_resources_async("create", "container", kwargs.get("containers"))

    def snapshot_template_servers(self, servers):
        self.operate_resources_async("snapshot", "server", servers)

    def snapshot_template_containers(self, containers):
        self.operate_resources_async("snapshot", "container", containers)

    def delete_template_servers(self, servers):
        self.operate_resources_async("delete", "server", servers)

    def delete_template_containers(self, containers):
        self.operate_resources_async("delete", "container", containers)

    def delete_scene_snapshots(self, snapshots=None, request_id=None):
        snapshot_list = []
        if snapshots:
            snapshot_list = snapshots
        elif request_id:
            snapshots = self.glance_cli.images_list_by_name(
                            "{}-{}-".format(SNAPAHOT_PREFIX, request_id))
            snapshot_list = [s.id for s in snapshots]

        for snapshot_id in snapshot_list:
            try:
                self.glance_cli.image_delete(snapshot_id)
            except Exception, e:
                err_msg = _("Unable to delete snapshot {}").format(snapshot_id)
                LOG.error(err_msg)
                LOG.error(e)
        return True


class BaseADSceneCreator(BaseSceneCreator):
    def __init__(self, contest_id, **kwargs):
        super(BaseADSceneCreator, self).__init__(contest_id, **kwargs)
        self.contest_id = contest_id

    @logger_decorator
    def create_network(self, **kwargs):
        id = kwargs.get("id")
        name = kwargs.get("name")
        try:
            net = self.neutron_cli.network_create(name=name,
                            admin_state=kwargs.get("admin_state", "True"),
                            shared=kwargs.get("shared"))
        except Exception, e:
            err_msg = _("Unable to create network {}.").format(name)
            self._handle_error(err_msg, e)

        LOG.info("Created network {} .".format(name))
        self.resources['networks'].update({id: net})
        return net

    @logger_decorator
    def create_subnets(self, net_id, subnets):
        create_threads = []
        for subnet in subnets:
            try:
                create_threads.append(threading.Thread(
                    target=getattr(self, "create_subnet"), args=(net_id), kwargs=subnet))
            except Exception as e:
                err_msg = _("Unable to create subnet : {}").format(subnet)
                self._handle_error(err_msg, e)

        for t in create_threads:
            t.start()

        for t in create_threads:
            t.join()


class BaseADSceneDeleter(BaseSceneDeleter):
    def __init__(self, *args, **kwargs):
        super(BaseADSceneDeleter, self).__init__(*args, **kwargs)

