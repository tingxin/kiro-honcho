# Kiro Honcho - 多 AWS 账号管理平台架构设计

## 项目概述

将现有的 Kiro CLI 工具升级为一个带前后端 UI 的多 AWS 账号管理平台，支持多 AWS 账号管理、用户订阅全流程管理、以及 Kiro 用户 Credit 使用统计。

---

## 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React + Ant Design)            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐│
│  │账号管理   │  │用户管理   │  │订阅管理   │  │Credit 统计分析   ││
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              │ REST API / WebSocket
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Backend (FastAPI)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────────┐│
│  │认证模块   │  │账号服务   │  │用户服务   │  │订阅服务          ││
│  │(JWT)     │  │          │  │          │  │                  ││
│  └──────────┘  └──────────┘  └──────────┘  └──────────────────┘│
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                     │
│  │Credit服务│  │批量操作   │  │任务队列   │                     │
│  │          │  │          │  │(asyncio) │                     │
│  └──────────┘  └──────────┘  └──────────┘                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Data Layer (SQLite / PostgreSQL)             │
│  ┌──────────────────┐  ┌──────────────────┐                   │
│  │ aws_accounts     │  │ users            │                   │
│  │ subscriptions    │  │ credit_usage     │                   │
│  │ operation_logs   │  │ batch_tasks      │                   │
│  └──────────────────┘  └──────────────────┘                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AWS Services                                 │
│  ┌──────────────────┐  ┌──────────────────┐                   │
│  │ Identity Center  │  │ Kiro/Q Developer │                   │
│  │ (SSO)            │  │ Subscription     │                   │
│  └──────────────────┘  └──────────────────┘                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 技术栈

### 后端
- **框架**: Python FastAPI 3.x
- **数据库ORM**: SQLAlchemy 2.x
- **认证**: JWT (python-jose[cryptography])
- **数据验证**: Pydantic v2
- **加密**: cryptography (AES-256-GCM)
- **异步支持**: asyncio + aiohttp

### 前端
- **框架**: React 18+
- **UI库**: Ant Design 5.x
- **状态管理**: Zustand / React Query
- **路由**: React Router 6
- **HTTP客户端**: Axios
- **图表**: ECharts / Recharts

### 数据库
- **开发/轻量部署**: SQLite 3
- **生产环境**: PostgreSQL 15+
- **迁移工具**: Alembic

---

## 目录结构

