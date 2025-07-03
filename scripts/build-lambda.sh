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

# Copy built application
cp -r dist lambda-dist/
cp package.json lambda-dist/
cp package-lock.json lambda-dist/

# Copy lambda wrapper
cp src/lambda-wrapper.js lambda-dist/dist/

# Create a package.json that supports mixed modules for Lambda
cd lambda-dist
node -e "
const p = require('./package.json');
// Remove type: module to allow mixed CommonJS/ES modules
delete p.type;
// Add exports configuration
p.exports = {
  '.': {
    'import': './dist/app.js',
    'require': './dist/app.js'
  }
};
require('fs').writeFileSync('./package.json', JSON.stringify(p, null, 2));
"
cd ..

# Copy Prisma schema
cp -r prisma lambda-dist/

# Install production dependencies in lambda-dist
cd lambda-dist
npm ci --omit=dev --no-fund --no-audit
cd ..

# Generate Prisma client
cd lambda-dist
npx prisma generate --generator client
cd ..

# Remove Prisma CLI which is not needed at runtime
rm -rf lambda-dist/node_modules/prisma
rm -rf lambda-dist/node_modules/.bin/prisma

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
  "@prisma/client"
  "@prisma/engines"
  ".prisma"
)

# Move layer dependencies
for dep in "${LAYER_DEPS[@]}"; do
  if [ -d "lambda-dist/node_modules/$dep" ]; then
    parent_dir=$(dirname "$dep")
    if [ "$parent_dir" != "." ]; then
      mkdir -p "layer/nodejs/node_modules/$parent_dir"
    fi
    mv "lambda-dist/node_modules/$dep" "layer/nodejs/node_modules/$dep"
  fi
done

# Create layer package
if [ -d "layer/nodejs/node_modules" ] && [ "$(ls -A layer/nodejs/node_modules)" ]; then
  cd layer
  zip -r ../layer-package.zip . -q
  cd ..
  echo "Layer package created"
else
  echo "No dependencies for layer, skipping layer creation"
fi

# Remove unnecessary files
find lambda-dist -name "*.md" -delete 2>/dev/null || true
find lambda-dist -name "*.map" -delete 2>/dev/null || true
find lambda-dist -name "*.ts" -not -path "*/node_modules/*" -delete 2>/dev/null || true
find lambda-dist -name "test" -type d -exec rm -rf {} + 2>/dev/null || true
find lambda-dist -name "tests" -type d -exec rm -rf {} + 2>/dev/null || true
find lambda-dist -name ".git" -type d -exec rm -rf {} + 2>/dev/null || true
find lambda-dist -name "*.d.ts" -not -path "*/node_modules/@types/*" -not -path "*/@prisma/*" -delete 2>/dev/null || true
find lambda-dist -name "*.flow" -delete 2>/dev/null || true
find lambda-dist -name "docs" -type d -exec rm -rf {} + 2>/dev/null || true
find lambda-dist -name "example" -type d -exec rm -rf {} + 2>/dev/null || true
find lambda-dist -name "examples" -type d -exec rm -rf {} + 2>/dev/null || true
rm -rf lambda-dist/node_modules/*/node_modules/.bin 2>/dev/null || true

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