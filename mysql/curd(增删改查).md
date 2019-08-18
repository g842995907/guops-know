## 增删改查(curd)

**curd的解释: 代表创建（Create）、更新（Update）、读取（Retrieve）和删除（Delete）**

#### 增加

```mysql
insert into 表名 values(...),(),(),(),() # 需要从id开始加

# 部分列插入：值的顺序与给出的列顺序对应
insert into 表名(列1,...) values(值1,...),(),(),()...

insert into 表名(列1,...) select...语句

# 将分组结果写入到goods_cates数据表
insert into goods_cates (name,description) select cate_name,description from goods group by cate_name;
```



#### 修改

```mysql
update 表名 set 列1=值1,列2=值2... where 条件
```



#### 删除

```mysql
delete from 表名 where 条件;

delete from table_name; # 直接删除表中的所有内容

# truncate table
truncate table table_name;
# 会把表中的所有数据删除 

delete 和 truncate table区别
# truncate table 删除表中的所有行，但表结构及其列、约束、索引等保持不变。新行标识所用的计数值重置为该列的种子。
# 如果想保留标识计数值，请改用 delete。
# truncate 不可以where,删全部表
# truncate 没有delete回滚方便
```



