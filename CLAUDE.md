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

# Seed plans (required before pricing)
poetry run python scripts/seed_plans.py

# Seed revenue ranges and pricing
poetry run python scripts/seed_pricing.py
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
# Deploy to AWS Lambda with Zappa
poetry run zappa deploy dev  # First deployment
poetry run zappa update dev  # Update existing deployment

# Deploy to specific stage
poetry run zappa deploy staging
poetry run zappa deploy prod

# View deployment info
poetry run zappa status dev

# View logs
poetry run zappa tail dev

# Rollback deployment
poetry run zappa rollback dev -n 1

# Undeploy
poetry run zappa undeploy dev
```

## Architecture

### Pricing Structure

The billing system supports dynamic pricing based on customer annual revenue:

1. **Revenue Ranges** (`src/models/revenue_range.py`)
   - Define different company size tiers (Microempresa, Pequena Empresa, etc.)
   - Each range has min/max revenue thresholds
   - Sorted by `sort_order` for proper display

2. **Plan Pricing** (`src/models/plan_pricing.py`)
   - Links plans to revenue ranges with specific prices
   - Each plan can have different prices per revenue range
   - Unique constraint ensures one price per plan/range combination

3. **Customer Revenue** (`src/models/customer.py`)
   - `annual_revenue` field stores customer's yearly revenue
   - Required during checkout to determine applicable pricing

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

## AWS Lambda Deployment with Zappa

The project is deployed as a serverless application on AWS Lambda using Zappa:

### Key Files for Lambda
- `src/handler.py` - Mangum adapter for Lambda
- `zappa_settings.json` - Zappa configuration for all environments
- `.github/workflows/deploy.yml` - Automated deployment pipeline

### Deployment Configuration
- **Service Name**: numbr-billing
- **Stages**: dev, staging, prod
- **Region**: us-east-1
- **Runtime**: Python 3.11
- **Handler**: src.handler.handler

### Deployment Flow
1. Push to branch (develop/staging/main) triggers GitHub Actions
2. Poetry installs dependencies
3. Zappa packages the application with all dependencies
4. Deployment creates/updates Lambda function and API Gateway
5. Database migrations run automatically

### Lambda Endpoints
Zappa automatically generates API Gateway endpoints:
- **Development**: https://billing-dev.numbr.com.br
- **Staging**: https://billing-staging.numbr.com.br  
- **Production**: https://billing.numbr.com.br

### API Endpoints
- **Health Check**: GET /health
- **API Documentation**: GET /docs
- **Admin Panel**: GET /admin
- **Checkout API**: POST /api/checkout/start
- **Webhook**: POST /webhooks/asaas

### Lambda Considerations
- Database connections use async SQLAlchemy with proper pooling
- Memory allocation: 1024MB (dev/staging), 2048MB (prod)
- Timeout: 30 seconds
- Keep warm enabled in production
- VPC configuration handled by Zappa settings

### Local Deployment
```bash
# First time deployment
poetry run zappa deploy dev

# Update existing deployment
poetry run zappa update dev

# Check deployment status
poetry run zappa status dev

# View real-time logs
poetry run zappa tail dev
```

### Environment Variables
Zappa manages environment variables through:
1. `zappa_settings.json` for static variables
2. GitHub Actions for secrets (passed during deployment)
3. AWS Lambda environment variables

### Database URL Format
The GitHub repository variables store DATABASE_URL with `mysql://` protocol, but Python SQLAlchemy requires `mysql+pymysql://`. The GitHub Actions workflow automatically converts the format during deployment.

### AWS Profile
- Local deployment uses profile `numbr` from zappa_settings.json
- GitHub Actions uses AWS credentials configured as secrets
- No manual AWS configuration needed

### Custom Domains
Domains are configured in `zappa_settings.json` and managed by Zappa:
- **Development**: https://billing-dev.numbr.com.br
- **Staging**: https://billing-staging.numbr.com.br  
- **Production**: https://billing.numbr.com.br

### Zappa Advantages
- Simpler configuration than Serverless Framework
- Native Python packaging without Docker issues
- Built-in support for Django/Flask/FastAPI
- Automatic API Gateway configuration
- Easy rollback capabilities
- Direct integration with Poetry (no requirements.txt needed)

### GitHub Actions Configuration
The deployment pipeline requires several secrets and variables configured in GitHub:

**Secrets:**
- `AWS_ACCESS_KEY_ID` - AWS access key
- `AWS_SECRET_ACCESS_KEY` - AWS secret key
- `ASAAS_API_KEY_[DEV|STAGING|PROD]` - Asaas API keys per environment
- `ASAAS_WEBHOOK_TOKEN` - Webhook signature validation
- `JWT_SECRET_KEY` - JWT token signing

**Variables:**
- `DATABASE_URL_[DEV|STAGING|PROD]` - MySQL connection strings
- `ASAAS_API_URL` - Asaas API base URL
- `VPC_SUBNET_IDS` - Comma-separated subnet IDs (optional)
- `VPC_SECURITY_GROUP_IDS` - Comma-separated security group IDs (optional)

See `.github/workflows/README.md` for detailed configuration instructions.

## API Endpoints

### Health Check
- `GET /health` - Returns server status and timestamp

### Checkout API
- `GET /api/checkout/plans` - List all available plans with pricing tiers
  ```json
  [
    {
      "id": "uuid",
      "name": "Professional",
      "description": "Para empresas em crescimento",
      "cycle": "MONTHLY",
      "features": ["Feature 1", "Feature 2"],
      "pricing": [
        {
          "revenue_range_id": "uuid",
          "revenue_range_name": "Microempresa",
          "min_revenue": "0.00",
          "max_revenue": "360000.00",
          "price": "99.90"
        }
      ]
    }
  ]
  ```
- `GET /api/checkout/addons` - List all available addons
- `GET /api/checkout/revenue-ranges` - List all revenue ranges
- `POST /api/checkout/start` - Create checkout session
  ```json
  {
    "customer": {
      "name": "string",
      "email": "string",
      "cpf_cnpj": "string",
      "phone": "string",
      "annual_revenue": "decimal"  // Required for pricing calculation
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

### Admin Panel Architecture
The admin panel uses standard SQLAdmin authentication with session-based authentication:
- Authentication backend: `src/admin/sqladmin_config.py`
- Session storage: Server-side sessions (compatible with Lambda)
- Secure cookies only in production (HTTPS)
- Session tracking in database for security
- Default admin created by `scripts/seed_admin.py`

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
- Deploy local com Zappa funciona perfeitamente no macOS
- Sempre teste os endpoints após o deploy
- Use `zappa tail` para monitorar logs em tempo real