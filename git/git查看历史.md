## Git历史回退

**1、查看历史版本**

```shell
git log

git log --pretty=oneline
#等号两边没有空格

# 或者
git reflog # 这个可以回退历史记录,比较好用
```

**2.回退版本**

方案一：

- HEAD表示当前最新版本

- HEAD^表示当前最新版本的前一个版本

- HEAD^^表示当前最新版本的前两个版本，**以此类推...**

- HEAD~1表示当前最新版本的前一个版本

- HEAD~10表示当前最新版本的前10个版本，**以此类推...**

  ```shell
  
  git reset --mixed HEAD~1 # 默认
  回退一个版本,且会将暂存区的内容和本地已提交的内容全部恢复到未暂存的状态,不影响原来本地文件(未提交的也 
  不受影响) 
  git reset --soft HEAD~1 
  回退一个版本,不清空暂存区,将已提交的内容恢复到暂存区,不影响原来本地的文件(未提交的也不受影响) 
  git reset --hard HEAD~1 
  git reset --hard HEAD^
  回退一个版本,清空暂存区,将已提交的内容的版本恢复到本地,本地的文件也将被恢复的版本替换
  ```



方案二：当版本非常多时可选择的方案

- 通过每个版本的版本号回退到指定版本

  git reset --hard 版本号

##### 3、撤销修改

```shell
git checkout 文件名

# 提交到暂存区 取消提交
git reset HEAD 文件名

# 撤销本地commit
git log
git reset --hard commit_id
```

不要轻易使用