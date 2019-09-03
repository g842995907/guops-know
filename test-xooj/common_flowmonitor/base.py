from __future__ import unicode_literals

import json

import redis

from common_flowmonitor import config as project_conf

HOSTS_KEY = "_net_flow_hosts_"
FLOW_HOST_KEY = "_net_flow_host_{}_"
FLOW_DEVICE_KEY = "_net_flow_device_{}_"
FLOW_INSTANCE_KEY = "_net_flow_instance_{}_"
FLOW_CHANNEL = "_net_flow_monitor_"
DATA_KEY = "datas"
EX_SECONDS = 3600


class RedisHelper(object):
    def __init__(self):
        self.rds = redis.Redis(host=getattr(project_conf,
                                            "redis_server",
                                            "127.0.0.1"),
                               port=getattr(project_conf,
                                            "redis_port",
                                            6379),
                               password=getattr(project_conf,
                                                "redis_pass",
                                                "foobar"))

    def publish(self, msg):
        self.rds.publish(FLOW_CHANNEL, msg)
        return True

    def subscribe(self):
        pub = self.rds.pubsub()
        pub.subscribe(FLOW_CHANNEL)
        pub.parse_response()
        return pub

    def write_host_flow_datas(self, host, datas, keep_history=5):
        key = FLOW_HOST_KEY.format(host)

        # save latest n data
        if keep_history > 1:
            orig_data = self.rds.get(key) or []
            if orig_data:
                orig_data = json.loads(orig_data)

            if len(orig_data) >= keep_history:
                orig_data = orig_data[1 - keep_history:]
            orig_data.append(datas)
            self.rds.set(key, json.dumps(orig_data), ex=EX_SECONDS)
        else:
            self.rds.set(key, json.dumps(datas), ex=EX_SECONDS)

    def write_device_flow_datas(self, datas, keep_history=5):
        if not datas:
            return

        for dev, data in datas.items():
            key = FLOW_DEVICE_KEY.format(dev)
            dev_data = self.rds.get(key) or []
            if dev_data:
                dev_data = json.loads(dev_data)
            if len(dev_data) >= keep_history:
                dev_data = dev_data[1-keep_history:]
            dev_data.append(data)
            self.rds.set(key, json.dumps(dev_data))

    def write_instance_flow_datas(self, host_datas, keep_history=1):
        datas = host_datas.get("datas")
        for dev, data in datas.items():
            inst_key = FLOW_INSTANCE_KEY.format(data.get("server_id"))
            inst_data = json.loads(self.rds.get(inst_key) or "[]")
            if inst_data:
                # TODO: deal with multi net card
                # This may cause error when update
                # network instance interface card
                if dev in inst_data[-1].keys():
                    if keep_history > 1:
                        if len(inst_data) >= keep_history:
                            inst_data = inst_data[1-keep_history:]
                    else:
                        inst_data = []
                    inst_data.append({dev: data})
                else:
                    inst_data[-1].update({dev: data})
            else:
                inst_data.append({dev: data})
            self.rds.set(inst_key, json.dumps(inst_data), ex=EX_SECONDS)

    def clean_host_flow_datas(self, host):
        key = FLOW_HOST_KEY.format(host)
        if self.rds.exists(key):
            self.rds.delete(key)

    def refresh_hosts(self, host):
        registed_hosts = self.rds.get(HOSTS_KEY) or []
        if registed_hosts:
            registed_hosts = json.loads(registed_hosts)
        if host not in registed_hosts:
            self.rds.set(HOSTS_KEY,
                         json.dumps(registed_hosts.append(host)))

