# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import requests
import yaml
import uuid
from requests_toolbelt.multipart.encoder import MultipartEncoder

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

DOCKER_COMPOSE_NAME = "docker-compose.yml"
DOCKER_FILE_NAME = "Dockerfile"
START_SCRIPT = "start.sh"

OJ_HOME = "http://10.10.62.252"
OJ_AUTH_URL = "{}/accounts/login/".format(OJ_HOME)
OJ_TARGET_URL = "{}/admin/common_env/api/standard_devices/".format(OJ_HOME)
OJ_SCENE_URL = "{}/admin/common_env/api/envs/".format(OJ_HOME)
OJ_SCENE_DETAIL_URL = "%s{}/" % OJ_SCENE_URL
OJ_USER = "admin"
OJ_PASSWORD = "admin123456"
FLAG_STR = "flag{%s}"
EXISTS_ACTION = "update" #update/delete/pass

OS_AUTH_STR = 'export OS_USERNAME=admin && ' \
              'export OS_PASSWORD=L5uCdcjQQuyY9DLs && ' \
              'export OS_PROJECT_NAME=admin && ' \
              'export OS_USER_DOMAIN_NAME=default && ' \
              'export OS_PROJECT_DOMAIN_NAME=default && ' \
              'export OS_AUTH_URL=http://controller:35357/v3 && ' \
              'export OS_IDENTITY_API_VERSION=3 && ' \
              'export OS_AUTH_VERSION=3 && '

OPERATORS = {
    "misc_operator": {
        "systemType": "linux",
        "flavor": "m2.1c-1g-10g",
        "accessMode": [{
                    "username": "root",
                    "password": "",
                    "protocol": "ssh",
                    "port": 22
                }]
    },
    "centos_operator": {
        "systemType": "linux",
        "flavor": "m2.1c-1g-10g",
        "accessMode": [{
                    "username": "root",
                    "password": "ycxx123#",
                    "protocol": "ssh",
                    "port": 22
                }]
    },
    "ubuntu-crypto": {
        "systemType": "linux",
        "flavor": "m4.2c-2g-40g",
        "accessMode": [{
                    "username": "crypto",
                    "password": "toor",
                    "protocol": "rdp",
                    "port": 3389
                }]
    },
    "kali-operator": {
        "systemType": "linux",
        "flavor": "m4.2c-2g-40g",
        "accessMode": [{
                    "username": "root",
                    "password": "xctf@2017",
                    "protocol": "rdp",
                    "port": 3389
                }]
    },
    "security_win10": {
        "systemType": "windows",
        "flavor": "m4.2c-2g-40g",
        "accessMode": [{
                    "username": "admin",
                    "password": "123456",
                    "protocol": "rdp",
                    "mode": "nla",
                    "port": 3389
                }]
    },
    "dh_win10": {
        "systemType": "windows",
        "flavor": "m4.2c-2g-40g",
        "accessMode": [{
                    "username": "ops",
                    "password": "123456",
                    "protocol": "rdp",
                    "mode": "nla",
                    "port": 3389
                }]
    },
    "security_win10_first": {
        "systemType": "windows",
        "flavor": "m4.2c-2g-40g",
        "accessMode": [{
                    "username": "ops",
                    "password": "123456",
                    "protocol": "rdp",
                    "mode": "nla",
                    "port": 3389
                }]
    },
    "security-winserver-clone": {
        "systemType": "windows",
        "flavor": "m4.2c-2g-40g",
        "accessMode": [{
                    "username": "Administrator",
                    "password": "Cp123456",
                    "protocol": "rdp",
                    "port": 3389
                }]
    },
    "security_ubuntu_first": {
        "systemType": "linux",
        "flavor": "m3.1c-2g-20g",
        "accessMode": [{
                    "username": "administrator",
                    "password": "123456",
                    "protocol": "ssh",
                    "port": 22
                }]
    },
    "net_conf_win7": {
        "systemType": "windows",
        "flavor": "m4.4c-4g-40g",
        "accessMode": [{
                    "username": "admin",
                    "password": "",
                    "protocol": "rdp",
                    "port": 3389
                }]
    },
    "reverse_operator": {
        "systemType": "windows",
        "flavor": "m4.4c-4g-40g",
        "accessMode": [{
                    "username": "admin",
                    "password": "",
                    "protocol": "rdp",
                    "port": 3389
                }]
    },
    "ppc_operator": {
        "systemType": "linux",
        "flavor": "m2.1c-1g-10g",
        "accessMode": [{
                    "username": "root",
                    "password": "",
                    "protocol": "ssh",
                    "port": 22
                }]
    },
    "crypto_operator": {
        "systemType": "linux",
        "flavor": "m2.1c-1g-10g",
        "accessMode": [{
                    "username": "root",
                    "password": "",
                    "protocol": "ssh",
                    "port": 22
                }]
    },
    "pwn_operator":{
        "systemType": "linux",
        "flavor": "m2.1c-1g-10g",
        "accessMode": [{
                    "username": "ubuntu",
                    "password": "ubuntu",
                    "protocol": "ssh",
                    "port": 22
                }]
    },
    "web_operator": {
        "systemType": "linux",
        "flavor": "m2.1c-1g-10g",
        "accessMode": [{
                    "username": "root",
                    "password": "",
                    "protocol": "ssh",
                    "port": 22
                }]
    },
    "winxp-crypto": {
        "systemType": "windows",
        "flavor": "m4.2c-2g-40g",
        "accessMode": [{
                    "username": "Administrator",
                    "password": "xctf@2017",
                    "protocol": "rdp",
                    "mode": "rdp",
                    "port": 3389
                }]
    },
    "win7-wireshark": {
        "systemType": "windows",
        "flavor": "m3.4c-4g-20g",
        "accessMode": [{
            "username": "Administrator ",
            "password": "ycxx123#",
                    "protocol": "rdp",
                    "mode": "nla",
                    "port": 3389
                }]
    },
    "windows_code_audit": {
        "systemType": "windows",
        "flavor": "m4.4c-4g-40g",
        "accessMode": [{
                    "username": "admin",
                    "password": "12345qwert",
                    "protocol": "rdp",
                    "mode": "nla",
                    "port": 3389
                }]
    },
    "windows_operator": {
        "systemType": "windows",
        "flavor": "m4.4c-4g-40g",
        "accessMode": [{
                    "username": "admin",
                    "password": "",
                    "protocol": "rdp",
                    "mode": "nla",
                    "port": 3389
                }]
    },
    "default_operator": {
        "systemType": "linux",
        "flavor": "m2.1c-1g-10g",
        "accessMode": [{
                    "username": "root",
                    "password": "",
                    "protocol": "ssh",
                    "port": 22
                }]
    }
}


