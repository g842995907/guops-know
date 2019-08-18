#### pip下载

```shell
cd /tmp
curl -O https://bootstrap.pypa.io/get-pip.py
python get-pip.py
pip install  --upgrade pip
mkdir ~/.pip/

cat <<EOF >> ~/.pip/pip.conf
[global]
index-url = https://mirrors.aliyun.com/pypi/simple/
[install]
trusted-host=mirrors.aliyun.com
EOF
```

#### supervisor配置(有需要的话)

```shell
cd /tmp
echo_supervisord_conf > supervisord.conf

cat <<EOF >> supervisord.conf
[include]
files = /etc/supervisord.d/*.conf
EOF

mv supervisord.conf /etc/
mkdir /etc/supervisord.d/
# 启动supervisor
supervisord -c /etc/supervisord.conf
```

#### 虚拟环境

```shell
pip install virtualenv
pip install virtualenvwrapper
# 配置虚拟环境
cat <<"EOF" >> /etc/profile
export WORKON_HOME=$HOME/.virtualenvs
source /usr/bin/virtualenvwrapper.sh
EOF
# virtualenvwrapper 环境可能不在这个目录下
# which ...
source /etc/profile
```
