# coding=utf-8
import functools
import imp
import json
import logging

import gevent.monkey
import thriftpy
from gevent import Timeout
from thriftpy.rpc import make_server

gevent.monkey.patch_all()

logger = logging.getLogger(__name__)
LOG_PATH = "/tmp/xoj.log"


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


class Instance(object):
    def __init__(self, script_path, ip, port, **kwargs):
        self.script_path = script_path
        self.ip = ip
        self.port = port
        self.kwargs = kwargs

    def done(self):
        _ret = self.real_done()
        return json.dumps(_ret)

    def real_done(self):
        raise Exception('implement in subclass')

    def log_detail(self, e=None):
        _log = "script_path[{}] ip[{}] port[{}]".format(self.script_path, self.ip, self.port)
        if e:
            _log = "{} msg[{}]".format(_log, str(e))
        return _log


class Checker(Instance):
    # checker检查时间15秒超时
    checker_timeout = 15

    def real_done(self):
        if not self.script_path or not self.ip or not self.port:
            return {'status': 'down', 'msg': 'checker argc error' + self.log_detail()}

        _ret = {'status': 'up', 'msg': 'good'}
        timeout = Timeout.start_new(self.checker_timeout)

        try:
            _ret = self._checker()
        except Timeout as e:
            logger.warning("checker timeout, %s", self.log_detail(e))
            _ret['msg'] = 'time out'
        except Exception as e:
            logger.error("checker script run error, %s", self.log_detail(e))
            _ret['msg'] = 'script run error'
        finally:
            timeout.cancel()

        logger.info("checker ip[%s] port[%d] status[%s] msg[%s]",
                    self.ip, self.port, _ret.get('status'), _ret.get('msg'))

        return _ret

    def _checker(self):
        _ret = {'status': 'up', 'msg': 'good'}

        try:
            script_module = imp.load_source('xoj_checker_script', self.script_path)
            _ret = script_module.checker(self.ip, self.port)
        except Exception as e:
            logger.error("checker script run error, %s", self.log_detail(e))
            _ret['msg'] = 'script run error'

        return _ret


class Dispatcher(object):
    @logger_decorator
    def checker(self, script_path, ip, port):
        _checker = Checker(script_path, ip, port)
        return _checker.done()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)-5.5s : %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        filename=LOG_PATH or None)

    checker_thrift = thriftpy.load("oj.thrift", module_name="xoj_thrift")
    server = make_server(checker_thrift.xoj, Dispatcher(), '0.0.0.0', 6000)
    server.serve()
