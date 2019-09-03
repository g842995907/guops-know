# -*- coding: utf-8 -*-
import logging
import os

from django.conf import settings
from django.utils.module_loading import import_string

from cloghandler import ConcurrentRotatingFileHandler

from common_framework.utils import common as common_util

DEFAULT_LOG_PATH = os.path.join(settings.BASE_DIR, 'log/oj.log')

log_level = {1: "DEBUG", 2: "INFO", 3: "WARN", 4: "ERROR", 5: "CRITICAL"}


def get_log_parent_path():
    log_path = get_log_path()

    log_name_idx = log_path.rfind('/') + 1
    _log_path = log_path[:log_name_idx]
    return _log_path


def get_log_path():
    logging = settings.LOGGING
    handlers = logging.get('handlers')
    if handlers is None:
        return ""

    log_file = handlers.get('logfile')
    if log_file is None:
        return ""

    log_path = log_file.get('filename')
    if log_path is None:
        log_path = DEFAULT_LOG_PATH

    return log_path


def get_log_file_list():
    log_path = get_log_path()

    log_name_idx = log_path.rfind('/') + 1
    log_name = log_path[log_name_idx:]

    _log_path = log_path[:log_name_idx]
    log_list = []
    for top, dirs, files in os.walk(_log_path):
        for _file in files:
            if _file.startswith(log_name):
                log_list.append(
                    {
                        'name': _file,
                        'size': common_util.get_file_size(os.path.join(top, _file)),
                        'create_time': common_util.get_file_create_time(os.path.join(top, _file)),
                        'modify_time': common_util.get_file_modify_time(os.path.join(top, _file))
                    }
                )
    log_list = sorted(log_list, key=lambda a: a.get('name'))
    return log_list


def configure_logging(logging_config, custom_logging_settings):
    logging_config_func = import_string(logging_config)

    if custom_logging_settings:
        logging_config_func(custom_logging_settings)


CRITICAL = 50
FATAL = CRITICAL
ERROR = 40
WARNING = 30
WARN = WARNING
INFO = 20
DEBUG = 10
NOTSET = 0

_levelNames = {
    CRITICAL: 'CRITICAL',
    ERROR: 'ERROR',
    WARNING: 'WARNING',
    INFO: 'INFO',
    DEBUG: 'DEBUG',
    NOTSET: 'NOTSET',
    'CRITICAL': CRITICAL,
    'ERROR': ERROR,
    'WARN': WARNING,
    'WARNING': WARNING,
    'INFO': INFO,
    'DEBUG': DEBUG,
    'NOTSET': NOTSET,
}


def set_loging_param(level, size, backup_count):
    from django.core.cache import cache
    cache.set("get_log_info_log_level", level, 60 * 60 * 5)
    cache.set("get_log_info_log_size", size, 60 * 60 * 5)
    cache.set("get_log_info_log_count", backup_count, 60 * 60 * 5)
    logger_root = logging.root

    # 设置日志级别
    logger_root.level = _levelNames.get(log_level.get(level))

    handlers = logger_root.handlers

    # only change ConcurrentRotatingFileHandler, in this project has other Handler(StramHandler)
    for handle in handlers:
        if isinstance(handle, ConcurrentRotatingFileHandler):
            handle.maxBytes = size * 1024 * 1024
            handle.backupCount = backup_count

