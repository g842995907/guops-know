from __future__ import unicode_literals

import json
import sys
import time

from common_flowmonitor.base import RedisHelper
from common_flowmonitor import config as project_conf
from common_flowmonitor.daemon import Daemon


def write_flow_datas():
    rh = RedisHelper()
    redis_sub = rh.subscribe()

    while True:
        _, channel, msg = redis_sub.parse_response()
        print (msg)

        resp = json.loads(msg)
        rh.write_instance_flow_datas(
                    resp, keep_history=getattr(project_conf,
                                               "keep_history", 1))
        time.sleep(1)


class ServerDaemon(Daemon):
    def run(self):
        write_flow_datas()


if __name__ == '__main__':
    # sys.exit(write_flow_datas())

    # use daemon
    daemon = ServerDaemon('/tmp/net-flow-server.pid')
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
