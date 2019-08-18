```python
l = []
for i in range(10):
	l.append({'num':i})
print(l)
[{'num': 0},{'num': 1},{'num': 2},{'num': 3},{'num': 4},{'num': 5},{'num': 6},{'num': 7}{'num': 8},{'num': 9}]

i = []
a = {"num":0}
for i in range(10):
    a['num'] = i
	l.append(a)
print(l)
[{'num': 9},{'num': 9},{'num': 9},{'num': 9},{'num': 9},{'num': 9},{'num': 9},{'num': 9}{'num': 9},{'num': 9}]

原因是:字典是可变对象,在下方的 l.append(a)的操作中是把字典 a 的引用传到列表 l 中,当后
续操作修改 a[‘num’]的值的时候,l 中的值也会跟着改变,相当于浅拷贝。

```

