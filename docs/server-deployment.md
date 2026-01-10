# SafeGuard 后端服务部署指南

本文档提供 SafeGuard 后端服务在 Ubuntu 服务器上的完整部署指南。

## ⚠️ 重要提示

### 权限策略说明

本部署指南采用**混合权限策略**：

1. **系统级操作**（需要 root 权限）：
   - 安装系统软件（Python 3.12、Nginx、Certbot）
   - 配置 Systemd 服务
   - 配置 Nginx
   - 申请 SSL 证书（绑定 80/443 端口）

2. **应用级操作**（使用普通用户）：
   - 创建和管理虚拟环境
   - 安装 Python 依赖包
   - 运行应用服务
   - 管理应用数据

### 用户和组配置

在开始部署前，需要配置专用用户和组：

```bash
# 1. 创建专用用户组（如果不存在）
sudo groupadd safeguard-group

# 2. 将当前用户添加到该组（假设当前用户是 ubuntu）
sudo usermod -aG safeguard-group ubuntu

# 3. 刷新组权限（需要重新登录或执行以下命令）
newgrp safeguard-group

# 4. 验证组配置
groups
# 应该能看到 safeguard-group 在列表中
```

**重要**：完成上述配置后，建议重新登录以使组权限完全生效。

## 部署目标

- **主域名**: `leadingagile.cn`
- **静态网站**: `www.leadingagile.cn` (HTTPS)
- **后台服务**: `safeguard.leadingagile.cn` (HTTPS)

## 服务器要求

- **操作系统**: Ubuntu 20.04+
- **内存**: 至少 2GB
- **磁盘**: 至少 20GB
- **Python**: 3.12
- **公网 IP**: 可访问
- **端口**: 开放 80、443 端口
- **权限**: **需要 root 权限**（用于安装系统软件、配置服务、绑定端口）

## 部署步骤

### 阶段零：前置检查

在开始部署前，请执行以下检查，确保系统环境满足要求：

```bash
# 1. 检查操作系统版本
lsb_release -a
# 应该显示 Ubuntu 20.04 或更高版本

# 2. 检查可用内存
free -h
# 至少需要 2GB 可用内存

# 3. 检查磁盘空间
df -h
# 至少需要 20GB 可用磁盘空间

# 4. 检查当前用户
whoami
# 记录用户名，后续配置会用到

# 5. 检查当前用户所属的组
groups
# 记录组信息

# 6. 检查 Python 版本
python3 --version
# 如果不是 3.12，需要安装

# 7. 检查 SQLite3 命令行工具
sqlite3 --version
# 如果报错，需要安装

# 8. 检查是否已安装必要的系统工具
which git wget curl
# 如果缺少，需要安装：sudo apt install -y git wget curl

# 9. 检查端口占用
sudo netstat -tlnp | grep -E ':(80|443|9999)\s'
# 如果端口被占用，需要停止相关服务或选择其他端口
```

**如果任何检查失败，请先解决相关问题，然后再继续部署。**

### 阶段一：安装 Python 3.12

如果系统没有 Python 3.12，需要从源码编译安装。

**重要**：必须按照以下顺序执行，确保 SQLite 支持正确安装：

