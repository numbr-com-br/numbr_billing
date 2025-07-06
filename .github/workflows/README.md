# GitHub Actions Configuration for Numbr Billing

## Required Secrets

Configure these secrets in your GitHub repository settings:

### Authentication & API Keys
- `AWS_ACCESS_KEY_ID` - AWS access key for deployment
- `AWS_SECRET_ACCESS_KEY` - AWS secret access key
- `ASAAS_API_KEY_DEV` - Asaas API key for development
- `ASAAS_API_KEY_STAGING` - Asaas API key for staging
- `ASAAS_API_KEY_PROD` - Asaas API key for production
- `ASAAS_WEBHOOK_TOKEN` - Asaas webhook token for signature validation
- `JWT_SECRET_KEY` - Secret key for JWT tokens

## Required Variables

Configure these variables in your GitHub repository settings:

### Database URLs
- `DATABASE_URL_DEV` - MySQL connection string for development
- `DATABASE_URL_STAGING` - MySQL connection string for staging
- `DATABASE_URL_PROD` - MySQL connection string for production

**Note**: Use `mysql://` format. The workflow automatically converts to `mysql+pymysql://`.

### API Configuration
- `ASAAS_API_URL` - Asaas API base URL (e.g., `https://sandbox.asaas.com/api/v3`)

### VPC Configuration (Optional but recommended for RDS access)
- `VPC_SUBNET_IDS` - Comma-separated list of subnet IDs (e.g., `subnet-xxx,subnet-yyy`)
- `VPC_SECURITY_GROUP_IDS` - Comma-separated list of security group IDs (e.g., `sg-xxx,sg-yyy`)

## Deployment Process

The workflow is triggered on pushes to:
- `develop` → deploys to `dev` environment
- `staging` → deploys to `staging` environment
- `main` → deploys to `prod` environment

### Workflow Steps

1. **Test Job**
   - Sets up Python 3.11 and Poetry
   - Installs dependencies
   - Runs tests with MySQL service container
   - Executes database migrations for test environment

2. **Deploy Job** (runs after tests pass)
   - Configures AWS credentials
   - Updates Zappa settings with environment variables
   - Runs database migrations
   - Deploys/updates Lambda function
   - Seeds admin data if needed
   - Tests deployment health

## Troubleshooting

### Common Issues

1. **VPC Access Issues**
   - Ensure `VPC_SUBNET_IDS` and `VPC_SECURITY_GROUP_IDS` are correctly configured
   - Lambda function needs to be in the same VPC as your RDS instance

2. **Database Connection Errors**
   - Verify DATABASE_URL format (should start with `mysql://`)
   - Check security group allows connections from Lambda

3. **Deployment Failures**
   - Check S3 bucket exists and has correct permissions
   - Verify AWS credentials have necessary permissions
   - Ensure Zappa version matches between local and CI/CD

### Required AWS Permissions

The AWS IAM user/role needs permissions for:
- Lambda (create, update, invoke functions)
- API Gateway (create, update APIs)
- S3 (read/write to deployment buckets)
- CloudFormation (manage stacks)
- IAM (create/update execution roles)
- CloudWatch Logs (create log groups)

## Local Testing

To test the deployment configuration locally:

```bash
# Test update script
./scripts/update_zappa_settings.py dev

# Test deployment (dry run)
poetry run zappa status dev
```