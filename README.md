# Kiro Honcho

Multi-AWS Account Management Platform for Kiro (Amazon Q Developer).

A comprehensive web-based platform for managing multiple AWS accounts, Identity Center users, and Kiro subscriptions.

## Features

### 🌐 Web UI Platform
- **Multi-Account Management**: Add and manage multiple AWS accounts with encrypted credential storage
- **User Management**: Create, list, and manage Identity Center users
- **Subscription Management**: Assign, change, and cancel Kiro subscriptions
- **Batch Operations**: Change subscription plans for multiple users at once
- **Credit Analytics**: Track and visualize user credit usage (coming soon)

### 💻 CLI Tool (Maintained)
- Command-line interface for automation and scripting
- Full backward compatibility with existing workflows

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.11+, FastAPI, SQLAlchemy |
| Frontend | React 18, TypeScript, Ant Design |
| Database | MySQL 8.x (RDS) |
| Auth | JWT + TOTP MFA |

## Quick Start

### Prerequisites
- Docker 24+ & Docker Compose v2+（生产部署）
- Python 3.11+（本地开发）
- Node.js 18+（本地开发）
- AWS Account with Kiro/Q Developer subscription
- MySQL 8.x（RDS 或自建）

### Setup

```bash
# Clone the repository
git clone <repo-url>
cd kiro-honcho

# Run setup script
./start.sh
```

### Development

```bash
# Start both servers
./start-dev.sh

# Or start separately:

# Backend (Terminal 1)
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Frontend (Terminal 2)
cd frontend
npm run dev
```

### Access
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Default Credentials

For development, use:
- Username: `admin`
- Password: `admin123`

⚠️ **Change these credentials in production!**

## Project Structure

```
kiro-honcho/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── main.py            # Application entry
│   │   ├── config.py          # Configuration
│   │   ├── database.py        # DB connection
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── routers/           # API endpoints
│   │   ├── services/          # Business logic
│   │   ├── aws/               # AWS client wrappers
│   │   └── utils/             # Utilities
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                   # React frontend
│   ├── src/
│   │   ├── components/        # Reusable components
│   │   ├── pages/             # Page components
│   │   ├── services/          # API services
│   │   ├── stores/            # Zustand stores
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
│
├── kiro_cli/                   # CLI tool (preserved)
│   ├── cli.py
│   ├── identity_center.py
│   ├── kiro_subscription.py
│   └── aws_client.py
│
├── docs/                       # Documentation
├── ARCHITECTURE.md             # System architecture
└── README.md                   # This file
```

## CLI Usage (Preserved)

The original CLI tool is maintained for automation:

```bash
# Install CLI
pip install -e .

# User management
kiro user add user@example.com -g John -f Doe
kiro user remove user@example.com

# Subscription management
kiro subscription list
kiro subscription change-plan user@example.com --subscription Q_DEVELOPER_STANDALONE_PRO_PLUS

# Password management
kiro password reset user@example.com
```

See `kiro_cli/README.md` for full CLI documentation.

## API Endpoints

### Authentication
- `POST /api/auth/login` - Login
- `POST /api/auth/refresh` - Refresh token
- `GET /api/auth/me` - Current user

### AWS Accounts
- `GET /api/accounts` - List accounts
- `POST /api/accounts` - Add account
- `POST /api/accounts/{id}/verify` - Verify credentials
- `POST /api/accounts/{id}/sync` - Sync users/subscriptions

### Users
- `GET /api/accounts/{id}/users` - List users
- `POST /api/accounts/{id}/users` - Create user
- `DELETE /api/accounts/{id}/users/{uid}` - Delete user

### Subscriptions
- `GET /api/accounts/{id}/subscriptions` - List subscriptions
- `POST /api/accounts/{id}/subscriptions` - Create subscription
- `POST /api/accounts/{id}/subscriptions/change-plan` - Batch change

## AWS Permissions Required

Attach these managed policies to your IAM user/role:

| Policy | Purpose |
|--------|---------|
| `AmazonQFullAccess` | Kiro subscription management |
| `AWSSSOMasterAccountAdministrator` | Identity Center user management |

## Configuration

### Backend Environment Variables

```env
# Database
DATABASE_URL=sqlite+aiosqlite:///./kiro_honcho.db

# JWT
JWT_SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Encryption (for AWS credentials)
APP_ENCRYPTION_KEY=base64-encoded-32-byte-key
```

### Frontend Environment

Create `frontend/.env`:
```env
VITE_API_URL=http://localhost:8000
```

## Production Deployment

### Docker

```bash
# Build and run
docker-compose up -d
```

### Manual

1. Build frontend: `cd frontend && npm run build`
2. Serve via nginx or CDN
3. Run backend: `uvicorn app.main:app --port 8000`
4. Configure PostgreSQL

See `docs/deployment.md` for details.

## Architecture

See [ARCHITECTURE.md](./ARCHITECTURE.md) for detailed system design.

## Contributing

1. Create a feature branch from `dev`
2. Make changes
3. Run tests: `pytest backend/tests/`
4. Submit PR

## License

MIT License - See [LICENSE](./LICENSE)
