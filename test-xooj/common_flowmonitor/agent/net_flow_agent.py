from __future__ import unicode_literals

import json
import socket
import sys
import time
from datetime import datetime
from xml.dom import minidom

from apscheduler.schedulers.blocking import BlockingScheduler

from common_flowmonitor import config as project_conf
from common_flowmonitor.agent.libvirt_client import LibvirtClient
from common_flowmonitor.base import RedisHelper
from common_flowmonitor.daemon import Daemon

TIME_FORMAT = "%Y-%m-%d %H:%M:%S %f"
TAP_DEVICE_PREFIX = "tap"


def load_taps():
    tap_dict = {}
    lc = LibvirtClient()
    dms = lc.list_domains()
    for dm in dms:
        dom = lc.get_domain(dm)
        inst_id = dom.UUIDString()

        raw_xml = dom.XMLDesc(0)
        xml = minidom.parseString(raw_xml)
        interfaceTypes = xml.getElementsByTagName('interface')
        for interfaceType in interfaceTypes:
            addr_elem = interfaceType.getElementsByTagName("target")[0]
            dev_name = addr_elem.getAttribute('dev')
            tap_dict.update({dev_name: inst_id})
    return tap_dict

def get_server_uuid(tap_name=None):
    if tap_name:
        return load_taps().get(tap_name)
    return load_taps()

def get_local_ip():
    return getattr(project_conf, "local_ip") or \
           socket.gethostname()

def net_ifs_datas():
    start_time = time.time()
    check_time = datetime.now().strftime(TIME_FORMAT)
    with open('/proc/net/dev') as f:
        net_dump = f.readlines()

    device_data = {}
    for line in net_dump[2:]:
        if_name, if_data = line.split(':')
        if if_name.strip().startswith(TAP_DEVICE_PREFIX) and if_data.strip():
            if_data_list = if_data.strip().split()
            device_data[if_name] = {
                "rx": float(if_data_list[0])/project_conf.report_interval,
                "tx": float(if_data_list[8])/project_conf.report_interval,
                "rxp": float(if_data_list[1])/project_conf.report_interval,
                "txp": float(if_data_list[9])/project_conf.report_interval
            }
            device_data[if_name]["server_id"] = get_server_uuid(if_name)
            device_data[if_name]["host"] = get_local_ip()
            device_data[if_name]["check_time"] = check_time
    print "check cost: {}".format(time.time()-start_time)
    return device_data


def publish_datas():
    obj = RedisHelper()
    datas = json.dumps({
        "host": get_local_ip(),
        # "check_time": datetime.now().strftime(TIME_FORMAT),
        "datas": net_ifs_datas()
    })
    obj.publish(datas)


class ClientDaemon(Daemon):
    def run(self):
        scheduler = BlockingScheduler()
        scheduler.add_job(publish_datas, 'interval',
                      seconds=getattr(project_conf,
                                      "report_interval", 30))
        scheduler.start()


if __name__ == "__main__":
    # scheduler = BlockingScheduler()
    # scheduler.add_job(publish_datas, 'interval',
    #                   seconds=getattr(project_conf,
    #                                   "report_interval", 30))
    # scheduler.start()


    daemon = ClientDaemon('/tmp/net-flow-agent.pid')
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        else:
            print "Unknown command"
            sys.exit(2)
        sys.exit(0)
    else:
        print "usage: python %s start|stop|restart" % sys.argv[0]
        sys.exit(2)
