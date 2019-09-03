# coding=utf-8
import json
import logging

import thriftpy
from thriftpy.rpc import make_client
from thriftpy.thrift import TException

checker_thrift = thriftpy.load("oj.thrift", module_name="xoj_thrift")

logger = logging.getLogger(__name__)

RPC_PORT = 6000


def checker(runner_ip, script_path, host, port):
    try:
        checker_runner = make_client(checker_thrift.xoj, runner_ip, RPC_PORT)
        ret = checker_runner.checker(script_path, host, port)
        return json.loads(ret)
    except TException as e:
        logger.error("Thrift Exception | checker error runner[%s] host[%s] port[%d] msg[%s]",
                     runner_ip, host, port, str(e))
        return {'status': 'up', 'msg': 'thrift TTransportException'}
    except Exception as e:
        logger.error("checker error runner[%s] host[%s] port[%d] msg[%s]",
                     runner_ip, host, port, str(e))
        return {'status': 'up', 'msg': 'run script error'}


# test = checker('127.0.0.1', "/home/sugar/Desktop/checker.py", "10.10.52.85", 20002)
# print test