```bash
# 1. 更新软件包列表
sudo apt update

# 2. 安装 SQLite3 命令行工具（系统级）
sudo apt install -y sqlite3

# 3. 验证 SQLite3 命令行工具
sqlite3 --version
# 应该输出类似：SQLite 3.x.x

# 4. 安装编译依赖（包含 SQLite 开发库和 pkg-config）
sudo apt install -y build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev wget libsqlite3-dev pkg-config

# 5. 验证 SQLite 开发库已安装
dpkg -l | grep libsqlite3-dev
# 应该显示：ii  libsqlite3-dev  ...

# 6. 下载 Python 3.12.0
cd /tmp
wget https://www.python.org/ftp/python/3.12.0/Python-3.12.0.tgz

# 7. 解压
tar -xzf Python-3.12.0.tgz
cd Python-3.12.0

# 8. 配置编译选项（启用优化和 SQLite 支持）
./configure --enable-optimizations --enable-loadable-sqlite-extensions

# 9. 编译（使用所有 CPU 核心加速，需要 10-20 分钟）
make -j$(nproc)

# 10. 安装
sudo make altinstall

# 11. 验证 Python 3.12 安装
python3.12 --version
# 应该输出：Python 3.12.0

# 12. 配置为默认 Python 版本
sudo update-alternatives --install /usr/bin/python3 python3 /usr/local/bin/python3.12 2
sudo update-alternatives --config python3
# 在提示时选择 Python 3.12 对应的编号

# 13. 验证默认 Python 版本
python3 --version
# 应该输出：Python 3.12.0

# 14. 安装 pip
python3 -m ensurepip --upgrade
python3 -m pip --version

# 15. 验证 SQLite 支持（关键步骤！）
python3.12 -c "import sqlite3; print('SQLite version:', sqlite3.sqlite_version)"
# 应该输出：SQLite version: 3.x.x

# 16. 如果步骤 15 报错 "ModuleNotFoundError: No module named '_sqlite3'"
# 说明编译时没有包含 SQLite 支持，需要重新编译：
#    a. 确保已安装 libsqlite3-dev：sudo apt install -y libsqlite3-dev
#    b. 清理编译文件：make clean
#    c. 重新配置：./configure --enable-optimizations --enable-loadable-sqlite-extensions
#    d. 重新编译：make -j$(nproc)
#    e. 重新安装：sudo make altinstall
#    f. 重新验证：python3.12 -c "import sqlite3; print('SQLite version:', sqlite3.sqlite_version)"
```

### 阶段二：上传后端代码

**注意**：此阶段需要 root 权限，因为要安装到 `/opt` 系统目录。

```bash
# 1. 在本地打包（在项目根目录执行）
cd /path/to/safeGuard
tar -czf backend.tar.gz backend/

# 2. 上传到服务器（使用 root 用户）
scp backend.tar.gz root@your-server-ip:/opt/

# 3. SSH 登录服务器（使用 root 用户）
ssh root@your-server-ip

# 4. 解压到 /opt 目录（需要 root 权限）
cd /opt
tar -xzf backend.tar.gz
cd /opt/safeguard/backend

# ⚠️ 警告：此时所有文件都是 root 权限！必须执行下面的权限配置步骤！
```

或者使用 Git（推荐）：

```bash
# 在服务器上
cd /opt
git clone <your-repo-url> safeguard
cd /opt/safeguard/backend

# ⚠️ 警告：如果以 root 用户执行 git clone，文件也是 root 权限！必须执行下面的权限配置步骤！
```

**⚠️ 重要：必须执行以下权限配置步骤！**

由于 `/opt` 目录需要 root 权限，所以解压或克隆后的文件都是 root 权限。必须立即修复权限，否则后续操作会失败。

```bash
# 5. 配置目录权限（使用普通用户作为 owner，专用组作为 group）
# 假设当前用户是 ubuntu，组是 safeguard-group
# 注意：这里必须包含 /opt/safeguard 目录，否则无法访问
sudo chown -R ubuntu:safeguard-group /opt/safeguard

# 6. 设置目录权限
# /opt/safeguard 目录：750 (owner: rwx, group: r-x, others: ---)
sudo chmod 750 /opt/safeguard

# /opt/safeguard/backend 目录：750 (owner: rwx, group: r-x, others: ---)
sudo chmod -R 750 /opt/safeguard/backend

# 7. 设置虚拟环境目录权限（770 = owner: rwx, group: rwx, others: ---）
# 注意：虚拟环境目录还未创建，此步骤在创建虚拟环境后需要再次执行
sudo chmod -R 770 /opt/safeguard/backend/venv_py312

# 8. 验证权限配置
ls -la /opt/safeguard
# 应该显示类似：drwxr-x--- ubuntu safeguard-group
# 如果显示 root:root，说明权限配置失败，请重新执行步骤 5

ls -la /opt/safeguard/backend
# 应该显示类似：drwxr-x--- ubuntu safeguard-group
# 如果显示 root:root，说明权限配置失败，请重新执行步骤 5

# 9. 切换到普通用户（如果当前是 root）
su - ubuntu
cd /opt/safeguard/backend

# 10. 验证普通用户可以访问
pwd
# 应该显示：/opt/safeguard/backend
```

