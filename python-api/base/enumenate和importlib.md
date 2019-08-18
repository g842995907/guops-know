## importlib模块的使用

动态加载模块

```python
import importlib
module = importlib.import_module("文件名/模块名") 
#这个模块名以自己启动文件为准，返回的是一个模块对象，可以直接调用里面的方法
obj=getattr(module,obj_str,default)
# moudle是模块对象,obj_str是模块里面的对象字符串"名字",得到的就是obj对象

# obj_str不存在的话就使用默认值 没有默认值的情况下就触发 AttributeError。

```



## enumerate函数

enumerate() 函数用于将一个可遍历的数据对象(如列表、元组或字符串)组合为一个索引序列，同时列出数据和数据下标，一般用在 for 循环当中。

Python 2.3. 以上版本可用，2.6 添加 start 参数。

### 语法

以下是 enumerate() 方法的语法:

```python
enumerate(sequence, [start=0])
```

