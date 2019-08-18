- **`nametuple`**命名字典

作用：可以像对象.属性拿到值，而且也可以用过索引 同时有元祖的其他属性

```python
collections.namedtuple(typename, field_names, verbose=False, rename=False) 
# typename：元组名称
# field_names: 元组中元素的名称
# rename: 如果元素名称中含有 python 的关键字，则必须设置为 rename=True
# verbose: 默认就好

from collections import namedtuple

# 定义一个namedtuple类型User，并包含name，sex和age属性。
User = namedtuple('User', ['name', 'sex', 'age'])

# 创建一个User对象
user = User(name='Runoob', sex='male', age=12)

# 获取所有字段名
print( user._fields )
>> ('name', 'sex', 'age')

# 也可以通过一个list来创建一个User对象，这里注意需要使用"_make"方法
user = User._make(['Runoob', 'male', 12])

print( user )
# User(name='user1', sex='male', age=12)


# 修改对象属性，注意要使用"_replace"方法
user = user._replace(age=22)
print( user )
# User(name='user1', sex='male', age=22)

# 将User对象转换成字典，注意要使用"_asdict"
print( user._asdict() )
# OrderedDict([('name', 'Runoob'), ('sex', 'male'), ('age', 22)]) 有序字典
```



- ### `deque`双向队列

```python
from collections import deque
q = deque(['a', 'b', 'c'])
q.append('x')
q.appendleft('y')
q.pop()
q.popleft()
q.remove()
q.extend(['a'])
q.extendleft(['c'])
q.clear()

deque(['y', 'a', 'b', 'c', 'x'])

```

- Counter类

```python
>>> c = Counter()  # 创建一个空的Counter类
>>> c = Counter('gallahad')  # 从一个可iterable对象（list、tuple、dict、字符串等）创建
>>> c = Counter({'a': 4, 'b': 2})  # 从一个字典对象创建
>>> c = Counter(a=4, b=2)  # 从一组键值对创建
Counter({'a': 2, 'b': 2, 'c': 1, 'd': 1, 'e': 1, 'f': 1, 'g': 1})

c = Counter('which')
c.update('witch')  # 使用另一个iterable对象更新

# 减少则使用subtract()方法：
c = Counter('which')
c.subtract('witch')  # 使用另一个iterable对象更新

# 算术和集合
>>> c = Counter(a=3, b=1)
>>> d = Counter(a=1, b=2)
>>> c + d  # c[x] + d[x]
Counter({'a': 4, 'b': 3})
>>> c - d  # subtract（只保留正数计数的元素）
Counter({'a': 2})
>>> c & d  # 交集:  min(c[x], d[x])
Counter({'a': 1, 'b': 1})
>>> c | d  # 并集:  max(c[x], d[x])
Counter({'a': 3, 'b': 2})
```

