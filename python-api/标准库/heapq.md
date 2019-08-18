## `heaqp`



查找最大或最小的 N 个元素

3.4.1 问题

怎样从一个集合中获得最大或者最小的 N 个元素列表？

3.4.2 解决方案

`heapq` 模块有两个函数： `nlargest()`和 `nsmallest() `可以完美解决这个问题。

```python
import heapq
nums = [1, 8, 2, 23, 7, -4, 18, 23, 42, 37, 2]
print(heapq.nlargest(3, nums)) # Prints [42, 37, 23]
print(heapq.nsmallest(3, nums)) # Prints [-4, 1, 2]

两个函数都能接受一个关键字参数，用于更复杂的数据结构中：
portfolio = [
    {'name': 'IBM', 'shares': 100, 'price': 91.1},
    {'name': 'AAPL', 'shares': 50, 'price': 543.22},
    {'name': 'FB', 'shares': 200, 'price': 21.09},
    {'name': 'HPQ', 'shares': 35, 'price': 31.75},
    {'name': 'YHOO', 'shares': 45, 'price': 16.35},
    {'name': 'ACME', 'shares': 75, 'price': 115.65}
]
cheap = heapq.nsmallest(3, portfolio, key=lambda s: s['price'])
expensive = heapq.nlargest(3, portfolio, key=lambda s: s['price'])  # key跟一个匿名函数 指定什么排序
返回的列表数据
```