```
kiro-honcho/
├── backend/                          # 后端服务
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI 入口
│   │   ├── config.py                 # 配置管理
│   │   ├── database.py               # 数据库连接
│   │   ├── models/                   # SQLAlchemy 模型
│   │   │   ├── __init__.py
│   │   │   ├── aws_account.py
│   │   │   ├── user.py
│   │   │   ├── subscription.py
│   │   │   ├── credit_usage.py
│   │   │   ├── operation_log.py
│   │   │   └── batch_task.py
│   │   ├── schemas/                  # Pydantic 模型
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── aws_account.py
│   │   │   ├── user.py
│   │   │   ├── subscription.py
│   │   │   └── credit.py
│   │   ├── routers/                  # API 路由
│   │   │   ├── __init__.py
│   │   │   ├── auth.py               # 认证 API
│   │   │   ├── accounts.py           # AWS 账号管理
│   │   │   ├── users.py              # 用户管理
│   │   │   ├── subscriptions.py      # 订阅管理
│   │   │   ├── credits.py            # Credit 统计
│   │   │   └── batch.py              # 批量操作
│   │   ├── services/                 # 业务逻辑层
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── account_service.py
│   │   │   ├── user_service.py
│   │   │   ├── subscription_service.py
│   │   │   └── credit_service.py
│   │   ├── aws/                      # AWS 客户端封装
│   │   │   ├── __init__.py
│   │   │   ├── base_client.py        # 基础 SigV4 客户端
│   │   │   ├── identity_center.py    # 移植现有代码
│   │   │   └── kiro_subscription.py  # 移植现有代码
│   │   ├── utils/                    # 工具函数
│   │   │   ├── __init__.py
│   │   │   ├── encryption.py         # 加密工具
│   │   │   └── jwt_handler.py        # JWT 处理
│   │   └── middleware/               # 中间件
│   │       ├── __init__.py
│   │       └── auth_middleware.py
│   ├── alembic/                      # 数据库迁移
│   │   └── versions/
│   ├── tests/                        # 测试
│   │   ├── __init__.py
│   │   ├── test_accounts.py
│   │   ├── test_users.py
│   │   └── test_subscriptions.py
│   ├── requirements.txt
│   └── alembic.ini
│
├── frontend/                         # 前端应用
│   ├── src/
│   │   ├── components/               # 通用组件
│   │   │   ├── Layout/
│   │   │   ├── AccountSelector/
│   │   │   └── PermissionGuard/
│   │   ├── pages/                    # 页面
│   │   │   ├── Login/
│   │   │   ├── Dashboard/
│   │   │   ├── Accounts/             # AWS 账号管理
│   │   │   ├── Users/                # 用户管理
│   │   │   ├── Subscriptions/        # 订阅管理
│   │   │   └── Credits/              # Credit 分析
│   │   ├── services/                 # API 调用
│   │   │   ├── auth.ts
│   │   │   ├── accounts.ts
│   │   │   ├── users.ts
│   │   │   └── subscriptions.ts
│   │   ├── stores/                   # 状态管理
│   │   ├── hooks/                    # 自定义 Hooks
│   │   ├── utils/                    # 工具函数
│   │   ├── types/                    # TypeScript 类型
│   │   └── App.tsx
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
│
├── kiro_cli/                         # CLI 工具（保持兼容）
│   ├── __init__.py
│   ├── cli.py                        # CLI 入口
│   ├── aws_client.py
│   ├── identity_center.py
│   └── kiro_subscription.py
│
├── docs/                             # 文档
│   ├── api.md                        # API 文档
│   ├── deployment.md                 # 部署指南
│   └── development.md                # 开发指南
│
├── docker-compose.yml                # 开发环境
├── Dockerfile.backend
├── Dockerfile.frontend
├── ARCHITECTURE.md                   # 本文档
├── README.md
└── setup.py                          # CLI 安装
```

---

## 数据模型设计

### 1. AWS 账号 (aws_accounts)

```python
class AWSAccount(Base):
    __tablename__ = "aws_accounts"

    id: int                    # 主键
    name: str                  # 账号名称（用户定义）
    access_key_id: str         # AWS Access Key ID（加密存储）
    secret_access_key: str     # AWS Secret Access Key（加密存储）
    region: str                # 默认区域
    identity_center_arn: str   # Identity Center 实例 ARN
    identity_store_id: str     # Identity Store ID
    status: str                # active, invalid, pending
    last_verified: datetime    # 最后验证时间
    permissions: JSON          # 权限检查结果缓存
    created_at: datetime
    updated_at: datetime
```

### 2. Identity Center 用户 (ic_users)

```python
class ICUser(Base):
    __tablename__ = "ic_users"

    id: int                    # 主键
    aws_account_id: int        # 关联 AWS 账号
    user_id: str               # AWS Identity Center UserId
    user_name: str             # 用户名
    display_name: str          # 显示名称
    email: str                 # 邮箱
    status: str                # enabled, disabled
    groups: JSON               # 所属 Group 列表
    last_synced: datetime      # 最后同步时间
    created_at: datetime
```

### 3. Kiro 订阅 (kiro_subscriptions)

```python
class KiroSubscription(Base):
    __tablename__ = "kiro_subscriptions"

    id: int                    # 主键
    user_id: int               # 关联用户
    principal_id: str          # AWS PrincipalId
    subscription_type: str     # PRO, PRO_PLUS, PRO_POWER
    status: str                # active, suspended, cancelled
    start_date: datetime       # 订阅开始时间
    last_synced: datetime      # 最后同步时间
    created_at: datetime
```

### 4. Credit 使用统计 (credit_usage)

```python
class CreditUsage(Base):
    __tablename__ = "credit_usage"

    id: int                    # 主键
    user_id: int               # 关联用户
    date: date                 # 统计日期
    total_credits: int         # 总使用 credits
    feature_breakdown: JSON    # 各功能使用明细
    created_at: datetime
```

