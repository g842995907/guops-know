# coding=utf-8
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
            return {'status': 'down', 'msg': 'checker argc error'}

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


class Attack(Instance):
    attack_dict = {}

    def _attack(self):
        _ret = {'status': 'ok'}

        try:
            script_module = imp.load_source('xoj_attack_script', self.script_path)
            while True:
                logger.info("attack %s", self.log_detail())

                # 测试先用checker函数测试
                _attack_result = script_module.attack(self.ip, self.port)
                logger.debug("attack result[%s], %s", _attack_result, self.log_detail())

                gevent.sleep(1)
        except Exception as e:
            logger.error("attack script run error,  %s", self.log_detail(e))
            print e
            _ret['status'] = 'error'
        return _ret

    def _stop_attackinstance(self, attack_instance):
        logger.info("attack instance kill, %s", self.log_detail())
        try:
            attack_instance.kill()
        except Exception as e:
            logger.warning("kill attack instance error, %s", self.log_detail(e))

    def real_done(self):
        _ret = {'status': 'ok'}

        # 攻击是否存在，
        key = "{}.{}.{}".format(self.script_path, self.ip, self.port)
        _attack_instance = self.attack_dict.get(key)

        if _attack_instance:
            self._stop_attackinstance(_attack_instance)

            # 停止攻击
            if self.stop:
                self.attack_dict[key] = None
                return _ret

        _attack_instance = gevent.spawn(self._attack)
        self.attack_dict[key] = _attack_instance

        return _ret

    def __init__(self, script_path, ip, port, **kwargs):
        super(Attack, self).__init__(script_path, ip, port, **kwargs)
        self.stop = kwargs.get('stop', False)

class Dispatcher(object):
    def checker(self, script_path, ip, port):
        _checker = Checker(script_path, ip, port)
        return _checker.done()

    def attack(self, script_path, ip, port, kwargs):
        kwargs = json.loads(kwargs)
        _attack = Attack(script_path, ip, port, **kwargs)

        return _attack.done()


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)-5.5s : %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        filename=LOG_PATH or None)

    checker_thrift = thriftpy.load("oj.thrift", module_name="xoj_thrift")
    server = make_server(checker_thrift.xoj, Dispatcher(), '127.0.0.1', 6000)
    server.serve()
