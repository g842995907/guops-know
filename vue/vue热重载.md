## VUE热重载

webpack搭建的项目不能进行热重载
第一步：You can do it by adding following line to the /etc/sysctl.conf file:  在/etc/sysctl.conf文件下添加

```shell
fs.inotify.max_user_watches = 524288 

```

第二步执行命令: sudo sysctl -p

第三步：重启ide.
在不行升级npm 和node 的版本

