## DDL(数据库定义语言) 

- 创建数据库

```MYSQL
create database 数据库名 charset=utf8;
```

- 删除数据库

```mysql
drop database 数据库名;
```

- 创建表

```mysql
create table students(

    id int unsigned primary key auto_increment not null,

    name varchar(20) default '',

    age tinyint unsigned default 0,

    height decimal(5,2),

    gender enum('男','女','人妖','保密'),

    cls_id int unsigned default 0
	
    # 或者可以在最后指定主键
    # primary key(id)
    # foreign key(cls_id) references 表名(字段)
)
```

- 修改表-添加字段和约束

```mysql
alter table 表名 add 列名 类型及约束;

# 直接添加约束
alter table Teacher add unique(TeaName); # 不能重复
alter table Teacher add primary key (TeaId) # 主键

# 外键的两个字段 自身不能是主键 添加的必须是主键 这两个字段的类型约束必须相同
alter table 表名 add foreign key(列名) references 表名(字段)    # 主表(列名)--外键

alter table Teacher add default '123' for TeaAddress # --默认约束
alter table Teacher add check (TeaAge>0) # --范围约束
```

- **Alter** **table** **表名** **add** **constraint** **约束 字** **约束类型**(列名)

```mysql
# -----添加约束(命名)----------- 有个名字 可以用名字删除约束

alter table Teacher add constraint PK_1 primary key (TeaId)--主键约束

alter table Teacher add constraint UN_1 unique(TeaName)--唯一约束

alter table Teacher add constraint CK_1 check (TeaAge>0)--范围约束

```

- 删除约束

```mysql
alter table 表名 drop constraint 约束名--删除约束


alter table Teacher drop constraint PK_1 --删除主键约束

alter table Teacher drop constraint UN_1 --删除唯一约束

```

- 修改表-修改字段：重命名版

```mysql
alter table 表名 change 原名 新名 类型及约束;
```



- 修改表-修改字段：不重命名版

```mysql
alter table 表名 modify 列名 类型及约束;

```

- 添加外键约束

```mysql
alter table 表名 add foreign key(列名) references 表名(字段)
```



- 修改表-删除字段

```mysql
alter table 表名 drop 列名;

```

- 删除表

```mysql
drop table 表名;
```

- 重命名表

```mysql
rename table old_name to new_name;

alter table old_tp_table_name rename new_tp_table_name;
```

