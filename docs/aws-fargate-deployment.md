# Deploying MiniPAM to AWS Fargate

This guide walks through deploying MiniPAM as a publicly accessible service on AWS Fargate.

## Overview

We'll deploy MiniPAM using:
- **AWS Fargate** for serverless container hosting
- **Application Load Balancer (ALB)** for public HTTPS access
- **Amazon ECR** for container registry
- **EFS or S3** for persistent storage (optional)
- **AWS Certificate Manager** for SSL/TLS

## Prerequisites

- AWS CLI configured with appropriate credentials
- Docker installed locally
- An AWS account with appropriate permissions
- A domain name (optional, for HTTPS)

## Step 1: Prepare the Docker Image

First, ensure the Dockerfile is optimized for production:

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY webui/dist/ ./webui/dist/

# Create data directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "src.minipam.main", "--config", "/app/config/config.yaml"]
```

## Step 2: Create ECR Repository and Push Image

```bash
# Create ECR repository
aws ecr create-repository --repository-name minipam --region us-east-1

# Get login token
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com

# Build and tag image
docker build -t minipam .
docker tag minipam:latest $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com/minipam:latest

# Push image
docker push $(aws sts get-caller-identity --query Account --output text).dkr.ecr.us-east-1.amazonaws.com/minipam:latest
```

## Step 3: Create Task Definition

Create `fargate-task-definition.json`:

```json
{
  "family": "minipam",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "256",
  "memory": "512",
  "containerDefinitions": [
    {
      "name": "minipam",
      "image": "${AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/minipam:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "MINIPAM_SERVER_HOST",
          "value": "0.0.0.0"
        },
        {
          "name": "MINIPAM_SERVER_PORT",
          "value": "8000"
        },
        {
          "name": "MINIPAM_STORAGE_TYPE",
          "value": "file"
        },
        {
          "name": "MINIPAM_STORAGE_PATH",
          "value": "/app/data"
        },
        {
          "name": "MINIPAM_AUTH_BACKEND",
          "value": "none"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/minipam",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      },
      "essential": true
    }
  ]
}
```

Register the task definition:

```bash
# Create log group
aws logs create-log-group --log-group-name /ecs/minipam --region us-east-1

# Register task definition
aws ecs register-task-definition --cli-input-json file://fargate-task-definition.json --region us-east-1
```

## Step 4: Create VPC and Security Groups

```bash
# Create VPC (or use existing)
VPC_ID=$(aws ec2 create-vpc --cidr-block 10.0.0.0/16 --query 'Vpc.VpcId' --output text)

# Create public subnets in 2 AZs
SUBNET_1=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.1.0/24 --availability-zone us-east-1a --query 'Subnet.SubnetId' --output text)
SUBNET_2=$(aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.2.0/24 --availability-zone us-east-1b --query 'Subnet.SubnetId' --output text)

# Create Internet Gateway
IGW_ID=$(aws ec2 create-internet-gateway --query 'InternetGateway.InternetGatewayId' --output text)
aws ec2 attach-internet-gateway --internet-gateway-id $IGW_ID --vpc-id $VPC_ID

# Create route table
ROUTE_TABLE_ID=$(aws ec2 create-route-table --vpc-id $VPC_ID --query 'RouteTable.RouteTableId' --output text)
aws ec2 create-route --route-table-id $ROUTE_TABLE_ID --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW_ID
aws ec2 associate-route-table --subnet-id $SUBNET_1 --route-table-id $ROUTE_TABLE_ID
aws ec2 associate-route-table --subnet-id $SUBNET_2 --route-table-id $ROUTE_TABLE_ID

# Create security group for ALB
ALB_SG=$(aws ec2 create-security-group --group-name minipam-alb-sg --description "Security group for MiniPAM ALB" --vpc-id $VPC_ID --query 'GroupId' --output text)
aws ec2 authorize-security-group-ingress --group-id $ALB_SG --protocol tcp --port 80 --cidr 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id $ALB_SG --protocol tcp --port 443 --cidr 0.0.0.0/0

# Create security group for Fargate tasks
TASK_SG=$(aws ec2 create-security-group --group-name minipam-task-sg --description "Security group for MiniPAM tasks" --vpc-id $VPC_ID --query 'GroupId' --output text)
aws ec2 authorize-security-group-ingress --group-id $TASK_SG --protocol tcp --port 8000 --source-group $ALB_SG
```

## Step 5: Create Application Load Balancer

```bash
# Create ALB
ALB_ARN=$(aws elbv2 create-load-balancer \
  --name minipam-alb \
  --subnets $SUBNET_1 $SUBNET_2 \
  --security-groups $ALB_SG \
  --query 'LoadBalancers[0].LoadBalancerArn' \
  --output text)

# Create target group
TG_ARN=$(aws elbv2 create-target-group \
  --name minipam-targets \
  --protocol HTTP \
  --port 8000 \
  --vpc-id $VPC_ID \
  --target-type ip \
  --health-check-path /api/v1/health/ready \
  --query 'TargetGroups[0].TargetGroupArn' \
  --output text)

