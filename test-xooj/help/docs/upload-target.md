 

## <span id='upload-vmware'>VMware虚拟机</span>

- [Windows-XP](#upload-vmware-windowxp)
- [Windows-7 && Windows Server 2008](#upload-vmware-window7-and-2008)
- [kali](#upload-vmware-kali)
- [其他Linux](#upload-vmware-onter-linux)

--- 
<strong size=4 id='upload-vmware-windowxp'>Windows-XP</strong>

<font color=#FF3333 >**前置要求**</font>

- 安装系统虚拟磁盘存储方式为 ”单个文件”  
- 安装系统虚拟磁盘类型为IDE， 若为其他，如SATA，需要手动修改为IDE
- 修改MTU值为1450
- 执行[MergeIDE.bat](attachment/MergeIDE.zip)文件, 
- 关闭防火墙或放开防火墙3389端口
- 打开远程桌面，并确认是否允许无密码登录
- 若安装了cloudbase-init且启用了域控, 请删除cloudbase-init配置文件中修改主机名的插件cloudbaseinit.plugins.common.sethostname.SetHostNamePlugin.
- 释放IP配置

<font color=#FF3333 >**导入参数**</font>

- 磁盘控制器类型  **ide**      
- 虚拟网卡型号   **rtl8139**

---
<strong size=4 id='upload-vmware-window7-and-2008'>Windows-7 && Windows Server 2008</strong>

<font color=#FF3333 >**前置要求**</font>

- 安装系统虚拟磁盘存储方式为 ”单个文件”  
- 安装系统虚拟磁盘类型为IDE， 若为其他，如SATA，需要手动修改为IDE
- 修改MTU值为1450
- 关闭防火墙或放开防火墙3389端口
- 打开远程桌面，并确认是否允许无密码登录
- 若安装了cloudbase-init且启用了域控, 请删除cloudbase-init配置文件中修改主机名的插件cloudbaseinit.plugins.common.sethostname.SetHostNamePlugin.
- 释放IP配置

<font color=#FF3333 >**导入参数**</font>

- 磁盘控制器类型  **ide**      
- 虚拟网卡型号   **rtl8139**

---
<strong size=4 id='upload-vmware-kali'>kali</strong>

<font color=#ff0000 >**前置要求**</font>

- 安装系统虚拟磁盘存储方式为 ”单个文件”  
- 安装系统虚拟磁盘类型为IDE， 若为其他，如SATA，需要手动修改为IDE
- 关闭防火墙或放开防火墙3389端口
- 关闭防火墙或放开防火墙22端口
- 禁用网卡命名规则

<font color=#FF3333 >**导入参数**</font>

- 磁盘控制器类型  **ide**      
- 视频图像驱动   **vga**

---
<strong size=4 id='upload-vmware-onter-linux'>其他linux</strong>

<font color=#ff0000 >**前置要求**</font>

- 安装系统虚拟磁盘存储方式为 ”单个文件”  
- 安装系统虚拟磁盘类型为IDE， 若为其他，如SATA，需要手动修改为IDE
- 关闭防火墙或放开防火墙3389端口
- 关闭防火墙或放开防火墙22端口
- 禁用网卡命名规则

<font color=#FF3333 >**导入参数**</font>

- 磁盘控制器类型  **ide**  

--- 
## <span id='upload-virtualbox'>Virtualbox虚拟机</span>

- [Windows-XP](#upload-virtualbox-windowxp)
- [Windows-7 && Windows Server 2008](#upload-virtualbox-window7-and-2008)
- [kali](#upload-virtualbox-kali)
- [其他linux](#upload-virtualbox-other-linux)


<strong size=4 id='upload-virtualbox-windowxp'>Windows-XP</strong>

<font color=#FF3333 >**前置要求**</font>

- 安装系统虚拟磁盘类型为IDE， 若为其他，如SATA，需要手动修改为IDE
- 修改MTU值为1450
- 执行[MergeIDE.bat](attachment/MergeIDE.zip)文件, 
- 关闭防火墙或放开防火墙3389端口
- 打开远程桌面，并确认是否允许无密码登录
- 若安装了cloudbase-init且启用了域控, 请删除cloudbase-init配置文件中修改主机名的插件cloudbaseinit.plugins.common.sethostname.SetHostNamePlugin.
- 释放IP配置

<font color=#FF3333 >**导入参数**</font>

- 磁盘控制器类型  **ide**      
- 虚拟网卡型号   **rtl8139**

---
<strong size=4 id='upload-virtualbox-window7-and-2008'>Windows-7 && Windows Server 2008</strong>

<font color=#ff0000 >**前置要求**</font>

- 安装系统虚拟磁盘类型为IDE， 若为其他，如SATA，需要手动修改为IDE
- 修改MTU值为1450
- 关闭防火墙或放开防火墙3389端口
- 打开远程桌面，并确认是否允许无密码登录
- 若安装了cloudbase-init且启用了域控, 请删除cloudbase-init配置文件中修改主机名的插件cloudbaseinit.plugins.common.sethostname.SetHostNamePlugin.
- 释放IP配置

<font color=#FF3333 >**导入参数**</font>

- 磁盘控制器类型  **ide**      
- 虚拟网卡型号   **rtl8139**

---
<strong size=4 id='upload-virtualbox-kali'>kali</strong>

<font color=#FF3333 >**前置要求**</font>

- 安装系统虚拟磁盘类型为IDE， 若为其他，如SATA，需要手动修改为IDE
- 关闭防火墙或放开防火墙3389端口
- 关闭防火墙或放开防火墙22端口
- 禁用网卡命名规则

<font color=#FF3333 >**导入参数**</font>

- 磁盘控制器类型  **ide**      
- 视频图像驱动   **vga**      

---
<strong size=4 id='upload-virtualbox-other-linux'>其他Linux</strong>

<font color=#FF3333 >**前置要求**</font>

- 安装系统虚拟磁盘类型为IDE， 若为其他，如SATA，需要手动修改为IDE
- 关闭防火墙或放开防火墙3389端口
- 关闭防火墙或放开防火墙22端口
- 禁用网卡命名规则

<font color=#FF3333 >**导入参数**</font>

- 磁盘控制器类型  **ide**     

---
## <span id='upload-kvm'>KVM虚拟机</span>
- [Windows-XP](#upload-kvm-windowxp)
- [Windows-7 && Windows Server 2008](#upload-kvm-window7-and-2008)
- [kali](#upload-kvm-kali)
- [其他Linux](#upload-kvm-other-linux)

<strong size=4 id='upload-kvm-windowxp'>Windows-XP</strong>

<font color=#FF3333 >**前置要求**</font>

- 安装系统需要手动指定虚拟硬盘、网卡模式为virtio，并加载virtio驱动文件
- 修改MTU值为1450
- 关闭防火墙或放开防火墙3389端口
- 打开远程桌面，并确认是否允许无密码登录
- 若安装了cloudbase-init且启用了域控, 请删除cloudbase-init配置文件中修改主机名的插件cloudbaseinit.plugins.common.sethostname.SetHostNamePlugin.
- 释放IP配置

---
<strong size=4 id='upload-kvm-window7-and-2008'>Windows-7 && Windows Server 2008</strong>

<font color=#FF3333 >**前置要求**</font>

- 安装系统需要手动指定虚拟硬盘、网卡模式为virtio，并加载virtio驱动文件
- 修改MTU值为1450
- 关闭防火墙或放开防火墙3389端口
- 打开远程桌面，并确认是否允许无密码登录
- 若安装了cloudbase-init且启用了域控, 请删除cloudbase-init配置文件中修改主机名的插件cloudbaseinit.plugins.common.sethostname.SetHostNamePlugin.
- 释放IP配置

---
<strong size=4 id='upload-kvm-kali'>kali</strong>

<font color=#FF3333 >**前置要求**</font>

- 安装系统需要手动指定虚拟硬盘、网卡模式为virtio，并加载virtio驱动文件
- 关闭防火墙或放开防火墙3389端口
- 关闭防火墙或放开防火墙22端口
- 禁用网卡命名规则

<font color=#FF3333 >**导入参数**</font>

- 磁盘控制器类型  **ide**      
- 视频图像驱动   **vga**           

---
<strong size=4 id='upload-kvm-other-linux'>其他Linux</strong>

<font color=#FF3333 >**前置要求**</font>

- 安装系统需要手动指定虚拟硬盘、网卡模式为virtio，并加载virtio驱动文件
- 关闭防火墙或放开防火墙3389端口
- 关闭防火墙或放开防火墙22端口
- 禁用网卡命名规则

<font color=#FF3333 >**导入参数**</font>

无         


--- 
### <span id='upload-vm-setting'>虚拟机设置方法</span>
- [VMware 单个文件磁盘存储](#vm-setting-vmware-signal-disk)
- [VMware 设置虚拟磁盘控制器类型](#vm-setting-disk-control-vmware)
- [ViturlBox设置虚拟磁盘控制器类型](#vm-setting-disk-control-viturlbox)
- [Windows-XP 设置MTU](#vm-setting-winxp-mtu)
- [Windows-7 设置MTU](#vm-setting-win7-mtu)
- [Windows配置用户自动登陆](#vm-setting-windows-auto-login)
- [Windows-Server-2008 设置MTU](#vm-setting-winserver-2008-mtu)
- [Windows 释放IP配置](#vm-setting-winows-ip-release)
- [Windows 关闭防火墙](#vm-setting-windows-shutdown-firewall)
- [Windows-XP 远程桌面](#vm-setting-windowxp-remote)
- [Windows-7 远程桌面](#vm-setting-window7-remote)
- [Windows-Server-2008 远程桌面](#vm-setting-windows-server-2008-remote)
- [Windows安装qemu-guest-agent插件](#vm-setting-windows-qemu-guest-agent)
- [Windows server 2008/2012 解除密码复杂度限制](#vm-setting-windowserver2008-and-2012-password-complex)
- [验证qemu-guest-agent是否安装成功](#vm-setting-yanzheng-qemu-guest-agent)
- [Linux配置开放端口](#vm-setting-linux-open-port)
- [Windows配置开放端口](#vm-setting-windows-open-port)
- [Windows允许无密码远程登录](#vm-setting-windows-allow-empty-password)
- [Windows XP加载virtio驱动](#vm-setting-windowxp-virtio)
- [Windows 7/2008/2012 加载virtio驱动](#vm-setting-window7-and-2008-virtio)
- [Windows xp/2003安装cloudbase-init](#vm-setting-windowsXP-and-2003-cloudbase-init)
- [Linux安装qemu-guest-agent插件](#vm-setting-linux-qemu-guest-agent)
- [Linux允许root远程登录](#vm-setting-linux-allow-empty-password-and-root)
- [Linux允许无密码登录](#vm-setting-linux-allow-empty-password-and-root)
- [Linux禁用网卡命名规则](#vm-setting-linux-no-rename-nic)
- [多网卡默认网关冲突问题](#vm-setting-multi-nics)

<strong size=4 id='vm-setting-vmware-signal-disk'>VMware 单个文件磁盘存储 </strong>

安装系统虚拟磁盘存储方式为 ”单个文件” 

![](img/1.png) 

如当前为多文件转换方法(转换前需要删除虚拟机快照)

```
vmware-vdiskmanager.exe -r 需要转换的源文件.vmdk -t 0 需要转换的目标文件.vmdk
```

---
<strong size=4 id='vm-setting-disk-control-vmware'>VMware设置虚拟磁盘控制器类型</strong>

![](img/2.png) 

---
<strong size=4 id='vm-setting-disk-control-viturlbox'>ViturlBox设置虚拟磁盘控制器类型</strong>

![](img/3.png) 

![](img/4.png) 

---
<strong size=4 id='vm-setting-winxp-mtu'>Windows-XP 设置MTU</strong>
方法1在部分虚拟机中找不到该项配置

- 方法1

![](img/5.png)

![](img/6.png) 

- 方法2
 
	1. 按Win+R组合键，调出“运行”菜单，输入regedit，然后回车； 
	2. 选择“HKEY_Local_Machine>SYSTEM>CurrentControlSet>Services>Tcpip>Parameters>interface”；
	3. 在 interface 中下可能有很多项，需要逐个观察键值，会有一个项与你的网卡IP一致，选中该项；
	4. 然后在该项上点击右键，选择“编辑>新建>DWORD值”，然后在右侧将其命名为“MTU”；
	5. 右键点击MTU，选择“修改”，在弹出的窗口中选择“十进制”，填入你得出的合理MTU值即可。

---
<strong size=4 id='vm-setting-win7-mtu'>Windows-7 设置MTU</strong>

1. 进入系统盘:\Windows\System32\找到cmd.exe，右键“以管理员身份运行”；
2. 在出现的“命令提示符”窗口中输入“netsh interface ipv4 show subinterfaces”并回车来查看当前的MTU值
3. 接下来输入“netsh interface ipv4 set subinterface "需修改的连接名" mtu=你得出的合理值 store=persistent”并回车即可
例如：“netsh interface ipv4 set subinterface "本地连接" mtu=1450 store=persistent”

![](img/11.png) 

---
<strong size=4 id='vm-setting-windows-auto-login'>Windows配置用户自动登陆</strong>

*   命令行执行 control userpasswords2

![](img/auto_login.png)

*   取消勾选，点击右下角的应用，弹出框，设置要自动登陆的用户设置密码

![](img/set_autologinuser_password.png)

*   重启系统，查看用户是否自动登陆

* * *


<strong size=4 id='vm-setting-winserver-2008-mtu'>Windows-Server-2008 设置MTU</strong>

1. 进入系统盘:\Windows\System32\找到cmd.exe，右键“以管理员身份运行”；
2. 在出现的“命令提示符”窗口中输入“netsh interface ipv4 show subinterfaces”并回车来查看当前的MTU值
3. 接下来输入“netsh interface ipv4 set subinterface "需修改的连接名" mtu=你得出的合理值 store=persistent”并回车即可
例如：“netsh interface ipv4 set subinterface "本地连接" mtu=1450 store=persistent”

![](img/11.png) 

---
<strong size=4 id='vm-setting-winows-ip-release'>Windows 释放IP配置</strong>

1. 运行cmd
2. 执行命令 “ipconfig /release”

---
<strong size=4 id='vm-setting-windows-shutdown-firewall'>Windows 关闭防火墙</strong>

![](img/7.png) 

---
<strong size=4 id='vm-setting-windowxp-remote'>Windows-XP 远程桌面</strong>

![](img/8.png)

---
<strong size=4 id='vm-setting-window7-remote'>Windows-7 远程桌面</strong>

![](img/10.png)

- 允许任意版本请选择 **RDP** 模式
- 网络级别身份认证请选择 **NLA** 模式

---
<strong size=4 id='vm-setting-windows-server-2008-remote'>Windows-Server-2008 远程桌面</strong>

![](img/10.png)

- 允许任意版本请选择 **RDP** 模式
- 网络级别身份认证请选择 **NLA** 模式

---
<strong size=4 id='vm-setting-windows-qemu-guest-agent'>Windows安装qemu-guest-agent插件</strong>


*   搜素文件系统中是否有virtio-win文件夹(如果没有则[下载virtio-win](https://fedorapeople.org/groups/virt/virtio-win/direct-downloads/archive-virtio/virtio-win-0.1.141-1/virtio-win-0.1.141.iso),更多virtio版本[请查看](https://docs.fedoraproject.org/quick-docs/en-US/creating-windows-virtual-machines-using-virtio-drivers.html) )
*   找到virtio-win可以看到下图

![](img/virtio_install_01.jpeg)

*   先更新 virto-serail driver 更新 pci 简单通讯控制器 (使用 vioserail 目录中的驱动)

![](img/virtio_viserial.jpeg)

*   安装virto-serail driver (**注意选择与系统版本对应的驱动** )

![](img/virtio_serial_install_01.jpeg)

![](img/virtio_serial_install_02.jpeg)

*   安装balloon pci 驱动 (**注意选择与系统版本对应的驱动** )

![](img/virtio_balloon_01.jpeg)

![](img/virtio_balloon_02.jpeg)

*   安装guest-agent 驱动 (**注意选择与系统版本对应的驱动** )
根据系统版本(x64,x86) 双击virtio-win目录下的 guest-agent 目录下的 qemu-ga-x86.msi 或 qemu-ga-x64.msi进行安装 执行完毕之后，命令行执行services.msc查看相关服务状态,启动qemu-guest-agent VSS provider服务，并改为自启动

![](img/virtio_guest_agent_01.jpeg)

**此时会发现，qemu-guest-agent服务没有启动，手动启动也会报错 1053：服务没有及时响应启动或控制请求。这个不用管，等到镜像做好之后给镜像加上metadata ,hw\_qemu\_guest_agent 为yes之后服务会正常自启动**

![](img/glance_metadata.png)
***

<strong size=4 id='vm-setting-windowserver2008-and-2012-password-complex'>Windows server 2008/2012 解除密码复杂度限制</strong>

 *  gpedit 打开本地组策略编辑器
 *  选择计算机设置---windows 设置---安全设置---帐号策略---密码策略
 *  第一个密码复杂度策略，将密码复杂度要求改为禁用
* * *

 <strong size=4 id='vm-setting-yanzheng-qemu-guest-agent'>验证qemu-guest-agent是否安装成功</strong>


在openstack 上启动镜像实例，找到实例对应的domain

方法1:*   执行 virsh qemu-agent-command domain '{"execute":"guest-ping"}',如果返回{"return":{}}则说明服务正常

方法2:*   执行 virsh set-user-password --domain domain--user user --password password ,如果返回“Password set successfully ”则说明插件安装正常

![](img/qemu_guest_agent_yanzheng.png)

* * *

---
<strong size=4 id='vm-setting-linux-open-port'>Linux配置开放端口</strong>

**Iptables**

```
vi/etc/sysconfig/iptables

-A INPUT -m state --state NEW -m tcp -p tcp--dport 3389 -j ACCEPT

```
Firewall
```
firewall-cmd --zone=public --add-port=3389 /tcp --permanent 
```

---
<strong size=4 id='vm-setting-windows-open-port'>Windows配置开放端口</strong>

1. 打开防火墙高级设置

![](img/12.png)

2. 新建入站规则

![](img/13.png)

3. 选择端口

![](img/14.png)

4. 设置端口

![](img/15.png)

---
<strong size=4 id='vm-setting-windows-allow-empty-password'>Windows允许无密码远程登录</strong>

配置Windows组策略

![](img/9.png)

---
<strong size=4 id='vm-setting-windowxp-virtio'>Windows XP加载virtio驱动</strong>

1. 安装时指定硬盘、网卡模式为virtio，并加载virtio驱动文件
2. 系统启动时，点击F6加载第三方驱动

![](img/16.png)

![](img/17.png)

3. 选择对应版本的驱动程序（WinXP），点击“ENTER”之后继续安装系统

![](img/18.png)


---
<strong size=4 id='vm-setting-window7-and-2008-virtio'>Windows 7/2008/2012 加载virtio驱动</strong>

1. 安装时指定硬盘、网卡模式为virtio，并加载virtio驱动文件
2. 安装过程中在选择硬盘驱动器时点击“加载驱动程序”

![](img/19.png)

3. 点击“确定”后选择系统对应的驱动程序，“下一步”之后即可看到一块未分配的硬盘

![](img/20.png)

![](img/21.png)

---
 <strong size=4 id='vm-setting-windowsXP-and-2003-cloudbase-init'>Windows xp/2003安装cloudbase-init</strong>
 
 Windows XP 和Windows server 2003默认不支持cloudbase-init,在安装时需要更改一些设置
 
*   编辑C:\Program Files\Cloudbase Solutions\Cloudbase-Init\Python\Lib\site-packages\serial\win32.py ，注释掉包含’CancelIOEx’的三行。
  
*   删除cloudbase-init服务   sc delete cloudbase-init
 
*   导入注册表文件（或者手动添加），内容为：
Windows Registry Editor Version 5.00

[HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\Run]
"Cloudbase-init"="\"C:\\Program Files\\Cloudbase Solutions\\Cloudbase-Init\\Python\\Scripts\\cloudbase-init.exe\" --config-file \"C:\\Program Files\\Cloudbase Solutions\\Cloudbase-Init\\conf\\cloudbase-init.conf\""


---

<strong size=4 id='vm-setting-linux-qemu-guest-agent'>Linux安装qemu-guest-agent插件</strong>



 ** kali和ubuntu上 **

1.  执行命令 sudo apt-get install qemu-guest-agent安装插件
2.  systemctl enable qemu-guest-agent设置插件自启动
3.  systemctl start qemu-guest-agent 启动服务

**   centos上  **

1.  执行命令 yum install -y qemu-guest-agent安装插件
2.  systemctl enable qemu-guest-agent设置插件自启动
3.  systemctl start qemu-guest-agent 启动服务



* * *


<strong size=4 id='vm-setting-linux-allow-empty-password-and-root'>Linux允许root/无密码远程登录</strong>

配置/etc/ssh/sshd_config 文件配置项
```
PermitEmptyPasswords no 
PasswordAuthentication yes
PermitRootLogin no

```
* * *

<strong size=4 id='vm-setting-linux-no-rename-nic'>Linux禁用网卡命名规则</strong>

编辑/etc/default/grub文件，在GRUB_CMDLINE_LINUX配置项中添加“net.ifnames=0  biosdevname=0”,执行update-grub. 如果不存在update-grub命令(如CentOS7), 就执行以下命令:
```
cp /boot/grub2/grub.cfg /boot/grub2/grub.cfg.$(date +%s)
grub2-mkconfig -o /boot/grub2/grub.cfg
```
重启系统, 应当能看到网卡名字为eth0, 然后为网卡eth0编辑配置文件,并设置从dhcp获取地址.

* * *

<strong size=4 id='vm-setting-multi-nics'>多网卡默认网关冲突问题</strong>

当虚拟机存在多块网卡时, 为了确保默认网关的唯一性, 建议只给其中一块网卡配置网关, 而其它网卡不配置网关. 此时不使用DHCP而只能配置静态地址.




