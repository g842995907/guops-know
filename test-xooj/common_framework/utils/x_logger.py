import logging

from django.core.cache import cache

from system_configuration.utils.loger import logset


def get_log_info(key):
    if not key:
        return None

    _key = "get_log_info_{}".format(key)
    value = cache.get(_key)
    if value:
        return value

    from system_configuration.models import SystemConfiguration
    obj = SystemConfiguration.objects.filter(key=key).first()
    if obj:
        cache.set(key, int(obj.value), 60 * 60 * 5)
        return int(obj.value)

    return None


def load_log_config():
    context = {'log_level': 2, 'log_size': 20, 'log_count': 5}

    try:
        from system_configuration.models import SystemConfiguration
        log_level = get_log_info('log_level')
        log_size = get_log_info('log_size')
        log_count = get_log_info('log_count')

        if log_level:
            context['log_level'] = log_level

        if log_size:
            context['log_size'] = log_size

        if log_count:
            context['log_count'] = log_count

        logset.set_loging_param(
            context.get('log_level'),
            context.get('log_size'),
            context.get('log_count')
        )

    except Exception as e:
        pass


def get_x_logger(name):
    return logging.getLogger(name)
