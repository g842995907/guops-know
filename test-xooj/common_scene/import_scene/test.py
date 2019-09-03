from __future__ import unicode_literals

import json

from utils import SceneCreater


class SceneCreaterTest(object):
    def __init__(self):
        self.sc = SceneCreater()

    def test_create_target(self):
        return self.sc.create_target(**{"name": "223344",
                                     "role": "3",
                                     "logo": "server.png",
                                     "role_type": "0",
                                     "source_image_name": "centos7-64",
                                     "disk_format": "docker",
                                     "image_type": "docker",
                                     "system_type": "linux",
                                     "access_mode": "ssh",
                                     "access_port": "22",
                                     "access_user": "root",
                                     "access_password": "xctfoj01",
                                     "flavor": "m1.1c-0.5g-8g"})

    def test_create_scene(self):
        config_json = {
            "scene": {
                "name": "123123",
                "vulns": [],
                "tools": [],
                "tag": [],
                "desc": ""
            },
            "routers": [{
                "net": ["network-1", "internet-1"],
                "staticRouting": [],
                "name": "Default Router",
                "id": "router-1"
            }],
            "networks": [{
                "dhcp": True,
                "range": "",
                "id": "network-1",
                "name": "network"
            }, {
                "dhcp": True,
                "range": "",
                "id": "internet-1",
                "name": "Internet"
            }],
            "servers": [
                {
                    "id": "scene-target",
                    "name": "docker-ubuntu-attacker",
                    "image": "docker-ubuntu-attacker",
                    "imageType": "docker",
                    "role": "target",
                    "flavor": "m2.1c-1g-10g",
                    "systemType": "linux",
                    "initScript": "./start.sh",
                    "accessMode": [{
                        "username": "root",
                        "password": "ycxx123#",
                        "protocol": "ssh",
                        "port": 22
                    }],
                    "external": True,
                    "net": ["network-1"],
                }
            ]
        }
        config_json["servers"].append(
            {
                "id": "scene-operator",
                "name": "ubuntu14-64",
                "image": "ubuntu14-64",
                "imageType": "vm",
                "role": "operator",
                "flavor": "m2.1c-1g-10g",
                "systemType": "linux",
                "accessMode": [{
                    "username": "",
                    "password": "",
                    "protocol": "console",
                    "port": ""
                }],
                "external": True,
                "net": ["network-1"],
            }
        )
        return self.sc.create_scene(**{"type": "1",
                                   "json_config": json.dumps(config_json),
                                   "name": "123123"})


if __name__ == "__main__":
    tsc = SceneCreaterTest()
    print tsc.test_create_target()
    print tsc.test_create_scene()
