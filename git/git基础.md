## Git个人仓库

##### 1、在项目中初始化git

```shell
git init

git第一次提交的时候,要配置用户名和邮箱,tell me who you are
git config --global user.email "429377083@qq.com"
git config --global user.name "zhangbingshuai"
```

##### 2、在远程创建仓库并和本地关联

```shell
git remote add origin 'https://github.com/guyibang/TEST2.git'

# 第一次提交远程仓库为空加-u
git push -u origin master

# 当远程仓库有本地没有的东西的时候可以先将内容合并
git pull --rebase origin master
```



##### 3、简单常用命令

```shell
# 查看状态
git status 

# 提交
git add .

# 提交到仓库
git commit -m "xxx"

# 取消仓库区的
git reset HEAD

# 对比暂存区和工作区的代码
git diff test.txt

# 先拉代码 后push
# 提交先
git fetch
git merge dev(分支)

```