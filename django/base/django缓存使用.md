# django缓存使用

### 设置缓存：

​	在项目的setting.py里面可以通过CACHES配置缓存，django中可用的缓存系统有Memcached、数据库、文件、本地内存，下面一一讲解。

## Memcached:

​	Memcached是Django本地支持的最快速，最高效的高速缓存类型，它是一个完全基于内存的缓存服务器,可以大文件和视频的存储，也是django中到目前为止最有效率的可用缓存。

​	 在安装Memcached之后，您需要安装Memcached绑定。 有几个Python Memcached绑定可用; 最常见的两个是**python-memcached**和pylibmc。

```python

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
    }
}

# 也可以绑定多台

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': [
            '172.19.26.240:11211',
            '172.19.26.242:11212',
            '172.19.26.244:11213',
        ]
    }
}
```

## 数据库储存：
  Django可以将其缓存的数据存储在数据库中。 如果你有一个快速，索引良好的数据库服务器，这最好。
将数据库表用作缓存后端：
将BACKEND设置为django.core.cache.backends.db.DatabaseCache
将LOCATION设置为表名，即数据库表的名称。 这个名称可以是任何你想要的，只要它是一个尚未在数据库中使用的有效表名即可。在这个例子中，缓存表的名字是my_cache_table：  

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'my_cache_table',# 数据库的名字
    }
}
```


​    在上面操作前，我们还没建好缓存表，所以首先我们应该创建好缓存表，使用如下命令，注意cache_table_name不要和数据库中已经存在的表名冲突：

```python
python manage.py createcachetable [cache_table_name]  
#这里cache_table_name即为上面的my_cache_table

```



这将在您的数据库中创建一个表格，该表格采用Django的数据库缓存系统所需的适当格式。 该表的名称取自LOCATION。
    如果您使用多个数据库缓存，createcachetable会为每个缓存创建一个表。
    如果您使用多个数据库，createcachetable会观察数据库路由器的allow_migrate（）方法。
    像迁移一样，createcachetable不会触及现有的表。 它只会创建缺少的表格。
    要打印将要运行的SQL，而不是运行它，请使用createcachetable --dry-run选项。

#### 本地内存缓存：

​    如果你想具有内存缓存的优点但有没有能力运行Memcached的时候，你可以考虑本地内存缓存，这个缓存是多进程和线程安全的，后端设置为django.core.cache.backends.lovMemCache

```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}
```

### 缓存参数

```python

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.filebased.FileBasedCache',
        'LOCATION': '/var/tmp/django_cache',
        "KEY_PREFIX":"defualt-default",
        'TIMEOUT': 60,
        'OPTIONS': {
            'MAX_ENTRIES': 1000，
            'server_max_value_length': 1024 * 1024 * 2,
        }
    }
}

# TIMEOUT表示时间
# MAX_ENTRIES最大缓存的数量
# KEY_PREFIX 缓存的前缀
# server_max_value_length 单个文件大小最大规格
```

每个视图的缓存：
    使用缓存框架的更细化的方式是缓存单个视图的输出。 django.views.decorators.cache定义了一个cache_page修饰器，它可以自动缓存视图的响应。 它很容易使用（请注意，为了便于阅读，我们将其写为60 * 15， 即15分钟。还要记得要先导入cache_page）：

```python
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)
def my_view(request):
    ...
    '''
    cache_page(timeout, [cache=cache name], [key_prefix=key prefix])
    cache_page只接受一个参数和两个关键字参数，
    timeout是缓存时间，以秒为单位
    cache：指定使用你的CACHES设置中的哪一个缓存后端
    key_prefix：指定缓存前缀，可以覆盖在配置文件中CACHE_MIDDLEWARE_KEY_PREFIX的值
    '''

```

也可以在路由中配置

```python
urlpatterns = [
    path('foo/<int:code>/', cache_page(60 * 15)(my_view)),
]
```



#### 底层缓存API：

有时候我们并不想缓存整个视图，只是想缓存某个数据库检索的结果，事实上有时候缓存整个渲染页面并不会给你带来太多好处。例如，也许您的网站包含一个视图，其结果取决于几个复杂的查询，其结果会以不同的时间间隔进行更改。 在这种情况下，使用每个站点或每个视图缓存策略提供的整页缓存并不理想，因为您不希望缓存整个结果（因为一些数据经常变化）， 但你仍然想缓存很少改变的结果。

对于这种情况，Django公开了一个简单的底层缓存API。 您可以使用此API将对象以任意级别的粒度存储在缓存中。 您可以缓存任何可以安全序列化的Python对象：字符串，字典，模型对象列表等。 

```python
from django.core.cache import caches
cache1 = caches['myalias']
cache2 = caches['myalias']
cache1 is cache2
True
```

>>> **基本用法：**
>>>
>>> ```python
>>> cache.set('my_key', 'hello, world!', 30)
>>> cache.get('my_key')
>>> 'hello, world!'
>>> ```
>>>
>>> 键应该是一个str，并且值可以是任何可Python对象。
>>> 超时参数是可选的，默认为CACHES设置中相应后端的超时参数（如上所述）。 这是值应该存储在缓存中的秒数。 传入无超时将永远缓存该值。 超时0不会缓存该值。
>>> 如果该对象不存在于缓存中，则
>>>
>>> ```python
>>> cache.get（）返回None：
>>> 
>>> cache.get('my_key')
>>> None
>>> ```
>>>
>>>
>>> 只有在键不存在的情况下才能添加键，请使用add（）方法。 它采用与set（）相同的参数，但如果指定的键已经存在，它不会尝试更新缓存：
>>>
>>> ```python
>>> cache.set('add_key', 'Initial value')
>>> cache.add('add_key', 'New value')
>>> cache.get('add_key')
>>> 'Initial value'
>>> ```
>>>
>>>
>>> 还有一个get_many（）接口只能访问一次缓存。 get_many（）返回一个字典，其中包含您要求的实际存在于缓存中的所有密钥（并且尚未过期）：
>>>
>>> ```python
>>> cache.set('a', 1)
>>> cache.set('b', 2)
>>> cache.set('c', 3)
>>> cache.get_many(['a', 'b', 'c'])
>>> {'a': 1, 'b': 2, 'c': 3}
>>> # 您可以使用delete（）显式删除键。 这是清除特定对象缓存的简单方法：
>>> cache.delete('a')
>>> 
>>> ```
>>>
>>> 
>>>
>>> 