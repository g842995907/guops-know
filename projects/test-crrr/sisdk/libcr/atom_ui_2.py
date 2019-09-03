#!/usr/bin/python
# -*- coding: utf-8 -*-
# @Time    : 19-4-4 上午8:52
# @Author  : wangheng
# @Email   : wangh@cyberpeace.cn
# @File    : atom_ui_2.py.py
# @Project : cpss

import datetime
import time
import sisdk.libcr.enums as Enums
from sisdk.messages import wrap_message_2
# 以下为了兼容proto2
from .proto2.cr_sysctrl2_pb2 import (sysctrl_set_title, sysctrl_set_logo, sysctrl_set_message, sysctrl_toast)


legends = [('red','红方'), ('blue','蓝方'), ('white','白方')]


class AtomUi(object):
    @staticmethod
    def mk_ui_toast(position=Enums.EnumPosition.left, icon=Enums.EnumToastIcon.information, text_title="untitled",
                    text_content="sample content", switch=Enums.EnumOnoff.on, duration=5, color=""):
        if position == Enums.EnumPosition.top:
            alpha = 1.0
        else:
            alpha = 0.8
        if not color:
            color = color
        msg = sysctrl_toast(positon=position,
                            icon=icon,
                            text_title=text_title,
                            text_content=text_content,
                            switch=switch,
                            duration=duration,
                            message_id=str(time.time()),
                            color=color,
                            alpha=alpha)
        return wrap_message_2(msg)


    @staticmethod
    def mk_ui_set_title(title_text="untitled"):
        msg = sysctrl_set_title(title_text=title_text)
        return wrap_message_2(msg)


    @staticmethod
    def mk_ui_set_logo(logo_url=""):
        msg = sysctrl_set_logo(logo_url=logo_url)
        return wrap_message_2(msg)


    @staticmethod
    def mk_ui_set_message(message="", datetime=""):
        msg = sysctrl_set_message(message_text=message,
                                  datetime=datetime)
        return wrap_message_2(msg)