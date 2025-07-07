# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Numbr Billing is a serverless SaaS billing API built with Python/Flask, deployed on AWS Lambda using Zappa. It integrates with Asaas payment gateway for subscription management and payment processing.

## Key Commands

### Development
```bash
# Local development
flask --app src.main:app run --port 3000

# Run with poetry
poetry run flask --app src.main:app run --port 3000
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
   - Synchronous HTTP client using httpx
   - Webhook events from Asaas are processed to update local database state

2. **Database Models** (`src/models/`)
   - SQLAlchemy 2.0 with synchronous sessions
   - MySQL database with proper relationships
   - Models: Customer, Subscription, Payment, Plan, Addon, WebhookLog
   - Automatic timestamp tracking with created_at/updated_at

3. **API Endpoints** (`src/routers/`)
   - Flask blueprints for modular endpoint organization
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
- Required: `DATABASE_URL`, `ASAAS_API_KEY`, `ASAAS_WEBHOOK_TOKEN`, `JWT_SECRET_KEY`

### Testing Strategy

- **Unit Tests**: Mock external services using pytest fixtures
- **Integration Tests**: Use test database with proper cleanup
- **Test Coverage**: Maintain high coverage for critical paths

### Key Design Decisions

1. **Flask Framework**: Migrated from FastAPI to Flask for better Zappa compatibility
2. **Synchronous Operations**: All database operations and HTTP calls are synchronous
3. **Pydantic Models**: Strong typing and validation for all API inputs/outputs
4. **SQLAlchemy 2.0**: Modern ORM with connection pooling
5. **Decimal Handling**: Prices stored as DECIMAL, handled properly in Python
6. **Status Mapping**: Asaas payment statuses mapped to simplified internal enum
7. **Error Handling**: Comprehensive error handling with proper HTTP status codes

## Important Notes

- Use Poetry for dependency management (`poetry install`)
- Test database must exist before running tests
- Asaas sandbox API for development, production API requires real credentials
- Webhook endpoint `/webhooks/asaas` must be accessible to Asaas servers
- Environment variables loaded from `.env` file in development

## AWS Lambda Deployment with Zappa

The project is deployed as a serverless application on AWS Lambda using Zappa:

### Key Files for Lambda
- `src/handler.py` - Flask app export for Lambda
- `zappa_settings.json` - Zappa configuration for all environments
- `.github/workflows/deploy.yml` - Automated deployment pipeline

### Key Files for Admin Panel
- `src/admin/flask_admin.py` - Flask-Admin configuration and views
- `src/templates/admin/login.html` - Custom login page
- `src/templates/admin/custom_base.html` - Custom base template (optional)

### Deployment Configuration
- **Service Name**: numbr-billing
- **Stages**: dev, staging, prod
- **Region**: us-east-1
- **Runtime**: Python 3.11
- **Handler**: src.main.app

### Deployment Flow
1. Push to branch (develop/staging/main) triggers GitHub Actions
2. Poetry installs dependencies
3. Zappa packages the application with all dependencies
4. Deployment creates/updates Lambda function and API Gateway
5. Database migrations run automatically

### Lambda Endpoints
Zappa automatically generates API Gateway endpoints:
- **Development**: https://n61x7gkngj.execute-api.us-east-1.amazonaws.com/dev
- **Staging**: TBD
- **Production**: TBD

### API Endpoints
- **Health Check**: GET /health
- **Checkout API**: POST /api/checkout/start
- **Webhook**: POST /webhooks/asaas

### Lambda Considerations
- Database connections use SQLAlchemy with proper pooling
- Memory allocation: 1024MB (dev/staging), 2048MB (prod)
- Timeout: 30 seconds
- Keep warm enabled in production
- Slim handler enabled to reduce package size

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
Domains will be configured in `zappa_settings.json` and managed by Zappa:
- **Development**: https://billing-dev.numbr.com.br (TBD)
- **Staging**: https://billing-staging.numbr.com.br (TBD)
- **Production**: https://billing.numbr.com.br (TBD)

### Zappa Advantages
- Better compatibility with WSGI apps like Flask
- Native Python packaging without Docker issues
- Built-in support for Flask
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
- `DATABASE_URL` - MySQL connection string
- `ASAAS_API_URL` - Asaas API base URL
- `VPC_SUBNET_IDS` - Comma-separated subnet IDs (optional)
- `VPC_SECURITY_GROUP_IDS` - Comma-separated security group IDs (optional)

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

The project includes a comprehensive admin panel powered by Flask-Admin with JWT-based authentication:

### Features
- **Flask-Admin integration** with custom templates and JWT authentication
- **Multi-user support** with role-based access control (RBAC)
- **JWT authentication** using Flask-JWT-Extended for both API and web interface
- **Permission system** with granular resource-based permissions
- **System roles**: Super Admin, Admin, Support, Finance, Viewer
- **Session management** with token tracking
- **Custom model views** with RBAC integration for all database models

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

### Admin Panel UI
The admin panel is powered by Flask-Admin with custom authentication and RBAC integration:
- **URL**: `/admin`
- **Authentication**: JWT-based with cookies for web interface
- **Authorization**: Permission-based access to different sections
- **Interface**: Bootstrap 4 theme with responsive design

### Accessing Admin Panel Locally
```bash
# Run the Flask app
poetry run python src/main.py