### 5. 操作日志 (operation_logs)

```python
class OperationLog(Base):
    __tablename__ = "operation_logs"

    id: int                    # 主键
    aws_account_id: int        # 关联账号
    operation: str             # 操作类型
    target: str                # 操作目标
    status: str                # success, failed
    message: str               # 详细信息
    operator: str              # 操作人（可选）
    created_at: datetime
```

### 6. 批量任务 (batch_tasks)

```python
class BatchTask(Base):
    __tablename__ = "batch_tasks"

    id: int                    # 主键
    task_type: str             # 任务类型
    aws_account_id: int        # 关联账号
    targets: JSON              # 操作目标列表
    status: str                # pending, running, completed, failed
    progress: int              # 进度百分比
    result: JSON               # 执行结果
    created_at: datetime
    completed_at: datetime
```

---

## API 设计

### 认证 API

| Method | Endpoint | 描述 |
|--------|----------|------|
| POST | `/api/auth/login` | 登录获取 JWT Token |
| POST | `/api/auth/logout` | 登出 |
| GET | `/api/auth/me` | 获取当前用户信息 |
| POST | `/api/auth/refresh` | 刷新 Token |

### AWS 账号管理 API

| Method | Endpoint | 描述 |
|--------|----------|------|
| GET | `/api/accounts` | 列出所有 AWS 账号 |
| POST | `/api/accounts` | 添加新 AWS 账号 |
| GET | `/api/accounts/{id}` | 获取账号详情 |
| PUT | `/api/accounts/{id}` | 更新账号信息 |
| DELETE | `/api/accounts/{id}` | 删除账号 |
| POST | `/api/accounts/{id}/verify` | 验证账号权限 |
| POST | `/api/accounts/{id}/sync` | 同步账号数据 |

### 用户管理 API

| Method | Endpoint | 描述 |
|--------|----------|------|
| GET | `/api/accounts/{account_id}/users` | 列出用户 |
| POST | `/api/accounts/{account_id}/users` | 创建用户 |
| GET | `/api/accounts/{account_id}/users/{id}` | 获取用户详情 |
| DELETE | `/api/accounts/{account_id}/users/{id}` | 删除用户 |
| POST | `/api/accounts/{account_id}/users/{id}/reset-password` | 重置密码 |
| POST | `/api/accounts/{account_id}/users/{id}/verify-email` | 发送邮箱验证 |

### 订阅管理 API

| Method | Endpoint | 描述 |
|--------|----------|------|
| GET | `/api/accounts/{account_id}/subscriptions` | 列出订阅 |
| POST | `/api/accounts/{account_id}/subscriptions` | 创建订阅 |
| PUT | `/api/accounts/{account_id}/subscriptions/{id}` | 变更套餐 |
| DELETE | `/api/accounts/{account_id}/subscriptions/{id}` | 取消订阅 |

### Credit 统计 API

| Method | Endpoint | 描述 |
|--------|----------|------|
| GET | `/api/accounts/{account_id}/credits/summary` | Credit 汇总 |
| GET | `/api/accounts/{account_id}/credits/users` | 用户 Credit 列表 |
| GET | `/api/accounts/{account_id}/credits/trend` | 使用趋势 |
| GET | `/api/accounts/{account_id}/credits/breakdown` | 功能分解 |

### 批量操作 API

| Method | Endpoint | 描述 |
|--------|----------|------|
| POST | `/api/batch/users/create` | 批量创建用户 |
| POST | `/api/batch/subscriptions/change-plan` | 批量变更套餐 |
| GET | `/api/batch/tasks/{id}` | 获取任务状态 |
| DELETE | `/api/batch/tasks/{id}` | 取消任务 |

---

## 安全设计

### 1. AWS 凭证加密

使用 AES-256-GCM 加密存储 AWS Secret Access Key：

```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

class EncryptionService:
    def __init__(self, master_key: bytes):
        self.aesgcm = AESGCM(master_key)
    
    def encrypt(self, plaintext: str) -> str:
        nonce = os.urandom(12)
        ciphertext = self.aesgcm.encrypt(nonce, plaintext.encode(), None)
        return base64.b64encode(nonce + ciphertext).decode()
    
    def decrypt(self, encrypted: str) -> str:
        data = base64.b64decode(encrypted)
        nonce, ciphertext = data[:12], data[12:]
        return self.aesgcm.decrypt(nonce, ciphertext, None).decode()
```

