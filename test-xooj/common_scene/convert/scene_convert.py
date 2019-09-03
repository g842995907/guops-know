from __future__ import unicode_literals

import json
import multiprocessing
import os
import requests
import subprocess
import sys
import time
import zipfile

base_path = "/home/moose/scene"
CONFIG_FILE = "config.json"
OJ_HOME = "http://10.10.61.3"
OJ_AUTH_URL = "{}/accounts/login/".format(OJ_HOME)
OJ_SCENE_URL = "{}/admin/common_env/api/envs/".format(OJ_HOME)
OJ_USER = "admin"
OJ_PASSWORD = "xctfoj01"


class SceneCreater(object):
    def __init__(self):
        self.session = requests.Session()
        csrf_token = self._get_csrf_token(OJ_AUTH_URL)
        self.session.post(OJ_AUTH_URL,
                          data={"username": OJ_USER,
                                "password": OJ_PASSWORD,
                                "csrfmiddlewaretoken": csrf_token})

    def _get_csrf_token(self, url):
        self.session.get(url)
        return self.session.cookies['oj_csrftoken']

    def create_scene(self, **data):
        if "csrfmiddlewaretoken" not in data:
            data.update({"csrfmiddlewaretoken": self._get_csrf_token(OJ_SCENE_URL)})
        resp = self.session.post(OJ_SCENE_URL, data=data)

        if resp.status_code in [200, 201]:
            print "Created scene {}".format(data.get("name"))
            return json.loads(resp.text)
        print "Error: Failed to create scene {} : {}".format(data.get("name"), resp.text)
        return None

    def delete_scene(self, scene_id):
        pass


def convert_config_json(conf_json, create_scene=False):
    conf_dict = json.loads(conf_json)
    new_json = {
        "scene": {
            "name": conf_dict['scene'].get('name'),
            "vulns": conf_dict['scene'].get('vulns', []),
            "tools": conf_dict['scene'].get('tools', []),
            "tag": conf_dict['scene'].get('tag', []),
            "desc": conf_dict['scene'].get('desc', "")
        },
        "routers": [{
            "canUserConfigure": False,
            "net": ["network-1", "internet-1"],
            "staticRouting": [],
            "name": "router",
            "id": "router-1"
        }],
        "networks": [{
            "name": "network",
            "id": "network-1",
            "range": "",
            "dns": [],
            "dhcp": True,
            "gateway": ""
        }, {
            "name": "Internet",
            "id": "internet-1",
            "range": "",
            "dns": [],
            "dhcp": True,
            "gateway": ""
        }],
    }

    servers = []
    for srv in conf_dict["servers"]:
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
                "net": ["network-1"],
                "imageType": "vm"
            }
        )
    new_json.update({"servers": servers})
    if create_scene:
        sc = SceneCreater()
        sc.create_scene(**{"type": "1",
                           "json_config": json.dumps(new_json),
                           "name": conf_dict['scene'].get('name')})
    return json.dumps(new_json, indent=4)


def convert_zip(scene_zip):
    print "converting zip file {}".format(scene_zip)
    start_time = time.time()

    zip_file = zipfile.ZipFile(os.path.join(base_path, scene_zip), 'r')
    with zip_file.open(CONFIG_FILE) as conf_file:
        new_json = convert_config_json(conf_file.read())
    zip_file.close()

    del_proc = subprocess.Popen("/usr/bin/zip -d {} {}".format(os.path.join(base_path, scene_zip), CONFIG_FILE),
                                shell=True)
    out, err = del_proc.communicate()
    if del_proc.returncode != 0:
        print "Non zero exit code: ({}) while executing ({}) " \
              ": {}".format(del_proc.returncode, del_proc, err)
        sys.exit(-1)

    zip_file = zipfile.ZipFile(os.path.join(base_path, scene_zip), 'a')
    zip_file.writestr(CONFIG_FILE, new_json)
    zip_file.close()
    print "converted zip file {}, time cost: {}".format(scene_zip, time.time()-start_time)


def main():
    start_time = time.time()
    pool = multiprocessing.Pool(10)

    scene_zips = os.listdir(base_path)
    for scene_zip in scene_zips:
        if not zipfile.is_zipfile(os.path.join(base_path, scene_zip)):
            continue
        pool.apply_async(convert_zip, args=(scene_zip,))

    pool.close()
    pool.join()
    print "Done. Time cost: {}".format(time.time()-start_time)

if __name__ == "__main__":
    main()
