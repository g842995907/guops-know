# coding=utf-8
import functools
import json
import logging

import thriftpy
from thriftpy.rpc import make_client
from thriftpy.thrift import TException

checker_thrift = thriftpy.load("common_env/rpc/oj.thrift", module_name="xoj_thrift")

logger = logging.getLogger(__name__)

RPC_PORT = 6000


def logger_decorator(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        func_name = func.__name__
        logger.debug("Start {}(): args={}, kwargs={}".format(func_name,
                                                             args, kwargs))
        ff = func(self, *args, **kwargs)
        logger.debug("End {}()".format(func_name))
        return ff

    return wrapper


@logger_decorator
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


def attack(runner_ip, script_path, host, port, **kwargs):
    try:
        checker_runner = make_client(checker_thrift.xoj, runner_ip, RPC_PORT)

        if len(kwargs) == 0:
            args = ""
        else:
            args = json.dumps(kwargs)
        ret = checker_runner.attack(script_path, host, port, args)
        return json.loads(ret)
    except TException as e:
        logger.error("Thrift Exception | attack error runner[%s] host[%s] port[%d] msg[%s]",
                     runner_ip, host, port, str(e))
        return {'status': 'up', 'msg': 'thrift TTransportException'}
    except Exception as e:
        logger.error("attack error runner[%s] host[%s] port[%d] msg[%s]",
                     runner_ip, host, port, str(e))
        return {'status': 'error', 'msg': 'run script error'}
