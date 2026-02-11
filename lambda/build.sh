#!/bin/bash

# Build Lambda deployment package
# This script packages the Lambda function with dependencies

echo "Building Lambda deployment package..."

# Create temp directory
TEMP_DIR=$(mktemp -d)
echo "Using temp directory: $TEMP_DIR"

# Copy Lambda function
cp lambda_function.py $TEMP_DIR/

# Install dependencies
if [ -f requirements.txt ]; then
    echo "Installing dependencies for AWS Lambda (Linux x86_64)..."
    pip install \
        --platform manylinux2014_x86_64 \
        --target $TEMP_DIR/ \
        --implementation cp \
        --python-version 3.12 \
        --only-binary=:all: --upgrade \
        -r requirements.txt
fi

# Create zip file
cd $TEMP_DIR
zip -r lambda_function.zip .
cd -

# Move zip to terraform directory
mv $TEMP_DIR/lambda_function.zip ../terraform/

# Cleanup
rm -rf $TEMP_DIR

echo "Lambda package created: ../terraform/lambda_function.zip"
