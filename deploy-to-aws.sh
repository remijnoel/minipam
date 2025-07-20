#!/bin/bash
set -e

# Configuration
AWS_REGION="us-east-1"
STACK_NAME="minipam-fargate"
REPO_NAME="minipam"
API_KEY="minipam-demo-key-$(date +%s)"

echo "🚀 Deploying MiniPAM to AWS Fargate..."

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
echo "📋 AWS Account ID: $AWS_ACCOUNT_ID"

# Step 1: Create ECR repository if it doesn't exist
echo "🏗️  Creating ECR repository..."
aws ecr describe-repositories --repository-names $REPO_NAME --region $AWS_REGION 2>/dev/null || \
aws ecr create-repository --repository-name $REPO_NAME --region $AWS_REGION

# Step 2: Build and push Docker image
echo "🐳 Building Docker image..."
docker build -f Dockerfile.production -t $REPO_NAME .

echo "🔐 Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

echo "📤 Pushing image to ECR..."
IMAGE_URI="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$REPO_NAME:latest"
docker tag $REPO_NAME:latest $IMAGE_URI
docker push $IMAGE_URI

# Step 3: Deploy CloudFormation stack
echo "☁️  Deploying CloudFormation stack..."
aws cloudformation deploy \
  --template-file aws/cloudformation-fargate.yaml \
  --stack-name $STACK_NAME \
  --parameter-overrides \
    DockerImageUri=$IMAGE_URI \
    ApiKeyValue=$API_KEY \
  --capabilities CAPABILITY_IAM \
  --region $AWS_REGION

# Step 4: Get outputs
echo "📊 Getting deployment information..."
STACK_OUTPUTS=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --region $AWS_REGION --query 'Stacks[0].Outputs')

API_URL=$(echo $STACK_OUTPUTS | jq -r '.[] | select(.OutputKey=="APIEndpoint") | .OutputValue')
HEALTH_URL=$(echo $STACK_OUTPUTS | jq -r '.[] | select(.OutputKey=="HealthCheckURL") | .OutputValue')

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 API Endpoint: $API_URL"
echo "❤️  Health Check: $HEALTH_URL"
echo "🔑 API Key: $API_KEY"
echo ""
echo "💡 Test the deployment:"
echo "   curl $HEALTH_URL"
echo ""
echo "🔧 For your frontend, use this base URL:"
echo "   $API_URL"
echo ""

# Wait for service to be ready
echo "⏳ Waiting for service to be healthy..."
sleep 30

# Test the deployment
echo "🧪 Testing deployment..."
if curl -s "$HEALTH_URL" | grep -q "ready"; then
    echo "✅ Service is healthy!"
else
    echo "⚠️  Service might still be starting up. Check the AWS console."
fi

echo ""
echo "🎉 MiniPAM is now publicly available!"
echo "   Update your frontend to use: $API_URL"