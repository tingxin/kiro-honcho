# Kiro Honcho

[中文](./README.md) | [English](./README.en.md) | [Deutsch](./README.de.md)

**Multi-AWS Account Kiro/Q Developer Subscription Management Platform**

A unified platform to manage Identity Center users and Kiro subscriptions across multiple AWS accounts — simplifying user creation, subscription assignment, and plan changes.

---

## Why This Project Exists

If you use AWS Identity Center to manage users and assign Kiro (Amazon Q Developer) subscriptions to your team, you've likely run into these pain points:

**Manual and repetitive**
- Adding a new member requires: create user in Identity Center → wait for email activation → manually open Kiro console → assign subscription. Three steps, three different interfaces.
- Adding 10 users? Repeat 10 times.

**No unified view**
- Identity Center only manages users. The Kiro console only manages subscriptions. The data is siloed.
- To find out "which users haven't verified their email" or "which subscriptions are still Pending", you have to switch between consoles and manually cross-reference.

**Multi-account chaos**
- Companies often have multiple AWS accounts (production, staging, partner). Each has its own Identity Center and Kiro subscriptions.
- AWS provides no cross-account unified view.

**Opaque internal APIs**
- Kiro subscription management uses undocumented internal APIs (SigV4 signed). No official SDK support.
- Permission configuration is complex — `AmazonQFullAccess` does not include all required permissions.

**Kiro Honcho solves all of this:**
- One interface: create user → send activation email → assign subscription, fully automated
- Unified subscription lifecycle view (Email Unverified / Pending / Active)
- Multi-AWS account support with one-click switching
- CSV batch import with real-time progress
- All internal API calls encapsulated, works out of the box

---

## Features

### 🏢 Multi-AWS Account Management
- Add and manage multiple AWS accounts in one place
- Encrypted credential storage (AES-256-GCM)
- Automatic permission verification and Identity Center connection check
- Auto-generated Kiro login URL with one-click copy

### 👥 Full User Lifecycle Management
- **Create user** → auto-join Identity Center → send invitation email → immediately assign Kiro subscription
- **CSV batch import** — only email required, real-time progress display
- **Status tracking** — Email Unverified / Pending / Active three-state display
- **Delete user** — auto-cancel subscription → remove IC user (no impact on other cloud resources)

### 📋 Subscription Management
- View all active subscriptions (filterable by account)
- Change plan (Pro / Pro+ / Power)
- Cancel subscription
- View cancelled subscription history (cross-account)

### 🔄 Auto Sync
- Scheduled sync from AWS (configurable interval)
- Automatic email verification status detection
- Auto-cleanup of deleted users and cancelled subscriptions

### 🔐 Security
- JWT authentication + TOTP MFA (Google Authenticator)
- MFA enforcement — must be set up on first login
- System user management (admin only)

### 📱 Responsive Design
- Desktop: table view
- Mobile: card-based vertical layout

---

## Quick Start

### 1. Prerequisites

| Item | Requirement |
|------|-------------|
| Docker | 24+ |
| Docker Compose | v2+ |
| MySQL | 8.x (RDS or self-hosted) |
| AWS Account | IAM Identity Center enabled, Kiro/Q Developer subscription active, permissions configured as below |

### 2. AWS IAM Permission Setup

⚠️ **Important**: The IAM user for each AWS account requires the following permissions:

**Managed Policy:**
- `AWSSSOMasterAccountAdministrator`

**Custom Inline Policy (required):**

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

> `AmazonQFullAccess` does NOT include internal API permissions (`q:CreateAssignment`, `q:DeleteAssignment`, `q:UpdateAssignment`, `user-subscriptions:ListUserSubscriptions`). These must be granted via inline policy.

### 3. Deploy

```bash
# Clone the repository
git clone <repo-url>
cd kiro-honcho

# Configure environment variables
cp .env.example .env
# Edit .env with your database, JWT secret, and other settings

# Start services
sudo docker compose up -d --build

# Initialize database (first deployment only)
sudo docker compose exec backend python scripts/init_db.py
```

### 4. Access

- Frontend: `http://your-server` (port 80)
- Default credentials: `admin` / `admin123` (MFA setup required on first login)

### 5. Usage Flow

1. **Add AWS Account** — enter AK/SK, SSO Region, Kiro Region
2. **Verify Account** — click Verify to check permissions and Identity Center connection
3. **Sync Data** — click Sync to pull existing users and subscriptions
4. **Manage Users** — create / delete / batch import users
5. **Manage Subscriptions** — change plan / cancel subscription

---

## Environment Variables

```env
# Database (MySQL)
DATABASE_URL=mysql+aiomysql://user:password@host:3306/kiro_honcho
DB_SSL_CA=global-bundle.pem

# JWT Authentication
JWT_SECRET_KEY=your-secret-key-min-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Encryption key for AWS credentials
# Generate: python -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())"
APP_ENCRYPTION_KEY=your-base64-encoded-32-byte-key

# Default admin
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=admin123

# Auto subscription check interval (minutes)
AUTO_SUBSCRIBE_CHECK_INTERVAL=5
```

---

## Update Deployment

```bash
# After pulling latest code
sudo docker compose build --no-cache && sudo docker compose up -d
```

---

## Development Mode

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

# Frontend
cd frontend
npm install
npm run dev  # http://localhost:5020
```

---

## Technical Documentation

For detailed architecture, API design, and data models, see [ARCHITECTURE.md](./ARCHITECTURE.md).

---

## License

MIT License
