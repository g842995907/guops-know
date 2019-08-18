### `mysql`知识点

- 查看库结构、表结构

```mysql
SHOW CREATE DATABASE DATABASE_NAME;

SHOW CREATE TABLE TABLE_NAME; # 可以查看引擎
```

- 查看表字段结构

```mysql
SHOW COLUMNS FROM TABLE_NAME;
DESC TABLE_NAME;
```

- 查看用户权限

```mysql
use mysql;
# 查看所有用户及权限
SELECT host,user FROM USER; 

# 查看某个用户拥有的权限
SHOW GRANTS FOR 'USERNAME'@'localhost'; 
SHOW GRANTS FOR 'USERNAME'@'%'
SHOW GRANTS FOR USERNAME; # 默认是查看是否有远程连接的权限
```

- 用户授权

```mysql
# 创建用户 不授权
CREATE USER 'username'@'localhost' identified by 'password' # 不管理其他权限	

# 常用权限主要包括：create、alter、drop、insert、update、delete、select等
# 如果分配所有权限，可以使用all

# 给已有用户授权
grant 权限列表(CURD) on 数据库.* to '用户名'@'访问主机';
GRANT ALL PRIVILEGES ON cr.* TO 'cr'@'%';

# 这样的方式是创建用户及授权;
grant 权限列表(CURD) on 数据库.* to '用户名'@'访问主机' identified by '密码';

grant all on jing_dong.* to 'laowang'@'localhost' identified by '123456';

grant all privileges on *.* to "laoli"@"%" identified by "12345678";
# 给所有表所有权限

# 修改账户密码
SET PASSWORD FOR 'username'@'host' = PASSWORD('newpassword');

# 删除用户
DROP USER 'username'@'host';

# 以上最好刷新权限
FLUSH PRIVILEGES;

# 所有权限远程和本地不共享密码，需要创建两次 远程和本地
```

- `mysql`远程登录

```shell
# 修改sudo vim  /etc/mysql/mysql.conf.d/mysql.cnf

# 把 bind-address = 127.0.0.1  这行注释，再保存退出。重启MySQL服务：

# 重启mysql服务 
sudo service mysql restart
```



