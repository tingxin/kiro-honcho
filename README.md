# Kiro CLI

通过命令行自动化管理 Kiro (Amazon Q Developer) 用户订阅。

完整流程：创建 IAM Identity Center 用户 → 发送密码重置邮件 → 分配 Kiro 订阅。

## 前置条件

- AWS 账号已开通 Amazon Q Developer Pro 订阅
- IAM Identity Center 已启用
- 本地 AWS credentials 已配置，且 IAM 身份附加了以下托管策略（见下方权限说明）
- conda 环境 `py3`

## 安装

```bash
conda activate py3
pip install -e .
```

## 权限要求

将以下两个 AWS 托管策略附加到运行此 CLI 的 IAM 用户或 Role：

| 托管策略 | 用途 |
|---------|------|
| `AmazonQFullAccess` | Q Developer 订阅管理（创建/删除/变更套餐/列出订阅）及密码重置 |
| `AWSSSOMasterAccountAdministrator` | Identity Center 用户管理（创建用户、查询用户、Group 管理） |

> 如果只使用订阅相关命令（`subscription list/change-plan`、`user add/remove`），`AmazonQFullAccess` 单独即可满足大部分需求。`AWSSSOMasterAccountAdministrator` 在需要管理 Identity Center 用户和 Group 时才必须。

## 配置

```bash
cp .env.example .env
```

编辑 `.env`：

```env
# Identity Center 所在区域（默认 us-east-2）
SSO_REGION=us-east-2

# Kiro 订阅区域（默认 us-east-1）
KIRO_REGION=us-east-1

# SSO Instance ARN（不填则自动取账号下第一个实例）
# KIRO_INSTANCE_ARN=arn:aws:sso:::instance/ssoins-xxxxxxxxxxxxxxxxx

# 订阅类型（默认 Q_DEVELOPER_STANDALONE_PRO）
KIRO_SUBSCRIPTION_TYPE=Q_DEVELOPER_STANDALONE_PRO
```

## 命令结构

```
kiro
├── user          Identity Center 用户管理
│   ├── add       创建用户并分配 Kiro 订阅
│   ├── remove    取消用户的 Kiro 订阅
│   └── find      通过 principalId 前缀查找用户
│
├── password      密码与邮箱验证
│   ├── reset     发送密码重置邮件
│   └── verify    发送邮箱验证邮件
│
├── group         Identity Center Group 管理
│   ├── list      列出所有 Group
│   └── add-user  将用户加入 Group
│
└── subscription  Kiro 订阅管理
    ├── list      列出所有订阅
    └── change-plan  变更用户套餐
```

## 使用示例

### 用户管理

```bash
# 创建用户 + 发送密码邮件 + 分配订阅（一步完成）
kiro user add user@example.com -g John -f Doe

# 指定订阅类型
kiro user add user@example.com -g John -f Doe --subscription Q_DEVELOPER_STANDALONE_PRO_PLUS

# 取消订阅
kiro user remove user@example.com

# 通过 principalId 前缀查找用户（返回 JSON）
kiro user find a17b3570
```

### 密码管理

```bash
# 发送密码重置邮件（默认 email 模式，用户点击邮件直接设置密码）
kiro password reset user@example.com

# 发送一次性密码（OTP 模式）
kiro password reset user@example.com --mode otp

# 发送邮箱验证邮件
kiro password verify user@example.com
```

### Group 管理

```bash
# 列出所有 Group
kiro group list

# 将用户加入指定 Group
kiro group add-user user@example.com "MyGroupName"
```

### 订阅管理

```bash
# 列出所有订阅
kiro subscription list

# 变更单个用户套餐
kiro subscription change-plan user@example.com --subscription Q_DEVELOPER_STANDALONE_PRO_PLUS

# 批量变更多个用户套餐
kiro subscription change-plan user1@example.com user2@example.com user3@example.com --subscription Q_DEVELOPER_STANDALONE_PRO_PLUS
```

## 订阅类型

| 值 | 说明 |
|----|------|
| `Q_DEVELOPER_STANDALONE_PRO` | Pro 套餐 |
| `Q_DEVELOPER_STANDALONE_PRO_PLUS` | Pro+ 套餐 |
| `Q_DEVELOPER_STANDALONE_PRO_POWER` | Power 套餐 |

## 环境变量

所有参数均可通过 `.env` 或环境变量指定，命令行参数优先级更高。

| 环境变量 | 默认值 | 说明 |
|---------|--------|------|
| `SSO_REGION` | `us-east-2` | Identity Center 所在区域 |
| `KIRO_REGION` | `us-east-1` | Kiro 订阅区域 |
| `KIRO_INSTANCE_ARN` | 自动获取 | SSO Instance ARN |
| `KIRO_SUBSCRIPTION_TYPE` | `Q_DEVELOPER_STANDALONE_PRO` | 默认订阅类型 |