class YamlConvert(object):
    def __init__(self, yaml_path):
        self.content = None
        self.load_yaml_file(yaml_path)

    def load_yaml_file(self, yaml_path):
        with open(yaml_path, 'r') as f:
            self.content = yaml.load(f.read())


class ComposeYamlV2(YamlConvert):
    def __init__(self, yaml_path):
        super(ComposeYamlV2, self).__init__(yaml_path)

    @property
    def services(self):
        return self.content.get("services")


class ComposeYaml(YamlConvert):
    def __init__(self, yaml_path, service_name=None):
        super(ComposeYaml, self).__init__(yaml_path)
        if service_name:
            self.services0 = (service_name,
                              self.services.get(service_name))
        else:
            services = self.services.items()
            if len(services) >= 2:
                print "ERR: Multi service."
                raise Exception("Multi service.")
            self.services0 = services[0]

    @property
    def services(self):
        return self.content.get("services")

    @property
    def build(self):
        return self.services0[1].get("build")

    @property
    def command(self):
        cmd = self.services0[1].get("command")
        # if cmd.startswith("/"):
        #     cmd = ".{}".format(cmd)
        return cmd or ""

    @property
    def image(self):
        return self.services0[1].get("image")

    @property
    def image_name(self):
        img_name = self.image
        if "/" in img_name:
            img_name = img_name.split("/")[-1]
        if ":" in img_name:
            img_name = img_name.replace(':', "_")
        return img_name

    @property
    def ports(self):
        ports = self.services0[1].get("ports")
        t_ports = []
        for port in ports:
            if ":" in port:
                t_ports.append(port.split(":")[-1])
            else:
                t_ports.append(port)
        return t_ports


class LabsYaml(YamlConvert):
    def __init__(self, yaml_path, lab=None):
        super(LabsYaml, self).__init__(yaml_path)
        if lab:
            self.add_property(self.labs.get(lab).popitem())

    @property
    def labs(self):
        return self.content.get("labs")

    def add_property(self, lab):
        setattr(self, lab[0], lab[1])


