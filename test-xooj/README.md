# OJ新模板

## 工程结构简介

|文件| 名称|描述符|
|:-: |:--:|:-------------------------------------------------|
|d  |  common_cms               |        框架后台|
|d  |  common_web               |        框架前台|
|d  |  common_*               |        基本框架app|
|d  |  dist                 |        whl安装包生成路径|
|-  |  make_whl.py          |        自动打包python脚本|
|-  |  manage.py            |        项目manage.py|
|d  |  media                |        上传文件路径, 或者一些系统资源|
|d  |  common_product              |        app -- 此app是基础app,包含了所有我们系统的app|
|-  |  requirement.txt      |        项目依赖的python库|
|-  |  setup.cfg            |        打包配置文件, 不要动|
|-  |  setup.sh             |        项目安装脚本, 待完善|
|-  |  setup_templet.py     |        打包模板,由make_whl.py调动|
|d  |  static               |        项目的静态文件|
|-  |  uninstall.sh         |        删除所有app脚本|
|d  |  x-oj                 |        项目配置主目录 |
|d  |  common_framework       |        新框架主要代码 |

## 新建app

**命令:**
```
django-admin startapp test-app
```

**注意事项:**

+ templates下创建一个与app同名的文件夹, 所有html模板都放在里面
+ templates下同名文件夹下最好在分为cms和web, 为了区分, 例如:

```
➜  practice_theory git:(develop_thj) ✗ tree
.
├── cms
│   └── task_list.html
└── web
    └── task_list.html

2 directories, 2 files

```
+ static 同理templates, 创建一个文件夹
+ 第三方库尽量放在同一路径下

## app的配置
+ django层级的配置直接在项目下的settings.py中
+ 每个app中新建一个setting.py,内容大致如下:
+ urls.py 中添加前端url映射,**cms_urls** 中添加后台url映射


```python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from common_framework.setting.settings import APISettings

DEFAULTS = {
    'MENU': (
        {
            'name': 'oj菜单一',
            'parent': None,
            'icon': {
                'style': 'font awesonme',
                'value': 'fa fa-tasks',
            },
            'href': 'http://www.qq.com'
        },
        {
            'name': 'oj菜单二',
            'parent': 'oj菜单一',
            'href': 'list',
        },
    ),
    'WEB_MENU': (
        {
            'name':'靶场接口',
            'parent': None,
        },
        {
            'name':'应用场景',
            'parent': '靶场接口',
            'href': 'list',
            'icon':{
                'style':'icon',
                'value':'oj-icon oj-icon-F004 font25P'
            }
        },
    ),
    'SLUG':'task',
    'RELY_ON': [
        'qingbao',
    ]
}
IMPORT_STRINGS = ()
api_settings = APISettings('TASK', None, DEFAULTS, IMPORT_STRINGS)
```

**配置说明**

***1. 总体配置***

| 名称      | 必须  |  类型 | 描述                                        |
|-----------|------ |-------|---------------------------------------------|
|MENU       |True   |dict   |后台菜单, 详细见例子, 没有则填写None         |
|WEB_MENU   |True   |dcit   |前台菜单, 没有则填写None                     |
|SLUG       |True   |string |url路径                                      |
|RELY_ON    |True   |list   |依赖的app的名称                              |

***2. MENU/WEB_MENU***:

| 名称      | 必须  |  类型 | 描述                                     |
|-----------|------ |-------|------------------------------------------|
|name       | True  |string |菜单名称                                  |
|parent     | True  |string |父菜单名称, 没有则写None                  |
|icon       | False |dict   |value: 字母图标, web_menu中为icon路径     |
|href       | True  |string |以"/", "http(s)"开头, 则为其本身, 其余的url为"/{slug}/{value}"|

***3. 自定义配置***
+ 在DEFAULTS中添加自定义配置, 比如添加一个TASK_NAME
```
DEFAULTS = {
    .....
    'TASK_NAME': 'tanghaijun'
}
```
+ 取数据的时候调用 api_settings.TASK_NAME 
+ 生产环境中, 修改默认配置, 在项目settings.py中添加:

```
TASK = {
    'SLUG' : 'setting_task',
    'TASK_NAME': 'change_task_default'
}
```

***4. api_settings***
每一个setting.py中必须申明一个api_settins, 形式如下:
```
api_settings = APISettings('TASK', None, DEFAULTS, IMPORT_STRINGS)
```
'TASK'为项目名称, 在生产环境中, 可以用其名称的字典可以替换默认配置, 实现自定义配置的目的
其他的参数, 详见代码文件

***5. IMPORT_STRINGS***
支持动态class的引用

## 发布app

### 打包
**命令:**
```
python make_whl.py
```

**注意事项:**

+ 升级版本的时候, 需要改版本号版本号信息存放在app目录下的__init__.py的文件中, 添加或修改下面内容

```
__title__ = 'task'
__version__ = '0.0.2'
__author__ = 'tang haijun'
__license__ = 'BSD 2-Clause'
__copyright__ = 'Copyright 2011-2017'

VERSION = __version__
```

+ 此打包脚本只是通用的打包方法, 特殊的需求可以自己写脚本进行打包, [更多学习][]
[更多学习]: http://www.thj8.win/2017/05/26/python-package/ "tang haijun blog"


### 安装,卸载
**安装命令**
```
pip install cp_task-0.0.1-py2.py3-none-any.whl
```

**卸载命令**
```
pip uninstall -y cp_task
```

### 升级

**命令**

```
pip install cp_task-0.0.2-py2.py3-none-any.whl
```

**注意事项:**

+ 此方法只是安装了包, migrate数据库, 更新数据库数据, 等其他工作要另外手动执行, 或者写个脚本
+ 只能往高版本升级, 若向下安装会出现意想不到的问题


### api.py
**函数命令规则:**

1 尽量单独使用小写字母‘l’，大写字母‘O’等容易混淆的字母。

2 模块命名尽量短小，使用全部小写的方式，可以使用下划线。

3 包命名尽量短小，使用全部小写的方式，不可以使用下划线。

4 类的命名使用CapWords的方式，模块内部使用的类采用_CapWords的方式。

5 异常命名使用CapWords+Error后缀的方式。

6 全局变量尽量只在模块内有效，类似C语言中的static。实现方法有两种，一是__all__机制;二是前缀一个下划线。

7 函数命名使用全部小写的方式，可以使用下划线。

8 常量命名使用全部大写的方式，可以使用下划线。

9 类的属性（方法和变量）命名使用全部小写的方式，可以使用下划线。

9 类的属性有3种作用域public、non-public和subclass API，可以理解成C++中的public、private、protected，non-public属性前，前缀一条下划线。

11 类的属性若与关键字名字冲突，后缀一下划线，尽量不要使用缩略等其他方式。

12 为避免与子类属性命名冲突，在类的一些属性前，前缀两条下划线。比如：类Foo中声明__a,访问时，只能通过Foo._Foo__a，避免歧义。如果子类也叫Foo，那就无能为力了。

13 类的方法第一个参数必须是self，而静态方法第一个参数必须是cls。

**引用规则:**

使用** from import as ** 结构

例如:

```python
from practice import api as practice_api

```
