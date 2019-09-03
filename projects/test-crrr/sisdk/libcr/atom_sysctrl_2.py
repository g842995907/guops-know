#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 19-4-4 上午8:51
# @Author  : wangheng
# @Email   : wangh@cyberpeace.cn
# @File    : atom_sysctrl_2.py
# @Project : cpss

import time
import datetime
from .proto2.cr_sysctrl2_pb2 import sysctrl_sync_timing as sysctrl_sync_timing_2
from sisdk.messages import wrap_message_2

class AtomSysctrl(object):
    @staticmethod
    def mk_sync_timing(display_countdown=True, countdown_time=0):
        # TODO:如果到0点以后，这个信息要更新到第二天
        # TODO:在回放时，应当关闭自动倒数
        d = datetime.datetime.now()
        weekday = d.weekday()
        the_week = u'星期' + [u'一', u'二', u'三', u'四', u'五', u'六', u'日'][weekday]
        the_date = d.strftime('%Y-%m-%d')
        server_time = int(time.time())
        msg = sysctrl_sync_timing_2(the_week=the_week,
                                    the_date=the_date,
                                    countdown_time=countdown_time,
                                    server_time=server_time,
                                    display_countdown=display_countdown)
        return wrap_message_2(msg)