class SceneCreater(object):
    def __init__(self):
        self.session = requests.Session()
        csrf_token = self._get_csrf_token(OJ_AUTH_URL)
        resp = self.session.post(OJ_AUTH_URL,
                                 data={"username": OJ_USER,
                                       "password": OJ_PASSWORD,
                                       "csrfmiddlewaretoken": csrf_token},
                                 verify=False)

    def _get_csrf_token(self, url):
        self.session.get(url, verify=False)
        return self.session.cookies['oj_csrftoken']

    def create_target(self, **data):
        if "csrfmiddlewaretoken" not in data:
            data.update({"csrfmiddlewaretoken": self._get_csrf_token(OJ_TARGET_URL)})
        resp = self.session.post(OJ_TARGET_URL, data=data, verify=False)
        if resp.status_code in [200, 201]:
            print "Created target {}".format(data.get("name"))
            return json.loads(resp.text)
        if "\"code\":\"unique\"" in resp.text:
            print "Target {} already exists.".format(data.get("name"))
            return True
        print "Error: Failed to create target {} : {}".format(data.get("name"), resp.text)
        return None

    def get_target(self, name):
        search_str = "?search={}&order=asc&offset=0&limit=10&role=&role_type=&image_type=".format(name)
        resp = self.session.get("{}{}".format(OJ_TARGET_URL, search_str))
        if resp.status_code in [200, 201]:
            print "Get target {}".format(name)
            return json.loads(resp.text)['rows'][0]
        print "Error: Failed to get target {} : {}".format(name, resp.text)
        return None

    def update_scene(self, scene_id, data, files=None):
        if files and "json_config" in data:
            data.pop("json_config")

        if "csrfmiddlewaretoken" not in data:
            data.pop("csrfmiddlewaretoken")

        if files:
            data.update(files)

        m = MultipartEncoder(
            fields=data
        )
        resp = self.session.patch(OJ_SCENE_DETAIL_URL.format(scene_id), data=m,
                          headers={'Content-Type': m.content_type,
                                   "X-CSRFToken": self._get_csrf_token(OJ_SCENE_DETAIL_URL.format(scene_id)),
                                   "Connection": "keep-alive",
                                   "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36",
                                   "Accept": "*/*",
                                   "Accept-Encoding": "gzip, deflate, br",
                                   'Accept-Language': 'zh,en;q=0.9,zh-CN;q=0.8',
                                   'X-Requested-With': 'XMLHttpRequest'
                                   })
        if resp.status_code in [200, 201]:
            print "Updated scene {}".format(data.get("name"))
            return json.loads(resp.text)
        print "Error: Failed to update scene {} : {}".format(data.get("name"), resp.text)
        return None

    def delete_scene(self, scene):
        headers = {"X-CSRFToken": self._get_csrf_token(OJ_SCENE_DETAIL_URL.format(scene.get("id")))}
        resp = self.session.delete(OJ_SCENE_DETAIL_URL.format(scene.get("id")),
                                  verify=False, headers=headers)
        if resp.status_code in [200, 201, 204]:
            print "Deleted scene {}".format(scene.get("name"))
            return True
        print "Error: Failed to delete scene {} : {}".format(scene.get("name"), resp.text)
        return False

    def get_scene(self, name):
        search_str = "?search={}&order=asc&offset=0&limit=10&type=".format(name)
        resp = self.session.get("{}{}".format(OJ_SCENE_URL, search_str))
        if resp.status_code in [200, 201]:
            scene = json.loads(resp.text)['rows']
            if scene:
                print "Get scene {}".format(name)
                return scene[0]
            else:
                return None
        print "Error: Failed to get scene {} : {}".format(name, resp.text)
        return None

    def create_scene(self, **data):
        if "csrfmiddlewaretoken" not in data:
            data.update({"csrfmiddlewaretoken": self._get_csrf_token(OJ_SCENE_DETAIL_URL.format(0))})
        if "files" in data:
            files = data.pop("files") or None
        else:
            files = None

        # check scene exists
        scene = self.get_scene(data.get("name"))
        if scene:
            print "Scene {} exists .".format(data.get("name"))
            if EXISTS_ACTION == "delete":
                print "Delete scene before create."
                self.delete_scene(scene)
            elif EXISTS_ACTION == "pass":
                return scene
            elif EXISTS_ACTION == "update":
                print "Update scene {}".format(data.get("name"))
                return self.update_scene(scene.get("id"),
                                         data=data, files=files)

        resp = self.session.post(OJ_SCENE_URL, data=data, files=files, verify=False)

        if resp.status_code in [200, 201]:
            print "Created scene {}".format(data.get("name"))
            return json.loads(resp.text)
        elif resp.status_code == 400 and "已存在" in resp.text or "x_env_name_exists" in resp.text:
            print "Scene {} already exists, update scene .".format(data.get("name"))
            scene_new = self.update_scene(scene.get("id"), data=data, files=files)
            return scene_new
        print "Error: Failed to create scene {} : {}".format(data.get("name"), resp.text)
        return None