# Create listener
aws elbv2 create-listener \
  --load-balancer-arn $ALB_ARN \
  --protocol HTTP \
  --port 80 \
  --default-actions Type=forward,TargetGroupArn=$TG_ARN
```

## Step 6: Create ECS Cluster and Service

```bash
# Create ECS cluster
aws ecs create-cluster --cluster-name minipam-cluster --region us-east-1

# Create service
aws ecs create-service \
  --cluster minipam-cluster \
  --service-name minipam-service \
  --task-definition minipam:1 \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_1,$SUBNET_2],securityGroups=[$TASK_SG],assignPublicIp=ENABLED}" \
  --load-balancers targetGroupArn=$TG_ARN,containerName=minipam,containerPort=8000 \
  --region us-east-1
```

## Step 7: Get the Public URL

```bash
# Get ALB DNS name
ALB_DNS=$(aws elbv2 describe-load-balancers --load-balancer-arns $ALB_ARN --query 'LoadBalancers[0].DNSName' --output text)
echo "MiniPAM is available at: http://$ALB_DNS"
```

## Optional: Add HTTPS with Custom Domain

1. **Request certificate in ACM**:
```bash
aws acm request-certificate --domain-name api.yourdomain.com --validation-method DNS
```

2. **Add HTTPS listener**:
```bash
aws elbv2 create-listener \
  --load-balancer-arn $ALB_ARN \
  --protocol HTTPS \
  --port 443 \
  --certificates CertificateArn=arn:aws:acm:us-east-1:123456789012:certificate/12345678-1234-1234-1234-123456789012 \
  --default-actions Type=forward,TargetGroupArn=$TG_ARN
```

3. **Create Route 53 record** pointing to the ALB

## Configuration for Production

### Environment Variables for Fargate

Update the task definition with production settings:

```json
"environment": [
  {
    "name": "MINIPAM_SERVER_HOST",
    "value": "0.0.0.0"
  },
  {
    "name": "MINIPAM_SERVER_PORT",
    "value": "8000"
  },
  {
    "name": "MINIPAM_STORAGE_TYPE",
    "value": "file"
  },
  {
    "name": "MINIPAM_AUTH_BACKEND",
    "value": "apikey"
  },
  {
    "name": "MINIPAM_AUTH_APIKEY_KEYS",
    "value": "your-secure-api-key-here"
  }
]
```

### Persistent Storage Options

#### Option 1: EFS (Recommended)
```json
"volumes": [
  {
    "name": "minipam-data",
    "efsVolumeConfiguration": {
      "fileSystemId": "fs-12345678",
      "rootDirectory": "/minipam"
    }
  }
],
"mountPoints": [
  {
    "sourceVolume": "minipam-data",
    "containerPath": "/app/data"
  }
]
```

#### Option 2: S3 Backend (Requires code modification)
Modify MiniPAM to support S3 as a storage backend.

## Monitoring and Logging

1. **CloudWatch Logs**: Already configured in task definition
2. **CloudWatch Metrics**: Monitor CPU, memory, and request count
3. **X-Ray**: Add AWS X-Ray for distributed tracing

## Cost Optimization

- Use Fargate Spot for non-production environments
- Set up auto-scaling based on CPU/memory metrics
- Use a smaller task size (256 CPU, 512 MB) for light workloads

## Security Best Practices

1. **Enable authentication**: Use API keys or OIDC
2. **Restrict CORS**: Update allow_origins to specific domains
3. **Use HTTPS**: Always use HTTPS in production
4. **Network isolation**: Place tasks in private subnets with NAT gateway
5. **Secrets management**: Use AWS Secrets Manager for sensitive data

## Quick Deploy Script

Create `deploy-to-fargate.sh`:

```bash
#!/bin/bash
set -e

# Configuration
AWS_REGION="us-east-1"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPO="minipam"
CLUSTER_NAME="minipam-cluster"
SERVICE_NAME="minipam-service"

# Build and push Docker image
echo "Building Docker image..."
docker build -t $ECR_REPO .

echo "Logging into ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

echo "Tagging and pushing image..."
docker tag $ECR_REPO:latest $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO:latest

# Update service
echo "Updating ECS service..."
aws ecs update-service --cluster $CLUSTER_NAME --service $SERVICE_NAME --force-new-deployment --region $AWS_REGION

echo "Deployment initiated! Check the AWS console for status."
```

## Estimated Costs

For a basic deployment:
- Fargate: ~$10-20/month (1 task, 0.25 vCPU, 0.5 GB memory)
- ALB: ~$20/month + data transfer
- Total: ~$30-40/month

## Troubleshooting

1. **Task fails to start**: Check CloudWatch logs
2. **Health checks failing**: Ensure `/api/v1/health/ready` returns 200
3. **Cannot connect**: Verify security groups and target group configuration
4. **CORS issues**: Ensure frontend URL is in allow_origins list

## Frontend Configuration

Once deployed, update your frontend to use the ALB URL:

```javascript
const API_BASE_URL = 'http://minipam-alb-123456789.us-east-1.elb.amazonaws.com/api/v1';
// or with custom domain
const API_BASE_URL = 'https://api.yourdomain.com/api/v1';
```