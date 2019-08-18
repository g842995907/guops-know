# operator

##### operator模块是python中内置的操作符函数接口，它定义了一些算术和比较内置操作的函数。operator模块是用c实现的，所以执行速度比python代码快。

```python
from operator import *
rows = [
    {'fname': 'Brian', 'lname': 'Jones', 'uid': 1003},
    {'fname': 'David', 'lname': 'Beazley', 'uid': 1002},
    {'fname': 'John', 'lname': 'Cleese', 'uid': 1001},
    {'fname': 'Big', 'lname': 'Jones', 'uid': 1004}
]

row2 = [
    ('fname', 'Brian', 'lname', 'Jones', 'uid': 1003),
    ('fname': 'David', 'lname': 'Beazley', 'uid': 1002),
    ('fname': 'John', 'lname': 'Cleese', 'uid': 1001),
    ('fname': 'Big', 'lname': 'Jones', 'uid': 1004)
]
```

对以上按照某个字段排序

```python
from operator import itemgetter
rows_by_fname = sorted(rows, key=itemgetter('fname'))
rows_by_uid = sorted(rows2, key=itemgetter(1))  # 按照元祖的第二个值排序
print(rows_by_fname)
print(rows_by_uid)

# 运行结果
[{'fname': 'Big', 'uid': 1004, 'lname': 'Jones'},
	{'fname': 'Brian', 'uid': 1003, 'lname': 'Jones'},
	{'fname': 'David', 'uid': 1002, 'lname': 'Beazley'},
	{'fname': 'John', 'uid': 1001, 'lname': 'Cleese'}]

[
    ('fname': 'Big', 'lname': 'Jones', 'uid': 1004),
    ('fname', 'Brian', 'lname', 'Jones', 'uid': 1003),
    ('fname': 'David', 'lname': 'Beazley', 'uid': 1002),
    ('fname': 'John', 'lname': 'Cleese', 'uid': 1001),
]

# itemgetter() 函数也支持多个 keys，比如下面的代码
rows_by_lfname = sorted(rows, key=itemgetter('lname','fname'))

```

itemgetter()` 有时候也可以用 `lambda` 表达式代替，比如：

```python
rows_by_fname = sorted(rows, key=lambda r: r['fname'])
rows_by_lfname = sorted(rows, key=lambda r: (r['lname'],r['fname']))

# min ,max也是可以
min(rows, key=itemgetter('uid'))
{'fname': 'John', 'lname': 'Cleese', 'uid': 1001}

max(rows, key=itemgetter('uid'))
{'fname': 'Big', 'lname': 'Jones', 'uid': 1004}

```

