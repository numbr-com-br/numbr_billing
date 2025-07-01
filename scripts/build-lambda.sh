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
mkdir -p lambda-dist layer/nodejs

# Copy built application
cp -r dist/* lambda-dist/
cp package.json lambda-dist/
cp package-lock.json lambda-dist/

# Copy Prisma files
cp -r node_modules/.prisma lambda-dist/node_modules/
cp -r node_modules/@prisma/client lambda-dist/node_modules/@prisma/
cp -r prisma lambda-dist/

# Generate Prisma client
cd lambda-dist
npx prisma generate
cd ..

# Create layer with heavy dependencies
echo "Creating Lambda layer..."
LAYER_DEPS=(
  "@adminjs/design-system"
  "@adminjs/express" 
  "@adminjs/prisma"
  "adminjs"
  "express"
  "express-session"
  "@vendia/serverless-express"
  "axios"
)

# Copy layer dependencies
for dep in "${LAYER_DEPS[@]}"; do
  if [ -d "node_modules/$dep" ]; then
    cp -r "node_modules/$dep" "layer/nodejs/node_modules/$dep"
  fi
done

# Create layer package
cd layer
zip -r ../layer-package.zip . -q
cd ..

# Remove layer dependencies from main package
for dep in "${LAYER_DEPS[@]}"; do
  rm -rf "lambda-dist/node_modules/$dep"
done

# Copy remaining production dependencies
cd lambda-dist
npm ci --omit=dev --production
cd ..

# Remove unnecessary files
find lambda-dist -name "*.md" -delete
find lambda-dist -name "*.map" -delete
find lambda-dist -name "*.ts" -not -path "*/node_modules/*" -delete
find lambda-dist -name "test" -type d -exec rm -rf {} + 2>/dev/null || true
find lambda-dist -name "tests" -type d -exec rm -rf {} + 2>/dev/null || true
find lambda-dist -name ".git" -type d -exec rm -rf {} + 2>/dev/null || true

# Create Lambda deployment package
cd lambda-dist
zip -r ../lambda-package.zip . -q
cd ..

# Clean up
rm -rf lambda-dist layer

echo "Lambda package created:"
echo "  - lambda-package.zip ($(du -h lambda-package.zip | cut -f1))"
echo "  - layer-package.zip ($(du -h layer-package.zip | cut -f1))"