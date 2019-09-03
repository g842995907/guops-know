from __future__ import unicode_literals

import functools
import logging
import time
import uuid

from django.core.cache import cache
from django.utils.translation import ugettext as _

from novaclient import exceptions

from common_scene.clients.nova_client import Client as nv_client
from common_scene.exception import FriendlyException
from common_scene.utils import get_ip_by_hostname


LOG = logging.getLogger(__name__)
ATTEMPTS = 1200
WINDOWS = "windows"
LINUX = "linux"
HYPERVISOR_CACHE_KEY = "os_all_hypervisors_key"


def logger_decorator(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        func_name = func.__name__
        LOG.debug("[OPENSTACK] Start {}(): args={}, kwargs={}".format(func_name,
                                                          args, kwargs))
        ff = func(self, *args, **kwargs)
        LOG.debug("[OPENSTACK] End {}()".format(func_name))
        return ff
    return wrapper


def clean_create_params(func):
    @functools.wraps(func)
    def wrapper(self, **kwargs):
        body = {}
        body['name'] = kwargs.get("name")
        body['image'] = self._get_image(kwargs.get("image"))
        body['flavor'] = self._get_flavor(kwargs.get("flavor"))
        body['nics'] = kwargs.get("net")
        body['security_groups'] = self._get_sgs(kwargs.get("security_groups"))
        body['key_name'] = self._get_keypairs(kwargs.get("key_name"))
        body['user_data'] = self._get_userdata(kwargs.get("user_data"))
        body['availability_zone'] = kwargs.get("availability_zone")

        return func(self, **body)
    return wrapper


class InstanceAction(object):
    def __init__(self):
        super(InstanceAction, self).__init__()

    @property
    def nova_cli(self):
        if not hasattr(self, '_nova_cli'):
            self._nova_cli = nv_client()
        return self._nova_cli

    def _handle_error(self, err_msg=None, e=None):
        if not err_msg:
            err_msg = _("Unknown error occurred, Please try again later.")
        if e:
            err_msg = "{}\n{}".format(err_msg, getattr(e, "message", ""))
        LOG.error("[OPENSTACK] {}".format(err_msg))
        raise FriendlyException(err_msg)

    @logger_decorator
    def list_server(self, **kwargs):
        prefix = kwargs.pop("prefix") if kwargs.has_key("prefix") else None
        try:
            servers = self.nova_cli.instance_get_all(**kwargs)
        except Exception as e:
            err_msg = _("Unable to list servers "
                        "by kwargs {}").format(kwargs)
            self._handle_error(err_msg, e)
        if prefix and servers:
            return [server for server in servers
                    if server.name.startswith(prefix.strip())]
        return servers

    @logger_decorator
    def create_server(self, **kwargs):
        try:
            return self.nova_cli.instance_create(
                kwargs.get("name"),
                kwargs.get("image"),
                kwargs.get("flavor"),
                kwargs.get("key_name"),
                kwargs.get("user_data"),
                kwargs.get("security_groups"),
                nics=kwargs.get("nics"),
                availability_zone=kwargs.get("availability_zone"),
                block_device_mapping_v2=kwargs.get("block_device_mapping_v2"))
        except Exception as e:
            err_msg = _("Unable to create instance {}").format(kwargs.get("name"))
            self._handle_error(err_msg, e)

    def get_host_ip(self, hostname):
        hyper_dict = cache.get(HYPERVISOR_CACHE_KEY) or {}
        if not hyper_dict:
            hypers = self.nova_cli.hypervisor_list()
            for hyper in hypers:
                hyper_dict.update({hyper.hypervisor_hostname: hyper.host_ip})
            cache.set(HYPERVISOR_CACHE_KEY, hyper_dict)

        host_ip = hyper_dict.get(hostname)
        return host_ip

    @logger_decorator
    def get_server(self, instance_id, convert_host_ip=True):
        try:
            server = self.nova_cli.instance_get_by_id(instance_id)
        except Exception as e:
            err_msg = _("Unable to get instance {}").format(instance_id)
            self._handle_error(err_msg, e)

        if convert_host_ip:
            hostname = getattr(server, "OS-EXT-SRV-ATTR:hypervisor_hostname")
            if hostname:
                setattr(server, "host_ip_address", get_ip_by_hostname(hostname))

        return server

    @logger_decorator
    def check_server_task_state(self, inst_id, return_on="spawning"):
        attempts = 60
        while 1:
            if attempts <= 0:
                err_msg = _("Failed to check task_state for instance {}: "
                            "The maximum number of attempts "
                            "has been exceeded.").format(inst_id)
                break
            server = self.get_server(inst_id)
            task_state = getattr(server, "OS-EXT-STS:task_state", "none")
            if task_state is None or task_state == return_on:
                msg = "Instance {} task_state {}.".format(inst_id, return_on)
                LOG.info(msg)
                return server
            LOG.debug("Instance status not active. "
                      "Try again 1 second later...")
            attempts -= 1
            time.sleep(1)
        self._handle_error(err_msg)

    @logger_decorator
    def check_server_status(self, inst, return_on="ACTIVE"):
        inst_id = inst.id if hasattr(inst, "id") else inst
        inst_name = getattr(inst, "name", None) or inst_id

        attempts = ATTEMPTS
        while 1:
            if attempts <= 0:
                err_msg = _("Failed to check status for instance {}: "
                            "The maximum number of attempts "
                            "has been exceeded.").format(inst_name)
                break
            server = self.get_server(inst_id)
            if server.status == return_on:
                msg = "Instance {} status {}.".format(inst_name, return_on)
                LOG.info(msg)
                return server
            elif server.status == "ERROR":
                err_msg = _("Instance {} Status Error. "
                            "{}").format(inst_name, server.fault.get("message"))
                break
            LOG.debug("Instance status not active. "
                      "Try again 1 second later...")
            attempts -= 1
            time.sleep(1)
        self._handle_error(err_msg)

    @logger_decorator
    def delete_instance(self, instance_id, sync=True):
        try:
            self.nova_cli.instance_delete(instance_id)
            LOG.debug('Scheduled Delete an instance %s .' % instance_id)
        except exceptions.NotFound:
            LOG.info("Instance ({}) already deleted.".format(instance_id))
            return True
        except Exception as e:
            err_msg = _("Unknown error, Please try again later.")
            self._handle_error(err_msg, e)

        if sync:
            attempts = ATTEMPTS
            while attempts:
                try:
                    self.nova_cli.instance_get_by_id(instance_id)
                except exceptions.NotFound:
                    LOG.info("Deleted instance {}".format(instance_id))
                    break
                except Exception as e:
                    LOG.debug("Unable to get instance ({}). \n{}".format(instance_id, e))
                attempts -= 1
                time.sleep(1)
        return True

    @logger_decorator
    def shutdown_instance(self, instance_id):
        self.nova_cli.instance_stop(instance_id)

        attempts = ATTEMPTS
        while 1:
            if attempts <= 0:
                err_msg = _("The maximum number of attempts has been exceeded.")
                LOG.error(err_msg)
                break
            server = self.nova_cli.instance_get(instance_id)
            if server.status == "SHUTOFF":
                msg = "Successfully shutdown Instance {} .".format(instance_id)
                LOG.info(msg)
                return True
            LOG.debug("Instance status not Shutoff ({})...".format(server.status))
            attempts -= 1
            time.sleep(1)
        LOG.error(_("Unable to shutdown instance {}").format(instance_id))
        return False

    @logger_decorator
    def pause_instance(self, instance_id):
        try:
            self.nova_cli.instance_pause(instance_id)
        except Exception as e:
            err_msg = _("Unable to pause instance {}").format(instance_id)
            self._handle_error(err_msg, e)

    @logger_decorator
    def unpause_instance(self, instance_id):
        try:
            self.nova_cli.instance_unpause(instance_id)
        except Exception as e:
            err_msg = _("Unable to unpause instance {}").format(instance_id)
            self._handle_error(err_msg, e)

    @logger_decorator
    def start_instance(self, instance_id):
        try:
            self.nova_cli.instance_start(instance_id)
        except Exception as e:
            err_msg = _("Unable to start instance {}").format(instance_id)
            self._handle_error(err_msg, e)

    @logger_decorator
    def reboot_instance(self, instance_id):
        try:
            self.nova_cli.instance_reboot(instance_id)
        except Exception as e:
            err_msg = _("Unable to reboot instance {}").format(instance_id)
            self._handle_error(err_msg, e)

    @logger_decorator
    def rebuild_instance(self, instance_id, image):
        try:
            return self.nova_cli.instance_rebuild(instance_id, image)
        except Exception as e:
            err_msg = _("Unable to rebuild instance {}").format(instance_id)
            self._handle_error(err_msg, e)

    @logger_decorator
    def get_instance_list_by_name(self, instance_name):
        try:
            return self.nova_cli.instance_list_by_name(instance_name)
        except Exception as e:
            err_msg = _("Unable to get instance {}").format(instance_name)
            self._handle_error(err_msg, e)

    @logger_decorator
    def create_snapshot(self, instance_id, snapshot_name, check_status=False):
        snapshot_name = snapshot_name or \
                        "snapshot_{}".format(str(uuid.uuid4())[:12])
        try:
            snapshot_id = self.nova_cli.snapshot_create(instance_id,
                                                        snapshot_name)
            msg = "Instance {} snapshot creating...".format(instance_id)
            LOG.info(msg)
            if check_status:
                # TODO: check snapshot status
                pass
            return snapshot_id
        except Exception as e:
            err_msg = _("Unable to create snapshot for "
                        "instance {}.").format(instance_id)
            self._handle_error(err_msg, e)

    @logger_decorator
    def get_spice_console(self, instance_id, console_type='spice-html5'):
        if not instance_id:
            err_msg = _("Param instance_id not configured.")
            self._handle_error(err_msg)

        try:
            console = self.nova_cli.spice_console(instance_id, console_type)
            LOG.info("get spice console for instance {} .".format(instance_id))
            return console
        except Exception as e:
            err_msg = _("Unable to get spice console for instance {} .").format(instance_id)
            self._handle_error(err_msg, e)

    @logger_decorator
    def get_vnc_console(self, instance_id):
        if not instance_id:
            err_msg = _("Param instance_id not configured.")
            self._handle_error(err_msg)

        try:
            console = self.nova_cli.vnc_console(instance_id)
            LOG.info("get vnc console for instance {} .".format(instance_id))
            return console
        except Exception as e:
            err_msg = _("Unable to get vnc console for instance {} .").format(instance_id)
            self._handle_error(err_msg, e)

    @logger_decorator
    def create_flavor(self, **kwargs):
        """Create a flavor

        :param kwargs: name, ram, vcpus, disk
        :return: Flavor
        """
        try:
            return self.nova_cli.flavor_create(**kwargs)
        except Exception as e:
            err_msg = _("Unable to create flavor by params {}").format(kwargs)
            self._handle_error(err_msg, e)

    @logger_decorator
    def get_flavor(self, flavor_id=None, flavor_name=None):
        try:
            if flavor_id:
                return self.nova_cli.flavor_get(flavor_id)
            return self.nova_cli.flavor_get_by_name(flavor_name)
        except Exception as e:
            err_msg = _("Unable to get flavor by name {}").format(flavor_name)
            self._handle_error(err_msg, e)

    @logger_decorator
    def list_flavor(self):
        try:
            return self.nova_cli.flavor_list()
        except Exception as e:
            err_msg = _("Unable to list flavors")
            self._handle_error(err_msg, e)

    @logger_decorator
    def add_metadata(self, instance_id, metadata):
        try:
            self.nova_cli.instance_add_metadata(instance_id, metadata)
        except Exception as e:
            err_msg = _("Unable to add metadata {} "
                        "for instance {}").format(metadata, instance_id)
            self._handle_error(err_msg, e)

    @logger_decorator
    def delete_metadata(self, instance_id, keys):
        try:
            self.nova_cli.instance_delete_metadata(instance_id, keys)
        except Exception as e:
            err_msg = _("Unable to delete metadata {} "
                        "for instance {}").format(keys, instance_id)
            self._handle_error(err_msg, e)

    @logger_decorator
    def change_password(self, instance_id, password):
        try:
            self.nova_cli.password_change(instance_id, password)
        except Exception as e:
            err_msg = _("Unable to change password {} "
                        "for instance {}").format(password, instance_id)
            self._handle_error(err_msg, e)
