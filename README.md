# Kiro Honcho

**多 AWS 账号 Kiro/Q Developer 订阅管理平台**

一站式管理多个 AWS 账号下的 Identity Center 用户和 Kiro 订阅，简化用户创建、订阅分配、套餐变更等日常运维操作。

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

### 1. 前置条件

| 项目 | 要求 |
|------|------|
| Docker | 24+ |
| Docker Compose | v2+ |
| MySQL | 8.x（RDS 或自建） |
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

### 3. 部署

```bash
# 克隆项目
git clone <repo-url>
cd kiro-honcho

# 配置环境变量
cp backend/.env.example backend/.env
# 编辑 backend/.env，填写 MySQL 连接信息和 JWT 密钥

# 启动服务
sudo docker compose up -d --build

# 初始化数据库（首次部署）
sudo docker compose exec backend python scripts/init_db.py
```

### 4. 访问

- 前端界面：`http://your-server`（端口 80）
- 默认账号：`admin` / `admin123`（首次登录会强制设置 MFA）

### 5. 使用流程

1. **添加 AWS 账号** — 填写 AK/SK、SSO Region、Kiro Region
2. **验证账号** — 点击 Verify，自动检测权限和 Identity Center 连接
3. **同步数据** — 点击 Sync，拉取现有用户和订阅
4. **管理用户** — 创建/删除/批量导入用户
5. **管理订阅** — 变更套餐/取消订阅

---

## 环境变量配置

```env
# 数据库（MySQL）
DATABASE_URL=mysql+aiomysql://user:password@host:3306/kiro_honcho
DB_SSL_CA=global-bundle.pem

# JWT 认证
JWT_SECRET_KEY=your-secret-key-min-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 加密密钥（用于加密存储 AWS 凭证）
# 生成方式: python -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"
APP_ENCRYPTION_KEY=your-base64-encoded-32-byte-key

# 默认管理员
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=admin123

# 自动订阅检查间隔（分钟）
AUTO_SUBSCRIBE_CHECK_INTERVAL=5
```

---

## 更新部署

```bash
# 拉取最新代码后
sudo docker compose build --no-cache && sudo docker compose up -d
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
