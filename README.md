# Kiro Honcho

[中文](./README.md) | [English](./README.en.md) | [Deutsch](./README.de.md)

**多 AWS 账号 Kiro/Q Developer 订阅管理平台**

一站式管理多个 AWS 账号下的 Identity Center 用户和 Kiro 订阅，简化用户创建、订阅分配、套餐变更等日常运维操作。

---

## 为什么要做这个项目

如果你在企业中使用 AWS Identity Center 管理用户，并为团队成员分配 Kiro（Amazon Q Developer）订阅，你一定遇到过这些痛点：

**手动操作繁琐**
- 每次新增成员，需要先在 Identity Center 创建用户，等待邮件激活，再手动进入 Kiro 控制台分配订阅——三个步骤，三个不同的界面
- 批量添加 10 个用户？重复 10 遍

**没有统一视图**
- Identity Center 只管用户，Kiro 控制台只管订阅，两边数据割裂
- 想知道"哪些用户还没激活邮箱"、"哪些订阅是 Pending 状态"，需要来回切换界面对比

**多账号管理混乱**
- 公司有多个 AWS 账号（如生产、测试、合作伙伴），每个账号都有独立的 Identity Center 和 Kiro 订阅
- AWS 控制台没有跨账号统一视图

**AWS 内部 API 不透明**
- Kiro 订阅管理使用的是未公开的内部 API（SigV4 签名），没有官方 SDK 支持
- 权限配置复杂，`AmazonQFullAccess` 托管策略不包含所有必要权限

**Kiro Honcho 解决了这些问题：**
- 一个界面完成：创建用户 → 发送激活邮件 → 分配订阅，全程自动化
- 统一展示用户订阅生命周期状态（邮箱未激活 / Pending / Active）
- 支持多 AWS 账号，账号间一键切换
- CSV 批量导入，实时进度显示
- 封装了所有内部 API 调用，开箱即用

---

## 功能介绍

### � 多 AWS 账号管理
- 支持添加多个 AWS 账号，统一管理
- 加密存储 AWS 凭证（AES-256-GCM）
- 自动验证账号权限和 Identity Center 连接
- 自动生成 Kiro 登录 URL，一键复制

### 👥 用户全生命周期管理
- **创建用户** → 自动加入 Identity Center → 发送邀请邮件 → 立即分配 Kiro 订阅
- **CSV 批量导入** — 只需邮箱列，实时进度显示
- **状态追踪** — 邮箱未激活 / Pending / Active 三态显示
- **删除用户** — 自动取消订阅 → 删除 IC 用户（不影响云上其他资源）

### � 订阅管理
- 查看所有活跃订阅（按账号筛选）
- 变更套餐（Pro / Pro+ / Power）
- 取消订阅
- 已取消订阅历史查看（跨账号）

### 🔄 自动同步
- 定时从 AWS 同步用户和订阅数据（可配置间隔）
- 自动检测邮箱验证状态
- 自动清理已删除的用户和已取消的订阅

### 🔐 安全
- JWT 认证 + TOTP MFA（Google Authenticator）
- 强制 MFA — 首次登录必须设置
- 系统用户管理（仅管理员）

### 📱 响应式设计
- 桌面端：表格视图
- 移动端：卡片式纵向布局

---

## 快速开始

> 只需 3 步，30 秒启动。默认使用 SQLite，无需额外数据库。

```bash
mkdir kiro-honcho && cd kiro-honcho

# 下载部署文件
curl -O https://raw.githubusercontent.com/barryxu119/kiro-honcho/dev/docker-compose.deploy.yml
curl -O https://raw.githubusercontent.com/barryxu119/kiro-honcho/dev/.env.example
cp .env.example .env

# 启动
sudo docker compose -f docker-compose.deploy.yml pull
sudo docker compose -f docker-compose.deploy.yml up -d
```

访问 `http://your-server`，默认账号 `admin` / `admin123`（首次登录会强制设置 MFA）。

