## 查询语句

**避免使用!=或＜＞、IS NULL 或 IS NOT NULL、IN ，NOT IN 等这样的操作符**

##### 完整的查询语句

```mysql
select distinct *
from   表名
where ....
like...
group by ... having ...
order by ...
limit start,count

# 执行顺序为：
select distinct *
from 表名
where ....
like...
group by ...
having ...
order by ...
limit start,count
```

- **聚合函数** sum  count  max  min  avg   round()四舍五入

```mysql
count()
# 查询班级有多少人

select count(*) from students;

max()
# 查询最大的年龄

select max(age) from students;

# 查询最高身高的学生的名字 (子查询)
select name from students where height = (select max(height) from students);  
# 四舍五入 round(123.23 , 1) 保留1位小数, 四舍五入
select round(avg(age),2) from students;

```

- **消除重复行**

```mysql
select district gender from students;
```

- **模糊查询** 

```mysql
## like % 替换1个或者多个 _替换一个
select name from students where name like "小%";
# 查询速度较慢
```

- `rlike` **正则**

```mysql
 # 查询以 周开始的姓名
 select name from students where name rlike "^周.*";
```

- `not in` **不在非连续的范围之内**

```mysql
# 年龄不是 18、34岁之间的信息
select name,age from students where age not in (18, 34);
select * from students where age < 18 or age > 34;

```

- **排序**

```mysql
# order by 字段  asc从小到大排列，即升序  desc从大到小排序，即降序
# 查询年龄在18到34岁之间的男性，按照年龄从小到到排序  不允许 111>x>11
select * from students where (age between 18 and 34) and gender=1 order by age;
select * from students where (age between 18 and 34) and gender=1 order by age asc;
```

- `in` **表示在一个非连续的范围内 即单个范围**

```mysql
select * from students where id in(1,3,8);
# 	between ... and ...表示在一个连续的范围内
select * from students where id between 3 and 8;
```

- **比较运算符**

```mysql
# 例1：查询编号大于3的学生select round(avg(age),2) from students;
select * from students where id > 3;
# 例2：查询编号不大于4的学生
select * from students where id <= 4;
# 例3：查询姓名不是“黄蓉”的学生
select * from students where name != '黄蓉';
```

- **分组**

```mysql
group by

1. group by的含义:将查询结果按照1个或多个字段进行分组，字段值相同的为一组
2. group by可用于单个字段分组，也可用于多个字段分组

group by + `group_concat()`

1. `group_concat`(字段名)可以作为一个输出字段来使用，
2. 表示分组之后，根据分组结果，使用`group_concat()`来放置每一组的某字段的值的集合
```



```mysql
select gender from students group by gender;
select gender,group_concat(name) from students group by gender;
```

group by + 集合函数

```mysql
select gender,group_concat(age) from students group by gender;

# 分别统计性别为男/女的人年龄平均值
select gender,avg(age) from students group by gender;

#分别统计性别为男/女的人的个数
select gender,count(*) from students group by gender;

```

group by + having

```mysql
 select gender,count(*) from students group by gender having gender = 1;
 
 # 除了男生以外的分组的人数
 select gender,count(*) from students group by gender having gender != 1;
 
 # 查询平均年龄超过30岁的性别，以及姓名
 select gender, group_concat(name) from students group by gender having avg(age) > 30;

```

group by + with `rollup`

```mysql
# with rollup的作用是：在最后新增一行，来记录当前列里所有记录的总和

select gender,count(*) from students group by gender with rollup;
```

- **连接查询 将某两个表的某种条件合并在一起**

```mysql
table1 inner join table2 on 设置内连接条件  --> 内连接查询

select * from students, teacher where students.age = teacher.age;
# inner join 类似
```

- 子查询

```mysql
# 查询班级学生的平均身高的学生
select * from students where age > (select avg(age) from students);
# in用的多
select * from students where age in (select age from teacher where id = 5);

# 也可以是条件
select name (select count(*) from teacher where teacher.id = students.id) as order from students order by name;
```



