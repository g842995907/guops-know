### ORM优化

1.数据库技术进行优化，包括给字段加索引，设置唯一性约束等等；

2.查询过滤工作在数据库语句中做，不要放在代码中完成（看情况）；

3.如果要一次查询出集合的数量，使用count函数，而不是`len`函数，但是如果后面还需要到集合，那就用`len`，因为count还需要进行一次数据库的操作；使用`QuerySet.count()`代替`len(queryset)`,虽然这两个处理得出的结果是一样的，但前者性能优秀很多。同理判断记录存在时，`QuerySet.exists()`比`if queryset`实在强得太多了

4.避免过多的使用count和exists函数；

5.如果需要查询对象的外键，则使用外键字段而不是使用关联的外键的对象的主键；

列子:

```python
a.b_id # 正确
a.b.id # 错误
```

6.在通过all语句查询时，不要做跨表查询，只查询当前表中有的数据，否则查询语句的性能会下降很多;

 比如：a表存在外键b表

```	python
a.b.all()
```

7.如果想要查询其他表的数据，则加上select_related(`prefetch_related()`)(`ForeignKey`字段名，其实就是主动联表查询，性能也会下降)，如果有多个，则在括号中加上;



8.加only参数是从查询结果中只取某个字段,而另外一个defer方法则是从查询结果中排除某个字段；同样`QuerySet.defer()`和only()对提高性能也有很大的帮助，一个实体里可能有不少的字段，有些字段包含很多元数据，比如博客的正文，很多字符组成，`Django`获取实体时（取出实体过程中会进行一些python类型转换工作），我们可以延迟大量元数据字段的处理，只处理需要的关键字段，这时`QuerySet.defer()`就派上用场了，在函数里传入需要延时处理的字段即可；而only()和defer()是相反功能

9.不要获取你不需要的东西，可以通过values和value_list实现;



```python
values返回的是字典数组，比如：[{'key1': value1, 'key2': value2}, {'key1': value3, 'key2': value4}]
value_list返回的是tuple数组 [('value1', 'value2'), ('value3', 'value4')]
value_list+flat=True返回的是数组 ['value1', ...]
```

10.如果想知道是否存在至少一个结果，使用exists，而不是使用`if QuerySet`；但是如果后面需要用到前面的`QuerySet`，那就可以使用if 判断;

11.在任何位置使用`QuerySet.exists()`或者`QuerySet.count()`都会导致额外的查询;

12.不要做无所谓的排序，排序并非没有代价，每个排序的字段都是数据库必须执行的操作;

13.如果要插入多条数据，则使用bulk_create来批量插入，减少`sql`查询的数量;

14.对于缓存的`QuerySet`对象使用with标签，可以让数据被缓存起来使用;

15.使用`QuerySet.extra`明确的指出要查询的字段；

```python
Entry.objects.extra(select={'new_id': "select col from sometable where othercol > %s"}, select_params=(1,))

Entry.objects.extra(where=['headline=%s'], params=['Lennon'])
Entry.objects.extra(where=["foo='a' OR bar = 'a'", "baz = 'a'"])

Entry.objects.extra(select={'new_id': "select id from tb where id > %s"}, select_params=(1,), order_by=['-nid'])
```

16.批量的更新和删除则使用Queryset.update和delete函数，但是更新操作注意对象的缓存；

17.使用`QuerySet.Iterator`迭代大数据； 

当你获得一个queryset的时候，django会缓存下来，保存在内存中，如果需要对queryset进行多次的循环，那么这种缓存无可厚非； 但是如果你只需要进行一次的循环，那么其实并不需要缓存，这个使用就可以使用iterator；

比如:

```python
for book in Books.objects.all().iterator():
  do_stuff(book)
```

18.如果想判断是否存在外键，只需要判断外键的id即可；

19.不要在循环中查询，而是提前取出，并且做好映射关系，这样在循环中直接通过字典的形式获取到;

20.当计算出一个`QuerySet`的时候，如果还需要进行多次循环的话，则可以先保留着这个缓存，但是如果只是使用一次的话，没有必要使用到缓存;