### 2. JWT 认证

```python
# Token 配置
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# JWT Claims
{
    "sub": "user_id",
    "exp": expiration,
    "iat": issued_at,
    "type": "access" | "refresh"
}
```

### 3. 权限验证

在每个 AWS 账号添加时，自动检查以下权限：
- `AmazonQFullAccess` - Kiro 订阅管理
- `AWSSSOMasterAccountAdministrator` - Identity Center 管理

---

## 前端页面设计

### 1. 账号管理页面

- 账号列表（卡片视图）
- 添加账号表单（AK/SK 输入 + 验证）
- 账号详情（权限状态、实例信息）
- 账号切换下拉框

### 2. 用户管理页面

- 用户列表（分页表格）
- 创建用户表单
- 批量导入用户（CSV 上传）
- 操作按钮：重置密码、发送验证、加入组

### 3. 订阅管理页面

- 订阅列表（状态标签）
- 套餐变更弹窗
- 批量变更按钮

### 4. Credit 统计页面

- 总览卡片（总 Credit、活跃用户、平均使用）
- 趋势折线图
- 用户排行表格
- 功能使用饼图

---

## 兼容性设计

### CLI 工具保持不变

保留 `kiro_cli/` 目录下的所有代码，CLI 继续通过环境变量和 AWS 配置工作。

### 共享核心逻辑

将 AWS 操作逻辑抽取到 `backend/app/aws/` 模块：
- `kiro_cli` 导入 `backend.app.aws` 模块
- 或复制代码保持独立（推荐，避免耦合）

```python
# CLI 可以选择导入后端模块
# from backend.app.aws.identity_center import get_instance_info

# 或保持独立实现
```

---

## 部署方案

### 开发环境

```bash
# 后端
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 前端
cd frontend && npm install && npm run dev
```

### 生产环境

```yaml
# docker-compose.yml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://...
      - ENCRYPTION_KEY=...
    volumes:
      - ./data:/app/data

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: kiro_honcho
      POSTGRES_USER: kiro
      POSTGRES_PASSWORD: ***
    volumes:
      - pgdata:/var/lib/postgresql/data
```

---

## 实施计划

### Phase 1: 后端基础 (Week 1)
1. 创建项目结构
2. 实现数据库模型
3. 实现认证 API
4. 实现 AWS 账号管理 API

### Phase 2: 核心功能 (Week 2)
1. 移植 AWS 客户端代码
2. 实现用户管理 API
3. 实现订阅管理 API
4. 权限验证功能

### Phase 3: 前端开发 (Week 3)
1. 搭建 React 项目
2. 实现登录页面
3. 实现账号管理页面
4. 实现用户管理页面

### Phase 4: 高级功能 (Week 4)
1. Credit 统计 API
2. 批量操作功能
3. 前端高级页面
4. 测试与优化

---

## 技术细节

### 环境变量

```env
# 应用配置
APP_ENV=development
APP_SECRET_KEY=your-secret-key
APP_ENCRYPTION_KEY=your-32-byte-encryption-key

# 数据库
DATABASE_URL=sqlite:///./kiro_honcho.db

# JWT
JWT_SECRET_KEY=your-jwt-secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 错误处理

```python
# 统一错误响应格式
{
    "success": false,
    "error": {
        "code": "ACCOUNT_NOT_FOUND",
        "message": "AWS account with id 123 not found"
    }
}
```

### 日志记录

所有 AWS 操作记录到 `operation_logs` 表，包含：
- 操作类型、目标
- 执行状态、详细消息
- 时间戳

---

## 总结

本架构设计实现了：
1. **多账号管理** - 加密存储、权限验证
2. **完整用户订阅流程** - 从创建到变更
3. **Credit 统计分析** - 数据可视化
4. **批量操作支持** - 异步任务队列
5. **CLI 兼容性** - 保持现有功能

技术选型注重实用性和可维护性，FastAPI 提供高性能异步支持，React + Ant Design 提供现代化的管理界面。
