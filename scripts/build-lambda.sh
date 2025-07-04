#!/bin/bash
set -e

ENV=$1
if [ -z "$ENV" ]; then
  echo "Usage: ./build-lambda.sh <env>"
  exit 1
fi

echo "Building Lambda package for environment: $ENV"

# Clean up previous builds
rm -rf lambda-dist layer lambda-package.zip layer-package.zip

# Create directories
mkdir -p lambda-dist/node_modules layer/nodejs/node_modules

# Copy package files first
cp package.json lambda-dist/
cp package-lock.json lambda-dist/

# Copy built application
cp -r dist/* lambda-dist/

# No wrapper needed

# Copy Prisma schema
cp -r prisma lambda-dist/

# Install production dependencies in lambda-dist
cd lambda-dist
npm ci --omit=dev --no-fund --no-audit

# Generate Prisma client with correct binary targets for Lambda
echo "Generating Prisma client for Lambda..."
# First, temporarily modify the schema to use the old generator for Lambda
sed -i.bak 's/provider = "prisma-client"/provider = "prisma-client-js"/' prisma/schema.prisma
sed -i.bak '/output/d' prisma/schema.prisma
sed -i.bak '/moduleFormat/d' prisma/schema.prisma
# Use node directly to avoid npx installing prisma
node node_modules/@prisma/client/scripts/postinstall.js
# Restore original schema
mv prisma/schema.prisma.bak prisma/schema.prisma
cd ..

# Skip layer creation - include all dependencies in Lambda package
echo "Skipping layer creation - all dependencies will be included in Lambda package"

# Create Lambda deployment package
cd lambda-dist
zip -r ../lambda-package.zip . -q
cd ..

# Clean up
rm -rf lambda-dist layer

echo "Lambda package created:"
echo "  - lambda-package.zip ($(du -h lambda-package.zip | cut -f1))"
if [ -f "layer-package.zip" ]; then
  echo "  - layer-package.zip ($(du -h layer-package.zip | cut -f1))"
fi