### 阶段三：创建虚拟环境并安装依赖

**注意**：此阶段使用普通用户操作，但需要确保目录权限正确。

```bash
# 1. 检查当前用户和组
whoami
groups
# 应该能看到 safeguard-group 在列表中

# 2. 检查当前 shell
echo $SHELL
# 如果不是 bash，切换到 bash
bash

# 3. 进入项目目录
cd /opt/safeguard/backend

# 4. 检查目录权限
ls -la
# 应该显示：drwxr-x--- ubuntu safeguard-group

# 5. 创建虚拟环境
python3 -m venv venv_py312

# 6. 配置虚拟环境权限（确保组有写权限）
sudo chown -R ubuntu:safeguard-group venv_py312
sudo chmod -R 770 venv_py312

# 7. 激活虚拟环境
source venv_py312/bin/activate

# 8. 验证虚拟环境
which python
which pip
# 应该指向 venv_py312 目录

# 9. 升级 pip
pip install --upgrade pip

# 10. 安装依赖
pip install -r requirements.txt
pip install -r requirements-test.txt
```

### 阶段四：配置环境变量

```bash
# 1. 编辑生产环境配置
cd /opt/safeguard/backend/src
vim .env.prod
```

配置内容：

```bash
ENV_TYPE=prod
DEBUG=false

# 微信小程序配置
WX_APPID=your_wx_appid
WX_SECRET=your_wx_secret
TOKEN_SECRET=your_token_secret

# Redis 配置（如果需要）
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password
REDIS_DB=0

# SMS 配置
SMS_PROVIDER=mock
SMS_API_KEY=your_production_sms_api_key
SMS_API_SECRET=your_production_sms_api_secret
SMS_API_URL=https://api.sms-service.com/send
```

### 阶段五：创建 Systemd 服务

**注意**：此阶段需要 root 权限，因为要创建和配置系统服务。

```bash
# 1. 创建服务文件（需要 root 权限）
sudo vim /etc/systemd/system/safeguard.service
```

服务文件内容：

```ini
[Unit]
Description=SafeGuard Backend Service
After=network.target

[Service]
Type=simple
User=ubuntu
Group=safeguard-group
WorkingDirectory=/opt/safeguard/backend/src
Environment="PATH=/opt/safeguard/backend/venv_py312/bin"
Environment="ENV_TYPE=prod"
Environment="EXPOSE_PORT=9999"
ExecStart=/opt/safeguard/backend/venv_py312/bin/python /opt/safeguard/backend/src/run.py 0.0.0.0 9999
Restart=always
RestartSec=10

# 安全设置
NoNewPrivileges=true
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

**重要配置说明**：
- `User=ubuntu`：使用普通用户运行服务（不要使用 root）
- `Group=safeguard-group`：使用专用组
- `WorkingDirectory=/opt/safeguard/backend/src`：**关键！必须设置为 src 目录**，因为 alembic.ini 和其他配置文件都在 src 目录下
- `NoNewPrivileges=true`：防止进程获取额外权限
- `PrivateTmp=true`：使用独立的临时目录

**注意**：如果 WorkingDirectory 设置错误（如设置为 `/opt/safeguard/backend`），服务启动时会找不到 `alembic.ini` 文件，导致启动失败。

```bash
# 2. 启动服务前，确保所有文件权限正确
sudo chown -R ubuntu:safeguard-group /opt/safeguard/backend
sudo chmod -R 750 /opt/safeguard/backend
sudo chmod -R 770 /opt/safeguard/backend/venv_py312

# 3. 验证关键目录权限
ls -la /opt/safeguard/backend/src
ls -la /opt/safeguard/backend/src/data
ls -la /opt/safeguard/backend/logs

# 4. 重新加载 systemd 配置
sudo systemctl daemon-reload

# 5. 启动服务
sudo systemctl enable safeguard
sudo systemctl start safeguard

# 6. 查看服务状态
sudo systemctl status safeguard

# 7. 如果启动失败，查看详细日志
sudo journalctl -u safeguard -n 50 --no-pager
```

### 阶段六：安装和配置 Nginx

**注意**：此阶段需要 root 权限，因为要安装和配置 Web 服务器。

```bash
# 1. 安装 Nginx（需要 root 权限）
sudo apt update
sudo apt install -y nginx

