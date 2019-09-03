# coding:utf-8
'''A connection pool of MySQL in Django 1.5 based on DBUtils.'''
import MySQLdb
from common_framework.utils.DBUtils.PooledDB import PooledDB

class ConnectionWrapper(object):
    def __init__(self, connection):
        self._conn = connection

    def __getattr__(self, method):
        ''' 代理数据库连接的属性方法 '''
        return getattr(self._conn, method)

    def close(self):
        ''' 代理Django的关闭数据库连接 '''
        self._conn.close()

class DBWrapper(object):
    def __init__(self, module):
        self._connection = None
        self._db = module
        self._pool = {}

    def __getattr__(self, item):
        return getattr(self._db, item)

    def _clear_connections(self, **kwargs):
        ''' 关闭已有连接 '''
        conn = MySQLdb.connect(**kwargs)
        cursor = conn.cursor()
        sql = ''
        cursor.execute('show full processlist;')
        processlist = cursor.fetchall()
        for th in processlist:
            if th[3] == kwargs.get('db') and th[0] != conn.thread_id():
                sql += 'kill %s;' % th[0]
        if len(sql.split(';')) > 1:
            cursor.execute(sql)
        cursor.close()
        conn.close()

    def connect(self, *args, **kwargs):
        ''' 创建连接 '''
        db = kwargs.get('db')
        if db not in self._pool:
            size = kwargs.get('size')
            if 'size' in kwargs:
                kwargs.pop('size')
            self._clear_connections(**kwargs)
            self._pool[db] = PooledDB(self._db, mincached=size, maxcached=size, *args, **kwargs)
        self._connection = self._pool[db].connection()
        return ConnectionWrapper(self._connection)

