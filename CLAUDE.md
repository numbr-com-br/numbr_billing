# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Numbr Billing is a complete SaaS billing system with Asaas payment gateway integration, featuring an AdminJS administrative panel and transparent checkout flow.

## Key Commands

### Development
```bash
npm run dev                    # Start development server with hot reload (nodemon)
npm run build                  # Build TypeScript to dist/
npm start                      # Run production build
```

### Database & Prisma
```bash
npm run prisma:generate        # Generate Prisma client
npm run prisma:migrate        # Run migrations (development)
npm run prisma:migrate:test   # Deploy migrations to test database
npm run prisma:studio         # Open Prisma Studio GUI
```

### Testing
```bash
npm test                       # Run all tests with coverage
npm run test:watch            # Run tests in watch mode
npm run test:coverage         # Generate coverage report
npm run test:unit             # Run only unit tests
npm run test:integration      # Run only integration tests

# Run a single test file
npx jest tests/unit/services/asaas.service.test.ts

# Run tests matching a pattern
npx jest --testNamePattern="should create a customer"
```

### Code Quality
```bash
npm run lint                   # Run ESLint
npm run format                 # Format code with Prettier
```

## Architecture

### Core Services Integration

The application integrates three main systems:

1. **Asaas Payment Gateway** (`src/services/asaas.service.ts`)
   - Handles customer creation, subscription management, and payment processing
   - All Asaas API calls are centralized in this service
   - Webhook events from Asaas are processed to update local database state

2. **AdminJS Panel** (`src/admin/`)
   - Automatic CRUD generation based on Prisma models
   - Custom dashboard with business metrics (MRR, active subscriptions)
   - Resources configuration in `admin/resources.ts` defines UI behavior for each model

3. **Database Models** (`prisma/schema.prisma`)
   - MySQL database with enums for type safety
   - Relationships: Customer → Subscription → Payment
   - Plan and Addon models for flexible pricing
   - WebhookLog for audit trail

### Request Flow

1. **Checkout Flow** (`src/routes/checkout.route.ts`)
   - Customer selects plan + addons → Creates/finds customer in Asaas → Creates subscription → Generates payment link
   - Maintains local database records synchronized with Asaas

2. **Webhook Processing** (`src/webhooks/asaas.webhook.ts`)
   - Validates webhook token
   - Maps Asaas payment statuses to local enums
   - Updates subscription status based on payment events
   - Logs all webhook events for debugging

### Environment Configuration

The app uses different `.env` files:
- `.env` - Development/production configuration
- `.env.test` - Test database and mock API keys
- Required: `DATABASE_URL`, `ASAAS_API_KEY`, `ASAAS_WEBHOOK_TOKEN`

### Testing Strategy

- **Unit Tests**: Mock external services (Asaas API, Prisma)
- **Integration Tests**: Use real database with cleanup between tests
- **Test Helpers**: Factory functions in `tests/helpers/factories.ts` for data generation
- Database cleanup in `tests/setup.ts` handles MySQL foreign key constraints

### AdminJS Authentication

Simple email/password authentication configured in `app.ts`:
- Credentials from environment variables
- Session-based authentication with express-session
- No user management UI - single admin user

### Key Design Decisions

1. **ESM Modules**: Project uses `"type": "module"` with `.js` extensions in imports
2. **Prisma DMMF**: AdminJS requires access to Prisma's internal metadata (`_dmmf`)
3. **Decimal Handling**: Prices stored as Decimal type, converted to number for calculations
4. **Status Mapping**: Asaas payment statuses mapped to simplified internal enum
5. **MRR Calculation**: Converts all billing cycles to monthly equivalent in dashboard

## Important Notes

- Always run `npm run prisma:generate` after schema changes
- Test database must exist before running tests
- Asaas sandbox API for development, production API requires real credentials
- AdminJS runs on `/admin` route with authentication
- Webhook endpoint `/webhooks/asaas` must be accessible to Asaas servers

## AWS Lambda Deployment

The project supports deployment to AWS Lambda with API Gateway:

### Key Files for Lambda
- `src/lambda.ts` - Serverless Express handler
- `cloudformation/template.yaml` - SAM/CloudFormation template
- `scripts/build-lambda.sh` - Build script for Lambda packages
- `.github/workflows/deploy.yml` - Automated deployment pipeline

### Environment Detection
- `process.env.IS_LAMBDA` - Set by CloudFormation to detect Lambda environment
- App doesn't call `listen()` when running in Lambda
- Database connections should use RDS Proxy for better Lambda performance

### Deployment Flow
1. Push to branch (develop/staging/main) triggers GitHub Actions
2. Tests run first, then build and package for Lambda
3. CloudFormation deploys/updates the stack
4. Lambda function and layer are updated with new code

### Lambda Considerations
- AdminJS static assets are served through Lambda (may be slower)
- Sessions use in-memory store (not shared across Lambda instances)
- Consider using DynamoDB or Redis for session persistence in production
- Prisma connection pooling should be adjusted for Lambda cold starts

## Workflow Reminders

- Sempre atualize os testes em qualquer alteração do codigo