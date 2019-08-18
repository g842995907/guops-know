## Git用户提交设置

#### 1、用户名密码设置长期

```shell
git config --global user.name "yourName"
git config --global user.email "email@example.com"
# 需要先提交一次才可以进行下面的操作

# 设置记住密码（默认15分钟）：
git config --global credential.helper cache
# 如果想自己设置时间，可以这样做(1小时后失效)：可以把这个时间设置长一点
git config credential.helper 'cache --timeout=3600'
# 长期存储密码：
git config --global credential.helper store

# 需要设置simple
 git config --global push.default simple
 
# linux下载看查看配置在用户目录下
cat ~/.gitconf
# 查看哪些文件
cat ~/.git-credentials	
```

### 2、ssh秘钥登录

```shell
ssh-keygen -t rsa
# 不用设置密码，全部回车 会在用户目录下.ssh/文件夹下生成两个文件id_rsa 和id_rsa.pub

将id_rsa.pub文件里面的内容放到远程仓库上，可以正常使用
```

#### 3、ssh切换成用户名密码提交

```shell
# 1， 取消当前的分支对远程分支的关联

git remote rm origin

# 2， 以HTTP的方式重新关联

git remote add origin http://username:password@project_dir/project.git

# 3， 本地分支和远程分支的关联

git pull
```



