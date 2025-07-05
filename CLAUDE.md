# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Numbr Billing is a serverless SaaS billing API built with Python/FastAPI, deployed on AWS Lambda. It integrates with Asaas payment gateway for subscription management and payment processing.

## Key Commands

### Development
```bash
# Local development with hot reload
uvicorn src.main:app --reload --port 3000

# Run with poetry
poetry run uvicorn src.main:app --reload --port 3000
```

### Database
```bash
# Generate migration
poetry run alembic revision --autogenerate -m "Description"

# Apply migrations
poetry run alembic upgrade head

# Rollback migration
poetry run alembic downgrade -1

# Seed admin data
poetry run python scripts/seed_admin.py
```

### Testing
```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=src --cov-report=term-missing

# Run specific test file
poetry run pytest tests/test_checkout.py

# Run tests matching pattern
poetry run pytest -k "test_create_customer"
```

### Code Quality
```bash
# Lint with ruff
poetry run ruff check src/ tests/

# Format with ruff
poetry run ruff format src/ tests/

# Type checking
poetry run mypy src/
```

### Deployment
```bash
# Deploy to AWS Lambda
npx serverless deploy --stage dev

# Deploy to specific stage
npx serverless deploy --stage prod

# View deployment info
npx serverless info --stage dev

# View logs
npx serverless logs -f api --stage dev
```

## Architecture

### Core Services Integration

The application integrates these main systems:

1. **Asaas Payment Gateway** (`src/services/asaas_service.py`)
   - Handles customer creation, subscription management, and payment processing
   - All Asaas API calls are centralized in this service
   - Async HTTP client for optimal performance
   - Webhook events from Asaas are processed to update local database state

2. **Database Models** (`src/models/`)
   - SQLAlchemy 2.0 with async support
   - MySQL database with proper relationships
   - Models: Customer, Subscription, Payment, Plan, Addon, WebhookLog
   - Automatic timestamp tracking with created_at/updated_at

3. **API Endpoints** (`src/routers/`)
   - FastAPI routers for modular endpoint organization
   - Checkout flow endpoints for transparent billing
   - Webhook processing for payment status updates
   - Health check and monitoring endpoints

### Request Flow

1. **Checkout Flow** (`src/routers/checkout.py`)
   - Customer selects plan + addons → Creates/finds customer in Asaas → Creates subscription → Generates payment link
   - Maintains local database records synchronized with Asaas
   - Returns checkout URL for payment completion

2. **Webhook Processing** (`src/routers/webhook.py`)
   - Validates webhook signature using HMAC
   - Maps Asaas payment statuses to local enums
   - Updates subscription status based on payment events
   - Logs all webhook events for debugging and audit trail

### Environment Configuration

The app uses different `.env` files:
- `.env` - Development/production configuration
- `.env.test` - Test database and mock API keys
- Required: `DATABASE_URL`, `ASAAS_API_KEY`, `ASAAS_WEBHOOK_TOKEN`

### Testing Strategy

- **Unit Tests**: Mock external services using pytest fixtures
- **Integration Tests**: Use test database with proper cleanup
- **Async Testing**: Full async/await support in tests
- **Test Coverage**: Maintain high coverage for critical paths

### Key Design Decisions

1. **Async First**: All database operations and HTTP calls are async
2. **Pydantic Models**: Strong typing and validation for all API inputs/outputs
3. **SQLAlchemy 2.0**: Modern ORM with async support
4. **Decimal Handling**: Prices stored as DECIMAL, handled properly in Python
5. **Status Mapping**: Asaas payment statuses mapped to simplified internal enum
6. **Error Handling**: Comprehensive error handling with proper HTTP status codes

## Important Notes

- Use Poetry for dependency management (`poetry install`)
- Test database must exist before running tests
- Asaas sandbox API for development, production API requires real credentials
- API documentation available at `/docs` (Swagger UI) and `/redoc`
- Webhook endpoint `/webhooks/asaas` must be accessible to Asaas servers
- Environment variables loaded from `.env` file in development

## AWS Lambda Deployment

The project is deployed as a serverless application on AWS Lambda:

### Key Files for Lambda
- `src/lambda_handler.py` - Mangum adapter for Lambda
- `serverless.yml` - Serverless Framework configuration
- `.github/workflows/deploy.yml` - Automated deployment pipeline

### Deployment Configuration
- **Service Name**: numbr-billing (without environment suffix)
- **Stages**: dev, staging, prod
- **Region**: us-east-1
- **Runtime**: Python 3.11
- **Architecture**: x86_64

### Deployment Flow
1. Push to branch (develop/staging/main) triggers GitHub Actions
2. Tests run first, then dependencies are packaged
3. Docker is used in CI/CD to compile binary dependencies for Lambda
4. Serverless Framework deploys the stack
5. Lambda function and layer are updated with new code