镜像地址：
- `barryxu119/kiro-honcho-backend:latest`
- `barryxu119/kiro-honcho-frontend:latest`

---

## 详细部署指南

### 1. 前置条件

| 项目 | 要求 |
|------|------|
| Docker | 24+ |
| Docker Compose | v2+ |
| 数据库 | SQLite（默认，无需额外安装）或 MySQL 8.x |
| AWS 账号 | 已开通IAM Identity Center, Kiro/Q Developer 订阅服务, 如下配置好相关权限 |


### 2. AWS IAM 权限配置

⚠️ **重要**：每个 AWS 账号的 IAM 用户需要以下权限：

**托管策略：**
- `AWSSSOMasterAccountAdministrator`

**自定义 Inline Policy（必须）：**

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "user-subscriptions:*",
                "q:*"
            ],
            "Resource": "*"
        }
    ]
}
```

> `AmazonQFullAccess` 不包含内部 API 权限（`q:CreateAssignment`、`q:DeleteAssignment`、`q:UpdateAssignment`、`user-subscriptions:ListUserSubscriptions`），必须通过 inline policy 单独授权。

### 3. 部署方式

#### 方式一：Docker Hub 镜像部署（推荐）

即上面"快速开始"的方式。如需自定义配置，编辑 `.env` 文件后重启：

```bash
# 编辑配置
vi .env

# 重启生效
sudo docker compose -f docker-compose.deploy.yml up -d
```

#### 方式二：源码构建部署

```bash
git clone <repo-url>
cd kiro-honcho
cp .env.example .env
# 编辑 .env

sudo docker compose up -d --build
```

### 4. 使用流程

1. **添加 AWS 账号** — 填写 AK/SK、SSO Region、Kiro Region
2. **验证账号** — 点击 Verify，自动检测权限和 Identity Center 连接
3. **同步数据** — 点击 Sync，拉取现有用户和订阅
4. **管理用户** — 创建/删除/批量导入用户
5. **管理订阅** — 变更套餐/取消订阅

---

## 环境变量配置

项目使用根目录下唯一的 `.env` 文件管理所有配置：

```env
# ===== 数据库配置 =====
# DB_TYPE: sqlite 或 mysql
DB_TYPE=sqlite

# SQLite（默认，数据存储在 ./data 目录，Docker 自动挂载持久化）
# SQLITE_PATH=/app/data/kiro_honcho.db

# MySQL（取消注释并填写）
# MYSQL_HOST=your-mysql-host
# MYSQL_PORT=3306
# MYSQL_USER=root
# MYSQL_PASSWORD=your-password
# MYSQL_DATABASE=kiro_honcho
# DB_SSL_CA=global-bundle.pem

# ===== JWT 认证 =====
JWT_SECRET_KEY=your-secret-key-min-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ===== 加密密钥（用于加密存储 AWS 凭证）=====
# 生成方式: python -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"
APP_ENCRYPTION_KEY=your-base64-encoded-32-byte-key

# ===== 默认管理员 =====
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=admin123

# ===== 其他 =====
CORS_ORIGINS=http://your-domain.com
AUTO_SUBSCRIBE_CHECK_INTERVAL=5
DEFAULT_SSO_REGION=us-east-2
DEFAULT_KIRO_REGION=us-east-1
```

---

## 更新部署

```bash
# Docker Hub 镜像方式
sudo docker compose -f docker-compose.deploy.yml pull
sudo docker compose -f docker-compose.deploy.yml up -d

# 源码构建方式
git pull
sudo docker compose build --no-cache
sudo docker compose up -d
```

---

## 开发模式

```bash
# 后端
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# 前端
cd frontend
npm install
npm run dev  # http://localhost:5020
```

---

## 技术文档

详细的技术架构、API 设计、数据模型等内容请参考 [ARCHITECTURE.md](./ARCHITECTURE.md)。

---

## License

MIT License
