from __future__ import unicode_literals

import logging
import subprocess

from keystoneauth1.identity import v3
from keystoneauth1 import session

from zunclient.common import utils
from zunclient.v1 import client

try:
    from common_scene.setting import api_settings
except Exception:
    pass

LOG = logging.getLogger(__name__)
CONTAINER_CREATE_ATTRS = client.containers.CREATION_ATTRIBUTES
IMAGE_PULL_ATTRS = client.images.PULL_ATTRIBUTES


class Client(object):
    def __init__(self, **kwargs):
        auth = v3.Password(
                auth_url=kwargs.get("auth_url") or api_settings.OS_AUTH.get("auth_url"),
                username=kwargs.get("username") or api_settings.OS_AUTH.get("username"),
                password=kwargs.get("password") or api_settings.OS_AUTH.get("password"),
                project_name=kwargs.get("project_name") or api_settings.OS_AUTH.get("project_name"),
                user_domain_id=kwargs.get("user_domain_id") or api_settings.OS_AUTH.get("user_domain_id"),
                project_domain_id=kwargs.get("project_domain_id") or api_settings.OS_AUTH.get("project_domain_id")
        )
        sess = session.Session(auth=auth)
        self.zun_client = client.Client(session=sess)

    def _cleanup_params(self, attrs, check, **params):
        args = {}
        run = False

        for (key, value) in params.items():
            if key == "run":
                run = value
            elif key == "cpu":
                args[key] = float(value)
            elif key == "memory":
                args[key] = int(value)
            elif key == "interactive" or key == "nets" \
                    or key == "security_groups" or key == "hints":
                args[key] = value
            elif key == "restart_policy":
                args[key] = utils.check_restart_policy(value)
            elif key == "environment" or key == "labels":
                values = {}
                vals = value.split(",")
                for v in vals:
                    kv = v.split("=", 1)
                    values[kv[0]] = kv[1]
                args[str(key)] = values
            elif key in attrs:
                if value is None:
                    value = ''
                args[str(key)] = str(value)
            elif check:
                LOG.error("Key must be in %s" % ",".join(attrs))

        return args, run

    def _delete_attributes_with_same_value(self, old, new):
        '''Delete attributes with same value from new dict

        If new dict has same value in old dict, remove the attributes
        from new dict.
        '''
        for k in old.keys():
            if k in new:
                if old[k] == new[k]:
                    del new[k]
        return new

    def container_list(self, limit=None, marker=None, sort_key=None,
                       sort_dir=None, detail=True):
        return self.zun_client.containers.list(limit, marker,
                                               sort_key, sort_dir)

    def container_show(self, id):
        return self.zun_client.containers.get(id)

    def container_logs(self, id):
        args = {}
        args["stdout"] = True
        args["stderr"] = True
        return self.zun_client.containers.logs(id, **args)

    def container_start(self, id):
        return self.zun_client.containers.start(id)

    def container_stop(self, id, timeout=10):
        return self.zun_client.containers.stop(id, timeout)

    def container_restart(self, id, timeout=10):
        return self.zun_client.containers.restart(id, timeout)

    def container_pause(self, id):
        return self.zun_client.containers.pause(id)

    def container_unpause(self, id):
        return self.zun_client.containers.unpause(id)

    def container_delete(self, id, force=False):
        return self.zun_client.containers.delete(id, force=force)

    def container_create(self, **kwargs):
        args, run = self._cleanup_params(CONTAINER_CREATE_ATTRS, True, **kwargs)
        if run:
            return self.zun_client.containers.run(**args)
        return self.zun_client.containers.create(**args)

    def container_update(self, id, **kwargs):
        container = self.zun_client.containers.get(id).to_dict()
        if container["memory"] is not None:
            container["memory"] = int(container["memory"].replace("M", ""))
        args, run = self._cleanup_params(CONTAINER_CREATE_ATTRS, True, **kwargs)

        # remove same values from new params
        self._delete_attributes_with_same_value(container, args)

        # do rename
        name = args.pop("name", None)
        if len(args):
            self.zun_client.containers.update(id, **args)

        # do update
        if name:
            self.zun_client.containers.rename(id, name)
            args["name"] = name
        return args

    def container_execute(self, id, command):
        args = {"command": command}
        return self.zun_client.containers.execute(id, **args)

    def container_kill(self, id, signal=None):
        return self.zun_client.containers.kill(id, signal)

    def container_attach(self, id):
        return self.zun_client.containers.attach(id)

    def container_commit(self, id, repository, tag=None):
        return self.zun_client.containers.commit(id, repository, tag=tag)

    def image_list(self, limit=None, marker=None, sort_key=None,
                   sort_dir=None, detail=True):
        return self.zun_client.images.list(limit, marker, sort_key, sort_dir, False)

    def image_build(self, image_name, docker_file_path):
        build_cmd = "docker build -t {}".format(image_name)
        p = subprocess.Popen(build_cmd, cwd=docker_file_path,
                             shell=True, stdout=subprocess.PIPE)
        output = p.communicate()
        p.wait()
        LOG.debug(output)

        if p.returncode == 0:
            return image_name
        return None

    def image_pull(self, **kwargs):
        args, run = self._cleanup_params(IMAGE_PULL_ATTRS, True, **kwargs)
        return self.zun_client.images.create(**args)

    def host_list(self):
        return self.zun_client.hosts.list()

    def service_list(self):
        return self.zun_client.services.list()

    def network_create(self, network_id):
        return self.zun_client.containers.network_create(network_id)


if __name__ == "__main__":
    cli = Client(auth_url="http://controller:35357/v3/", username="admin",
                 password="ADMIN_PASS", project_name="admin",
                 user_domain_id="default", project_domain_id="default")

    net = cli.network_create("ed4edca2-9c40-48c5-b598-016b081c6d02")

    import uuid
    import time
    def create_container(i):
        start_time = time.time()
        cont = cli.container_create(name=uuid.uuid4().hex[:10],image="ubuntu_baseimage_cr",
                                    command="", run=True,
                                    nets=[{"network": "6fa50fcc-4e50-4b18-aff0-22a3df3a3d9b", "v4-fixed-ip": ""}])
        print "created %s (%s) :  %s" % (i, time.time()-start_time, cont)

    import multiprocessing
    stime = time.time()
    pool = multiprocessing.Pool(int(multiprocessing.cpu_count()/2))
    pool.map(create_container, range(1, 4))
    pool.close()
    pool.join()
    print "Done : %s" % (time.time()-stime)
    # first boot execute
    # lock_path = ""
    # if [ ! -f "{lock_path}" ]; then {init_script} fi
    # cont = cli.container_show("9c8cffe2-d524-4704-884c-196f7617bc91")
    # cont = cli.container_create(name="123123",image="ubuntu-web",
    #                             command="/bin/bash -c \"mkdir /root/1111111 && cd /root/1111111 && echo \"aaaa\" > aaaaaa.txt && sleep infinity;\"",run=True,
    #                             security_groups=["default"],
    #                             nets=[{"network": "c192f87f-2c6c-47aa-af9a-97cd9e58a958", "v4-fixed-ip": ""}])
    # print cont
    # cli.container_stop(id="f3907db3-c484-48fc-aa97-c36044b1c8e5")
    # cli.container_delete(id="f3907db3-c484-48fc-aa97-c36044b1c8e5")
    # ii = cli.container_commit("34375ae3-db3a-4bd0-af3f-04703e05d119", "sssssssss")

