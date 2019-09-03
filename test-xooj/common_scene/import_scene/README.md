## 准备

1. 配置OJ登录信息：

配置utils.py文件中 OJ_HOME, OJ_USER, OJ_PASSWORD，填写正确的登录信息

EXISTS_ACTION，这个配置表示遇到同名的场景时的操作，update表示更新场景，delete表示先删除再重新创建一个场景，pass表示不修改之前的场景

OPERATORS 字段定义了常用操作机的信息，适用于yaml文件中的operator字段

2. 配置openstack用户名密码：

配置utils.py文件中OS_AUTH_STR这个变量的用户名和密码

3. 修改debug

在导入前要保证OJ项目的Debug模式是开启的

4. 将git上的课程/题目项目下载到脚本同一目录下


## 导入课程、练习

1. 导入课程

```bash
# /bin/bash course_convert.sh <课程目录>
# 目录后面不需要加斜杠 "/"
```

2. 导入练习

```bash
# /bin/bash exam_convert.sh <题目目录> [类型]
# 目录后面不需要加斜杠 "/"
#类型为web,pwn等，可选，默认导入全部类型
```