### Lambda Endpoints
- **API Gateway**: https://vuoxz3psy4.execute-api.us-east-1.amazonaws.com/{stage}
- **Health Check**: GET /health
- **API Documentation**: GET /docs
- **Checkout API**: POST /api/checkout/start
- **Webhook**: POST /webhooks/asaas

### Lambda Considerations
- Database connections use connection pooling appropriate for Lambda
- Binary dependencies must be compiled for Linux x86_64
- Cold starts are minimized with proper memory allocation (1024MB)
- VPC configuration required for RDS access
- Environment variables passed through serverless.yml

### Deployment Issues & Solutions

#### Docker on macOS
When deploying from macOS, Docker permission issues may prevent proper compilation of Python dependencies. Solutions:
1. Use GitHub Actions for deployment (recommended)
2. Enable dockerizePip in serverless.yml only in CI/CD environment
3. Manual deployment script available in project history if needed

#### Database URL Format
The GitHub repository variables store DATABASE_URL with `mysql://` protocol, but Python SQLAlchemy requires `mysql+pymysql://`. The GitHub Actions workflow automatically converts the format during deployment.

#### AWS Profile
- Local deployment uses `--aws-profile numbr`
- GitHub Actions uses AWS credentials configured as secrets
- The serverless.yml has `profile: ${opt:aws-profile, ''}` to support both scenarios

#### Custom Domains
The following custom domains are configured and working:
- **Development**: https://billing-dev.numbr.com.br
- **Staging**: https://billing-staging.numbr.com.br  
- **Production**: https://billing.numbr.com.br

Domain creation is handled automatically by the deployment process using serverless-domain-manager plugin.

## API Endpoints

### Health Check
- `GET /health` - Returns server status and timestamp

### Checkout API
- `GET /api/checkout/plans` - List all available plans
- `GET /api/checkout/addons` - List all available addons
- `POST /api/checkout/start` - Create checkout session
  ```json
  {
    "customer": {
      "name": "string",
      "email": "string",
      "cpf_cnpj": "string",
      "phone": "string"
    },
    "plan_id": "string",
    "addon_ids": ["string"],
    "billing_type": "CREDIT_CARD" | "BOLETO" | "PIX"
  }
  ```

### Webhooks
- `POST /webhooks/asaas` - Receive payment notifications from Asaas
  - Requires valid `asaas-signature` header
  - Updates payment and subscription status

## Admin Panel

The project includes a comprehensive admin panel powered by SQLAdmin with JWT-based authentication:

### Features
- **Multi-user support** with role-based access control (RBAC)
- **JWT authentication** for stateless operation (ideal for serverless)
- **Permission system** with granular resource-based permissions
- **System roles**: Super Admin, Admin, Support, Finance, Viewer
- **Session management** with token revocation support

### Default Admin Credentials
- Email: `admin@numbr.com.br`
- Password: `AdminNumbr2025!`
- **Important**: Change this password after first login!

### Admin Models (`src/models/admin_user.py`)
- **AdminUser**: User accounts with email/password authentication
- **AdminRole**: Roles with customizable permissions
- **AdminSession**: Active session tracking for security

### Admin API Endpoints
- `/api/admin/auth/login` - User login
- `/api/admin/auth/logout` - User logout  
- `/api/admin/auth/refresh` - Refresh access token
- `/api/admin/auth/me` - Get current user info
- `/api/admin/auth/change-password` - Change user password
- `/api/admin/auth/sessions` - List active sessions
- `/api/admin/users/*` - User management (requires ADMIN_USERS permissions)
- `/api/admin/roles/*` - Role management (requires ADMIN_ROLES permissions)

### Admin Panel Access
- **URL**: `/admin`
- **Authentication**: Required - redirects to login page if not authenticated
- **Authorization**: Permission-based access to different sections
- **Interface**: SQLAdmin with custom model views

### Seeding Admin Data
Run the seed script to create initial system roles and superuser:
```bash
poetry run python scripts/seed_admin.py
```

## Development Workflow

1. **Local Development**
   - Create `.env` file with required environment variables
   - Run `poetry install` to install dependencies
   - Run `alembic upgrade head` to apply database migrations
   - Start with `uvicorn src.main:app --reload`

2. **Testing**
   - Run tests before committing: `poetry run pytest`
   - Ensure all tests pass in CI/CD pipeline

3. **Deployment**
   - Push to appropriate branch (develop/staging/main)
   - GitHub Actions handles testing and deployment
   - Monitor deployment in AWS CloudFormation console
   - Test endpoints after deployment

## Workflow Reminders

- Sempre atualize os testes em qualquer alteração do codigo
- Use Poetry para gerenciar dependências
- Nunca faça deploy manual do macOS devido a problemas de compatibilidade binária
- Sempre teste os endpoints após o deploy