# 2. 创建 Nginx 配置文件（需要 root 权限）
sudo vim /etc/nginx/sites-available/safeguard-backend.conf
```

Nginx 配置内容：

```nginx
# HTTP 重定向到 HTTPS
server {
    listen 80;
    server_name safeguard.leadingagile.cn;
    return 301 https://$server_name$request_uri;
}

# HTTPS 配置
server {
    listen 443 ssl http2;
    server_name safeguard.leadingagile.cn;
    
    # SSL 证书（需要申请）
    ssl_certificate /etc/letsencrypt/live/safeguard.leadingagile.cn/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/safeguard.leadingagile.cn/privkey.pem;
    
    # SSL 安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # 客户端请求体大小限制
    client_max_body_size 10M;
    
    location / {
        proxy_pass http://127.0.0.1:9999;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 超时设置
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # WebSocket 支持
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

```bash
# 3. 启用配置
sudo ln -s /etc/nginx/sites-available/safeguard-backend.conf /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 阶段七：申请 SSL 证书

**注意**：此阶段需要 root 权限，因为要绑定 80/443 端口并配置系统级证书。

```bash
# 1. 安装 Certbot（需要 root 权限）
sudo apt install -y certbot

# 2. 停止 Nginx（使用 standalone 模式，需要 root 权限）
sudo systemctl stop nginx

# 3. 申请证书（需要 root 权限）
sudo certbot certonly --standalone -d safeguard.leadingagile.cn

# 4. 重启 Nginx（需要 root 权限）
sudo systemctl start nginx

# 5. 设置证书自动续期（需要 root 权限）
sudo crontab -e
# 添加以下行（每天凌晨2点检查续期）
0 2 * * * certbot renew --quiet --post-hook "systemctl reload nginx"
```

### 阶段八：配置 DNS

在您的域名管理后台添加 A 记录：

- `safeguard.leadingagile.cn` → `175.27.228.78`（您的服务器 IP）

等待 DNS 生效（通常 10-30 分钟）。

### 阶段九：验证部署

```bash
# 1. 检查服务状态
sudo systemctl status safeguard

# 2. 查看服务日志
sudo journalctl -u safeguard -f

# 3. 测试本地访问
curl http://127.0.0.1:9999/api/env

# 4. 测试域名访问
curl https://safeguard.leadingagile.cn/api/env

# 5. 在浏览器访问
https://safeguard.leadingagile.cn
```

## 常用运维命令

### 服务管理

```bash
sudo systemctl start safeguard          # 启动服务
sudo systemctl stop safeguard           # 停止服务
sudo systemctl restart safeguard        # 重启服务
sudo systemctl status safeguard         # 查看状态
sudo systemctl enable safeguard         # 开机自启
```

### 日志查看

```bash
sudo journalctl -u safeguard -f         # 实时查看日志
sudo journalctl -u safeguard -n 100     # 查看最近100行日志
sudo journalctl -u safeguard --since today  # 查看今天的日志
```

### Nginx 管理

```bash
sudo nginx -t                            # 测试配置
sudo systemctl reload nginx             # 重载配置
sudo systemctl restart nginx            # 重启服务
sudo systemctl status nginx             # 查看状态
```

### 证书管理

```bash
sudo certbot renew --dry-run            # 测试续期
sudo certbot renew                      # 执行续期
sudo certbot certificates               # 查看证书信息
```

### 手动运行服务（调试用）

```bash
# 如果当前 shell 是 sh，先切换到 bash
bash

cd /opt/safeguard/backend
source venv_py312/bin/activate
cd src
python3 run.py 0.0.0.0 9999
```

## 故障排查

### 服务无法启动

如果服务启动失败，按照以下步骤排查：

```bash
# 1. 查看详细的服务日志
sudo journalctl -u safeguard -n 50 --no-pager

# 2. 检查服务状态
sudo systemctl status safeguard

# 3. 检查端口占用
sudo netstat -tlnp | grep 9999
# 如果端口被占用，停止占用进程或修改配置文件中的端口

# 4. 检查虚拟环境权限
ls -la /opt/safeguard/backend/venv_py312/bin/python
ls -la /opt/safeguard/backend/venv_py312/bin/pip
# 如果显示 root:root，需要修复权限

# 5. 修复权限（如果需要）
sudo chown -R ubuntu:safeguard-group /opt/safeguard/backend/venv_py312
sudo chmod -R 770 /opt/safeguard/backend/venv_py312

# 6. 手动运行测试（查看具体错误信息）
# 切换到普通用户
su - ubuntu
cd /opt/safeguard/backend

# 激活虚拟环境
source venv_py312/bin/activate

# 进入 src 目录
cd src

# 设置环境变量（重要！）
export ENV_TYPE=prod

# 手动运行应用（可以看到详细的错误输出）
python3 run.py 0.0.0.0 9999

# 如果手动运行成功，说明应用本身没问题，可能是 Systemd 配置问题
# 如果手动运行失败，会显示具体的错误信息，根据错误信息进行修复

# 注意：如果日志显示 "检测到 unit 环境（内存数据库）"，说明 ENV_TYPE 没有正确设置
# 必须设置 ENV_TYPE=prod 才能使用生产环境的数据库
```

**常见错误及解决方案**：

- **权限错误**：执行权限修复步骤（步骤 5）
- **端口占用**：停止占用进程或修改端口
- **环境变量未设置**：检查 `.env.prod` 文件配置
- **依赖缺失**：重新安装依赖 `pip install -r requirements.txt`
- **SQLite 支持问题**：参考"SQLite 支持问题"章节
- **找不到 alembic.ini 文件**：检查 Systemd 服务的 WorkingDirectory 是否正确设置为 `/opt/safeguard/backend/src`，而不是 `/opt/safeguard/backend`

### Nginx 配置问题

```bash
# 测试配置
sudo nginx -t

# 查看 Nginx 错误日志
sudo tail -f /var/log/nginx/error.log

# 查看 Nginx 访问日志
sudo tail -f /var/log/nginx/access.log
```

### 数据库问题

```bash
# 检查数据库文件
ls -la /opt/safeguard/backend/src/data/

# 查看数据库迁移日志
tail -f /opt/safeguard/backend/logs/migration_*.log
```

### 端口冲突

```bash
# 查看端口占用
sudo netstat -tlnp | grep 9999
sudo lsof -i :9999

# 停止占用端口的进程
sudo kill -9 <PID>
```

### 虚拟环境权限问题

如果在安装依赖时遇到 "Permission denied" 错误：

```bash
# 1. 检查虚拟环境权限
ls -la /opt/safeguard/backend/venv_py312/bin/python
ls -la /opt/safeguard/backend/venv_py312/bin/pip

# 2. 修复虚拟环境目录权限（使用正确的用户和组）
sudo chown -R ubuntu:safeguard-group /opt/safeguard/backend/venv_py312
sudo chmod -R 770 /opt/safeguard/backend/venv_py312

# 3. 验证权限已修复
ls -la /opt/safeguard/backend/venv_py312/bin/python
ls -la /opt/safeguard/backend/venv_py312/bin/pip

# 4. 重新安装依赖
source venv_py312/bin/activate
pip install -r requirements.txt
```

如果升级 pip 时遇到权限错误，可以跳过升级步骤，直接安装依赖：

```bash
# 跳过 pip 升级，直接安装依赖
source venv_py312/bin/activate
pip install -r requirements.txt
```

### 服务无法启动（权限问题）

如果服务启动失败且日志显示权限错误：

```bash
# 1. 查看详细日志
sudo journalctl -u safeguard -n 50 --no-pager

# 2. 检查当前用户和组
whoami
groups

# 3. 检查关键目录权限
ls -la /opt/safeguard/backend
ls -la /opt/safeguard/backend/src
ls -la /opt/safeguard/backend/src/data
ls -la /opt/safeguard/backend/logs

# 4. 修复所有目录权限
sudo chown -R ubuntu:safeguard-group /opt/safeguard/backend
sudo chmod -R 750 /opt/safeguard/backend
sudo chmod -R 770 /opt/safeguard/backend/venv_py312

# 5. 确保 data 和 logs 目录有写权限
sudo chmod -R 770 /opt/safeguard/backend/src/data
sudo chmod -R 770 /opt/safeguard/backend/logs

# 6. 重启服务
sudo systemctl restart safeguard
sudo systemctl status safeguard
```

### 组权限未生效

如果修改了用户组但权限未生效：

```bash
# 1. 检查当前用户所属的组
groups

# 2. 如果 safeguard-group 不在列表中，刷新组权限
newgrp safeguard-group

# 3. 或者重新登录（推荐）
exit
# 重新 SSH 登录

# 4. 验证组权限
groups
# 应该能看到 safeguard-group

# 5. 测试目录访问
cd /opt/safeguard/backend
ls -la
```

### SQLite 支持问题

如果启动应用时出现 "ModuleNotFoundError: No module named '_sqlite3'" 错误，说明 Python 3.12 编译时没有包含 SQLite 支持。请按照以下顺序解决：

```bash
# 1. 检查 SQLite3 命令行工具是否可用
sqlite3 --version
# 如果报错，先安装：sudo apt install -y sqlite3

# 2. 检查 SQLite 开发库是否已安装
dpkg -l | grep libsqlite3-dev
# 如果没有显示，安装它：sudo apt install -y libsqlite3-dev

# 3. 检查 Python 3.12 的 SQLite 支持
python3.12 -c "import sqlite3; print('SQLite version:', sqlite3.sqlite_version)"

# 4. 如果步骤 3 报错，需要重新编译 Python 3.12
cd /tmp/Python-3.12.0

# 5. 清理之前的编译文件
make clean

# 6. 重新配置（确保启用 SQLite 支持）
./configure --enable-optimizations --enable-loadable-sqlite-extensions

# 7. 重新编译（需要 10-20 分钟）
make -j$(nproc)

# 8. 重新安装
sudo make altinstall

# 9. 验证 SQLite 支持
python3.12 -c "import sqlite3; print('SQLite version:', sqlite3.sqlite_version)"
# 应该输出：SQLite version: 3.x.x

# 10. 重新启动服务
sudo systemctl restart safeguard
sudo systemctl status safeguard
```

**重要提示**：
- 必须先安装 `sqlite3` 和 `libsqlite3-dev`，然后再编译 Python 3.12
- 如果跳过这些依赖，编译后的 Python 将不支持 SQLite
- 重新编译需要较长时间，请耐心等待

## 安全建议

1. **防火墙配置**
   ```bash
   # 启用 ufw
   sudo ufw enable
   
   # 允许 SSH
   sudo ufw allow 22/tcp
   
   # 允许 HTTP 和 HTTPS
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   
   # 查看状态
   sudo ufw status
   ```

2. **限制 SSH 访问**
   ```bash
   # 编辑 SSH 配置
   sudo vim /etc/ssh/sshd_config
   
   # 禁用 root 登录（建议创建普通用户）
   PermitRootLogin no
   
   # 只允许密钥登录
   PasswordAuthentication no
   
   # 重启 SSH 服务
   sudo systemctl restart sshd
   ```

3. **定期更新系统**
   ```bash
   sudo apt update
   sudo apt upgrade -y
   ```

4. **配置 fail2ban 防止暴力破解**
   ```bash
   sudo apt install -y fail2ban
   sudo systemctl enable fail2ban
   sudo systemctl start fail2ban
   ```

## 性能优化

1. **启用 Nginx Gzip 压缩**
   
   在 `/etc/nginx/nginx.conf` 的 `http` 块中添加：
   ```nginx
   gzip on;
   gzip_vary on;
   gzip_min_length 1024;
   gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/json;
   ```

2. **配置 Nginx 缓存**
   
   在 server 块中添加：
   ```nginx
   location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
       expires 1y;
       add_header Cache-Control "public, immutable";
   }
   ```

3. **调整 Python Worker 数量**
   
   在 Systemd 服务文件中添加：
   ```ini
   Environment="WORKERS=4"
   ```

## 备份策略

1. **数据库备份**
   ```bash
   # 创建备份脚本
   sudo vim /opt/backup-safeguard-db.sh
   
   # 内容：
   #!/bin/bash
   DATE=$(date +%Y%m%d_%H%M%S)
   cp /opt/safeguard/backend/src/data/safeguard.db /opt/backups/safeguard_$DATE.db
   find /opt/backups/ -name "safeguard_*.db" -mtime +7 -delete
   
   # 设置执行权限
   sudo chmod +x /opt/backup-safeguard-db.sh
   
   # 添加到 crontab（每天凌晨3点备份）
   0 3 * * * /opt/backup-safeguard-db.sh
   ```

2. **配置文件备份**
   ```bash
   # 备份配置文件
   tar -czf safeguard-config-backup.tar.gz \
       /opt/safeguard/backend/src/.env.prod \
       /etc/nginx/sites-available/safeguard-backend.conf \
       /etc/systemd/system/safeguard.service
   ```

## 监控建议

1. **服务状态监控**
   ```bash
   # 创建监控脚本
   sudo vim /opt/monitor-safeguard.sh
   
   # 内容：
   #!/bin/bash
   if ! systemctl is-active --quiet safeguard; then
       echo "SafeGuard service is not running"
       systemctl restart safeguard
   fi
   
   # 设置执行权限
   sudo chmod +x /opt/monitor-safeguard.sh
   
   # 添加到 crontab（每5分钟检查一次）
   */5 * * * * /opt/monitor-safeguard.sh
   ```

2. **磁盘空间监控**
   ```bash
   # 检查磁盘使用
   df -h
   
   # 检查日志文件大小
   du -sh /opt/safeguard/backend/logs/
   ```

## 部署验证清单

### 前置检查
- [ ] 操作系统版本正确（Ubuntu 20.04+）
- [ ] 可用内存充足（至少 2GB）
- [ ] 磁盘空间充足（至少 20GB）
- [ ] 端口 80、443、9999 未被占用

### Python 3.12 安装
- [ ] SQLite3 命令行工具已安装（`sqlite3 --version`）
- [ ] SQLite 开发库已安装（`dpkg -l | grep libsqlite3-dev`）
- [ ] Python 3.12 安装成功（`python3.12 --version`）
- [ ] SQLite 支持已启用（`python3.12 -c "import sqlite3; print(sqlite3.sqlite_version)"`）
- [ ] pip 安装成功（`pip --version`）

### 用户和权限配置
- [ ] safeguard-group 组已创建
- [ ] 当前用户已添加到 safeguard-group 组
- [ ] 目录权限配置正确（owner: ubuntu, group: safeguard-group）
- [ ] 虚拟环境权限配置正确（770）

### 应用部署
- [ ] 虚拟环境创建成功
- [ ] 依赖包安装完成
- [ ] 环境变量配置正确
- [ ] Systemd 服务配置正确（使用 ubuntu 用户，不是 root）
- [ ] Systemd 服务运行正常
- [ ] Nginx 配置正确
- [ ] SSL 证书申请成功
- [ ] DNS 解析正常
- [ ] HTTPS 访问正常
- [ ] API 功能测试通过
- [ ] 服务日志无错误
- [ ] 数据库连接正常
- [ ] 防火墙配置正确

## 更新部署

当代码更新后，执行以下步骤：

```bash
# 1. 拉取最新代码
cd /opt/safeguard/backend
git pull origin main

# 2. 检查并修复文件权限（新文件可能需要修复权限）
sudo chown -R ubuntu:safeguard-group /opt/safeguard/backend
sudo chmod -R 750 /opt/safeguard/backend
sudo chmod -R 770 /opt/safeguard/backend/venv_py312

# 3. 切换到 bash（如果当前是 sh）
bash

# 4. 激活虚拟环境
source venv_py312/bin/activate

# 5. 更新依赖（如果有变化）
pip install -r requirements.txt

# 6. 重启服务
sudo systemctl restart safeguard

# 7. 检查状态
sudo systemctl status safeguard
```

## 联系支持

如果在部署过程中遇到问题，请：

1. 查看本文档的故障排查部分
2. 检查服务日志：`sudo journalctl -u safeguard -n 100`
3. 查看 Nginx 日志：`sudo tail -f /var/log/nginx/error.log`
4. 联系技术支持团队

---

**文档版本**: 1.0  
**最后更新**: 2025-01-09  
**适用版本**: SafeGuard Backend v2.1