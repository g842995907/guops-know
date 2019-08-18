- **聚合函数** sum  count  max  min  avg   round()四舍五入

```mysql
ount()
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

- **Concat()**函数  将多个字段拼接在一起

```mysql
# 将name和年龄字段放在一起
select Concat(name,' ', age ) from students; # 空格隔开

#()需要用引号
select Concat(name, '(', age,')') from students;
```

- 文本处理函数

```mysql
select Upper(name) from students;
# 将文本都大写
Length() 返回串的长度
Lower()  将文本小写
Ltrim() 去掉串左边的空格
RTrim() 去掉串右边空格
SubString() 返回子串字符
# 用来时间比较
Date() 返回日期时间的日期部分 
Day()  返回日期的天数
Year() 返回年
Month() 返回月
Time()  返回时间部分
DayOfWeek() 返回一个日期对应星期几

select name from students where date(public_date) = '2019-1-1';  # 时间是2019-1-1号的学生

select name from stduents where date(public_date) between '2019-1-1' and '2019-1-31'

select name from stduents where date(public_date) Year(public_date) = 2019 and Month(public_date) = 1;
# 2019年1月的学生；

```

