## 个人赛-检测

## 远程命令执行


### 题目描述

服务器上提供了python的交互页面，此时发生了getshell，请确认发生原因

### 出题思路

 * 抓取数据包观察，发现没有过滤的符号是getattr


### 题解

 * 可以观察到最后的操作getattr，找到这段内容获取的办法