def convert_config_json(conf_json, scene_name=None, only_rename=False):
    conf_dict = json.loads(conf_json)
    if not scene_name:
        scene_name = "{}-{}".format(conf_dict['scene'].get('name'),
                                    uuid.uuid4().hex[:6])
    if only_rename:
        conf_dict["scene"]["name"] = scene_name
        return json.dumps(conf_dict, indent=4)
    new_json = {
        "scene": {
            "name": scene_name,
            "vulns": conf_dict['scene'].get('vulns', []),
            "tools": conf_dict['scene'].get('tools', []),
            "tag": conf_dict['scene'].get('tag', []),
            "desc": conf_dict['scene'].get('desc', "")
        }
    }
    new_routers = []
    orig_routers = conf_dict.get('routers')
    if orig_routers:
        for i, rt in enumerate(orig_routers):
            rt_nets = rt.get("net")
            rt_legal_nets = []
            for rt_net in rt_nets:
                if "openstack" in rt_net.lower():
                    rt_legal_nets.append("internet-{}".format(i+1))
                else:
                    rt_legal_nets.append(rt_net)
            new_routers.append({
                "canUserConfigure": False,
                "net": rt_legal_nets,
                "staticRouting": [],
                "name": "router",
                "id": "router-{}".format(i+1)
            })
    # else:
    #     new_routers.append({
    #         "canUserConfigure": False,
    #         "net": ["network-1", "internet-1"],
    #         "staticRouting": [],
    #         "name": "router",
    #         "id": "router-1"
    #     })
    new_json.update({"routers": new_routers})

    new_nets = []
    orig_nets = conf_dict.get('networks')
    if orig_nets:
        for i, net in enumerate(orig_nets):
            net_id = net.get("id")
            net_name = net.get("name")
            if "openstack" in net_id.lower():
                net_id = "internet-{}".format(i+1)
                net_name = "Internet-{}".format(i+1)
            new_nets.append({
                "name": net_name,
                "id": net_id,
                "range": "",
                "dns": [],
                "dhcp": True,
                "gateway": ""
            })
    else:
        new_nets.extend([
            # {
            #     "name": "network",
            #     "id": "network-1",
            #     "range": "",
            #     "dns": [],
            #     "dhcp": True,
            #     "gateway": ""
            # },
            {
                "name": "Internet",
                "id": "internet-1",
                "range": "",
                "dns": [],
                "dhcp": True,
                "gateway": ""
            }
        ])
    new_json.update({"networks": new_nets})

    servers = []
    for srv in conf_dict.get("servers"):
        acc_user = srv.get("accessUser")
        acc_mode = srv.get("accessMode")
        accessMode = [{
                    "username": acc_user[0].get("username", "") if acc_user else "",
                    "password": acc_user[0].get("password", "") if acc_user else "",
                    "protocol": acc_mode[0].get("protocol", "") if acc_mode else "",
                    "port": int(acc_mode[0].get("port")) if acc_mode else "",
                }]
        if acc_mode[0].get("mode"):
            accessMode[0]["mode"] = acc_mode[0].get("mode", "")

        servers.append(
            {
                "id": srv["id"],
                "name": srv.get("name", srv["id"]),
                "image": srv.get("image", ""),
                "deployScript": "",
                "pushFlagScript": "",
                "wan_number": 0,
                "attackScript": "",
                "systemType": srv.get("imageType", "linux"),
                "lan_number": 0,
                "installScript": srv.get("installScript", ""),
                "attacker": "",
                "checker": "",
                "role": srv.get("role", "target"),
                "external": True,
                "initScript": srv.get("initScript", ""),
                "cleanScript": "",
                "accessMode": accessMode,
                "flavor": srv.get("flavor", "m2.1c-1g-10g"),
                "checkScript": "",
                "net": srv.get("net") if orig_nets else ["internet-1"],
                "imageType": "vm"
            }
        )
    new_json.update({"servers": servers})
    return json.dumps(new_json, indent=4)