# Access admin panel
# Open browser at: http://localhost:3000/admin/
```

The admin panel will redirect to login page if not authenticated. Use the default credentials or create a new admin user with the seed script.

#### Available Admin Views:
1. **Customers** - Full CRUD operations
2. **Plans** - Manage subscription plans
3. **Addons** - Manage plan addons
4. **Revenue Ranges** - Configure pricing tiers
5. **Plan Pricing** - Set prices per revenue range
6. **Subscriptions** - View and manage active subscriptions
7. **Subscription Addons** - Manage subscription extras
8. **Payments** - View payment history (read-only)
9. **Webhook Logs** - View webhook events (read-only)
10. **Admin Users** - Manage admin accounts
11. **Admin Roles** - Configure roles and permissions

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
   - Start with `flask --app src.main:app run --port 3000`

2. **Testing**
   - Run tests before committing: `poetry run pytest`
   - Ensure all tests pass in CI/CD pipeline

3. **Deployment**
   - Push to appropriate branch (develop/staging/main)
   - GitHub Actions handles testing and deployment
   - Monitor deployment in AWS Lambda console
   - Test endpoints after deployment

## Migration from FastAPI to Flask

The project was migrated from FastAPI to Flask for better Zappa compatibility:

### Key Changes:
1. **Web Framework**: FastAPI → Flask
2. **Database Operations**: Async SQLAlchemy → Sync SQLAlchemy
3. **HTTP Client**: httpx AsyncClient → httpx Client  
4. **Routing**: FastAPI routers → Flask blueprints
5. **Authentication**: FastAPI Depends → Flask-JWT-Extended decorators
6. **Admin Panel**: SQLAdmin → Flask-Admin with JWT authentication

### Benefits:
- Native WSGI support (Zappa works better with WSGI apps)
- Simpler deployment without ASGI-to-WSGI conversion
- Reduced complexity in Lambda environment
- Better compatibility with traditional Python libraries

## Flask-Admin on AWS Lambda

### Known Issues and Solutions

Flask-Admin can have issues running on AWS Lambda due to static file serving limitations. The application has been configured to handle this:

1. **CDN for Static Assets**: When `IS_LAMBDA` environment variable is set, Flask-Admin uses CDN URLs for Bootstrap, jQuery, and other assets instead of serving them locally.

2. **Custom Base Template**: The `src/templates/admin/custom_base.html` template conditionally loads assets from CDN when running on Lambda.

3. **Error Handling**: Comprehensive error handlers have been added to capture and log 500 errors for debugging.

4. **Database Session Management**: Proper session cleanup is configured to prevent connection leaks in Lambda environment.

### Accessing Admin Panel
- **Local**: http://localhost:3000/admin/
- **Development**: https://billing-dev.numbr.com.br/admin/
- **Staging**: https://billing-staging.numbr.com.br/admin/
- **Production**: https://billing.numbr.com.br/admin/

### Troubleshooting
If the admin panel shows 500 errors:
1. Check CloudWatch logs using `poetry run zappa tail [stage]`
2. Verify `IS_LAMBDA=true` is set in environment variables
3. Ensure database connections are accessible from Lambda
4. Check that all Flask-Admin dependencies are included in the deployment

## AWS Lambda Deployment with Zappa

### Current Deployment Status
- **Development Environment**: Successfully deployed
- **API Gateway URL**: https://py4cwe15d0.execute-api.us-east-1.amazonaws.com/dev
- **Lambda Function**: numbr-billing-dev
- **S3 Bucket**: numbr-billing-zappa-deployments

### Deployment Commands
```bash
# Deploy new environment
poetry run zappa deploy dev

# Update existing deployment
poetry run zappa update dev

# Check deployment status
poetry run zappa status dev

# View logs
poetry run zappa tail dev

# Remove all AWS resources
poetry run zappa undeploy dev
```

### Working Endpoints
- **Root**: https://py4cwe15d0.execute-api.us-east-1.amazonaws.com/dev/
- **Health**: https://py4cwe15d0.execute-api.us-east-1.amazonaws.com/dev/health
- **Admin Panel**: https://py4cwe15d0.execute-api.us-east-1.amazonaws.com/dev/admin/
- **Checkout Plans**: https://py4cwe15d0.execute-api.us-east-1.amazonaws.com/dev/api/checkout/plans
- **API Docs**: https://py4cwe15d0.execute-api.us-east-1.amazonaws.com/dev/docs

### Important Notes
1. The root endpoint "/" must return a valid response for Zappa deployment to succeed
2. All static files for Flask-Admin are served from CDN when IS_LAMBDA=true
3. Database connections work without VPC configuration using public RDS endpoint
4. Environment variables are managed in zappa_settings.json

### Next Steps
1. Configure custom domains with SSL certificates
2. Deploy staging and production environments
3. Set up VPC if needed for enhanced security
4. Configure CloudWatch alarms for monitoring

## Workflow Reminders

- Sempre atualize os testes em qualquer alteração do codigo
- Use Poetry para gerenciar dependências
- Deploy local com Zappa funciona perfeitamente no macOS
- Sempre teste os endpoints após o deploy
- Use `zappa tail` para monitorar logs em tempo real
- Flask-Admin requer configuração especial para funcionar no Lambda