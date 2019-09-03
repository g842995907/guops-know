

### 概述

标靶是网络拓扑中的最小单位，可以是网络、虚拟路由、虚拟终端。
网络和虚拟路由不支持访问和自定义，虚拟终端标靶采用RDP(远程桌面)或SSH远程访问方式。

--- 
### <span id='target-property'>标靶属性</span>
- 元数据
	- [角色](#target-role)，标靶角色分为**路由**、**网络**和**终端**；
	- 系统，系统分为Linux、Windows、其他；
	- 大小，标靶运行时的CPU、内存和硬盘的配置；
	- 系统访问方式，支持SSH(默认22端口)和RDP(远程桌面，默认3389端口)两种登录方式，请确保系统相关服务开启并允许远程接入；
	- 系统用户信息，系统登录的初始用户名和密码；
- 高级属性
	- 是否支持[Cloud-init](http://cloudinit.readthedocs.io/en/latest/),提供了虚拟机启动后的初始化能力；
	- [磁盘控制器类型](#target-disk-control-type)
	- [虚拟网卡型号](#target-virtual-io)
	- [视频图像驱动](#target-image-video-driver)
- 镜像
	- 标靶实际对应的系统镜像文件；
- 状态
	- 待编辑，从已有系统新增镜像，只有元数据而未生成系统镜像的状态，该标靶不能直接使用，在场景中被自动过滤；
	- 已保存，元数据和镜像已就绪，可以正常使用；

---
###  <span id='target-remote-access'>标靶接入</span>
系统提供操作标靶的远程接入能力，Windows系统支持RDP协议，Linux系统支持SSH和RDP协议。

- Web直接访问，系统支持从web页面直接访问，系统自动输入用户名密码
- RDP 协议支持 远程桌面、Remmina等支持RDP的工具
- SSH 协议支持 Xshell、SecureCRT、Putty、Terminal等支持SSH的工具

---
### <span id='target-selfdefine'>自定义标靶</span>

- 从基础系统启动，系统提供基础镜像
	- winxp-32
	- win7-64
	- win2008-64
	- centos7-64
	- ubuntu14-64
- 自定义上传
	- [VMware虚拟机](upload-target/#upload-vmware)
	- [Virtualbox虚拟机](upload-target/#upload-virtualbox)
	- [KVM虚拟机](upload-target/#upload-kvm)
	- [虚拟机设置方法](upload-target/#upload-vm-setting)
- 文件拷贝

方式1：文件直接从Web页面拖入，拖入的文件，Windows系统在虚拟盘符Gucamole盘中，Linux在登录用户所在目录下；

方式2：使用远程桌面、Remmina、Xshell等工具请使用工具自带传输方式

- 保存镜像


---
### <span id='target-assert'>注意项</span>

- 由于网络是随机的，标靶需设置dhcp，不能配置静态IP；
- 支持Cloud-init的标靶在使用中调整到高配硬盘启动时会自动挂载硬盘，不支持Cloud-init的系统需手动挂载；
- 标靶现不支持多网卡；
- 保存镜像过程中镜像会无法访问，保存成功后恢复正常，可以继续编辑，重复保存，只保存最后一次状态；
- Windows系统上传的文件请从Gucamole盘中移走，否则会占用服务器空间；
- Linux系统上传文件需要靶机开启SSH服务(SSH用户名密码需要和RDP用户一致);




--- 
<strong size=4 id='target-role'>标靶角色</strong>

系统有**网络**,**路由**,**终端**三种角色

- 路由只能和网络进行连接；终端只能接在网络上；路由和终端无法直接连接
- DIY拓扑时，平台属性为网络，提供系统默认的openstack网络
- 目前只有终端角色支持自定义

--- 
<strong size=4 id='target-disk-control-type'>磁盘控制器类型</strong>

- ide
- virtio 
- scsi 
- uml
- xen
- usb

--- 
<strong size=4 id='target-virtual-io'>虚拟网卡型号</strong>

- rtl8139
- virtio
- e1000
- ne2k_pci
- pcnet

--- 
<strong size=4 id='target-image-video-driver'>视频图像驱动</strong>

- **vga**（Video Graphics Array）即视频图形阵列
- cirrus
- vmvga
- xenXEN  
- qxl

---
### <span id='target-cloudbase-init'>Cloudbase-init WinXP部署</span>

- 运行[官方安装包](attachment/CloudbaseInitSetup_0_9_11_x86.msi)
- 打开C:\Program Files\Cloudbase Solutions\Cloudbase-Init\Python\Lib\site-packages\serial\win32.py, 注释掉包含'CancelIOEx'的三行 
- 打开C:\Program Files\Cloudbase Solutions\Cloudbase-Init\conf\cloudbase-init.conf, 增加metadata_services和allow_reboot=false, 参考cloudbase-init-unattend.conf
- 删除服务：sc delete cloudbase-init
- 导入注册表文件[cloudbase-init.reg](attachment/cloudbase-init.reg)
- 制作镜像前，需要检查注册表HKLM/Software/Cloudbase Solutions/Cloudbase-Init/下面是否有子键，有就删掉，否则新虚拟机启动时Cloudbase-init认为已经执行过，不再执行。
- 制作镜像前，执行ipconfig /release释放虚拟机的IP地址。

---
### <span id='target-automount'>Linux自动挂载脚本部署</span>
- 复制[automount.sh](attachment/automount.sh)到/usr/sbin
- 添加执行权限：chmod +x /usr/sbin/automount.sh
- 设置开机启动：echo /usr/sbin/automount.sh >> /etc/rc.local
- 设置定时启动：echo '* * * * * root /usr/sbin/automount.sh' >> /etc/crontab
