import functools

from django.db import connections


def close_old_connections():
    for conn in connections.all():
        conn.close_if_unusable_or_obsolete()


def promise_db_connection(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        close_old_connections()
        return func(*args, **kwargs)
    return wrapper
