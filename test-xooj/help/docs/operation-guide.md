### <span id='operation-guide'>虚拟机操作指南</span>

#### <span id='operation-caps'>大小写及输入法切换</span>

**Windows**:

使用capslock切换大小写,Windows7使用Ctrl+Shift切换中英文输入,Windows10使用Shift切换中英文输入

**Kali&Ubuntu（未安装输入法，以下切换大小写方法任选其一）**:

- 先按shift，再按capslock
- 长按capslock至少三秒
- 先按capslock，然后刷新当前远程页面
- 使用shift+字母键输入大写字母
- 在客户端系统的其他输入焦点按capslock，再回到远程页面输入焦点

------


#### <span id='operation-cv'>复制粘贴</span>

- 按住Ctrl+Shitf+Alt打开文本框
- 粘贴文本(Ctrl+c)到弹出的文本框，再次使用Ctrl+Shitf+Alt关闭弹出框
- 在虚拟机中使用Ctrl+v进行文本粘贴(SSH方式使用右键粘贴)

------

#### <span id='operation-upfile'>文件上传</span>

**方式1**：文件直接从Web页面拖入，拖入的文件，Windows系统在虚拟盘符Gucamole(G)盘中，Linux在登录用户所在目录下；如root用户(/root)

**方式2**：使用远程桌面、Remmina、Xshell等工具请使用工具自带传输方式；

**注意项**：

- windows上传文件，<font color=#FF3333>最大限制2G，超过2G的文件请分段上传</font>，然后合并。linux无限制

------

####  <span id='operation-downloadfile'>文件下载</span>

##### Windows:

将文件移动到虚拟盘符Gucamole盘中Download文件夹中(G:Download)，浏览器自动下载(如有弹出提示，请点击允许)

##### Linux:

使用远程桌面、Remmina、Xshell等工具请使用工具自带传输方式或SSH传输；

**注意项**：

- Windows系统上传的文件请从Gucamole盘中移走，否则会占用服务器空间；
- Linux系统上传文件需要靶机开启SSH服务(SSH用户名密码需要和RDP用户一致)；