from __future__ import unicode_literals

from datetime import datetime
import json
import logging
import time

from common_flowmonitor.base import RedisHelper


LOG = logging.getLogger(__name__)

HOSTS_KEY = "_net_flow_hosts_"
FLOW_HOST_KEY = "_net_flow_host_{}_"
FLOW_DEVICE_KEY = "_net_flow_device_{}_"
FLOW_INSTANCE_KEY = "_net_flow_instance_{}_"
DATA_KEY = "datas"
TIME_FORMAT = "%Y-%m-%d %H:%M:%S %f"


class FlowMonitor(RedisHelper):
    def __init__(self):
        super(FlowMonitor, self).__init__()

    def get_host_flow_datas(self, host, device=None, count=1):
        key = FLOW_HOST_KEY.format(host)
        host_data = self.rds.get(key) or []
        if host_data:
            host_data = json.loads(host_data)
        if isinstance(host_data, dict):
            if device:
                return host_data.get(DATA_KEY).get(device)
            return host_data.get(DATA_KEY)
        if device:
            return [data.get(DATA_KEY).get(device)
                    for data in host_data[1-count:]]
        return [data.get(DATA_KEY)
                for data in host_data[0-count:]]

    def get_device_flow_datas(self, device, count=1):
        key = FLOW_DEVICE_KEY.format(device)
        dev_data = self.rds.get(key) or []
        if dev_data:
            dev_data = json.loads(dev_data)
        if isinstance(dev_data, dict):
            return dev_data
        return dev_data[0-count:]

    def get_instance_flow_datas(self, instance_id,
                                count=10, time_since=None):
        LOG.debug("Get flow data for instance {} , count {}, "
                  "time_since {}".format(instance_id, count, time_since))
        if not instance_id:
            print "Error."
        key = FLOW_INSTANCE_KEY.format(instance_id)
        inst_flow_datas = json.loads(self.rds.get(key) or "[]")
        if inst_flow_datas and isinstance(inst_flow_datas, list):
            inst_flow_datas = inst_flow_datas[0-count:]

        if time_since:
            filter_list = []
            for tap_info in inst_flow_datas:
                for tap, data in tap_info.items():
                    try:
                        check_time = datetime.strptime(
                            data.get("check_time"), TIME_FORMAT)
                        if check_time > datetime.strptime(
                                time_since, TIME_FORMAT):
                            filter_list.append(tap_info)
                    except:
                        pass
            LOG.debug(filter_list)
            return filter_list
        LOG.debug(inst_flow_datas)
        return inst_flow_datas

    def get_hosts(self):
        hosts = self.rds.get(HOSTS_KEY) or []
        return hosts if hosts else json.loads(hosts)


if __name__ == "__main__":
    fm = FlowMonitor()
    now = datetime.now()
    time.sleep(10)
    aaa = fm.get_instance_flow_datas("829bb258-69d1-49c9-8815-cc358d1b828d", 10, now)
    print aaa
    print len(aaa)
