# mysql备份及恢复

#### 备份

- 运行mysqldump命令

```mysql
mysqldump –uroot –p 数据库名 > python.sql;
```

#### 恢复

- 连接mysql，创建新的数据库
- 退出连接，执行如下命令

mysql -uroot –p 新数据库名 < python.sql



**如何把整个数据库导出来，再导入指定数据库中？**

导出：

​    mysqldump [-h 主机] -u 用户名 -p 数据库名 > 导出的数据库名.sql

导入指定的数据库中:

第一种方法：

​    mysqldump [-h 主机] -u 用户名 -p 数据库名 < 导出的数据库名.sql



第二种方法：

先创建好数据库，因为导出的文件里没有创建数据库的语句，如果数据库已经建好，则不用再创建。

​    create database example charset=utf8;（数据库名可以不一样）

切换数据库：

​    use example;

导入指定 sql 文件：

​    mysql>source /path/example.sql;

