# MiniPAM ECS Quick Deploy Guide

## Prerequisites

- AWS CLI configured
- Docker installed
- Existing ECS cluster: `minipam-dev-cluster`
- Existing ECS service: `minipam-dev-service`
- ECR repository: `minipam-dev`

## Quick Commands

### 🚀 Deploy Latest Code
```bash
# This is the main command you'll use
make redeploy
```

This single command:
1. Builds the Docker image
2. Pushes to ECR with `latest` tag
3. Forces ECS to redeploy the service
4. Waits for deployment to complete

### 📊 Check Status
```bash
# Get deployment status
make status

# Get the API URL
make get-url
```

### 🛠️ Other Useful Commands

```bash
# View logs
make logs

# Stop service (save costs)
make stop-service

# Start service again
make start-service

# Run locally for testing
make local

# Check everything is working
make check
```

## Workflow Example

1. **Make code changes**

2. **Deploy to ECS**:
   ```bash
   make redeploy
   ```

3. **Get your API URL**:
   ```bash
   make get-url
   ```
   
   Output will show:
   ```
   🌐 API Endpoints:
     Base URL: http://minipam-dev-alb-123456.us-west-2.elb.amazonaws.com
     API: http://minipam-dev-alb-123456.us-west-2.elb.amazonaws.com/api/v1
     Health: http://minipam-dev-alb-123456.us-west-2.elb.amazonaws.com/api/v1/health/ready
   ```

4. **Share with frontend developer**:
   Give them the API URL for integration

## Configuration

The Makefile uses these defaults:
- **Region**: `us-west-2` (change with `AWS_REGION=us-east-1 make redeploy`)
- **Cluster**: `minipam-dev-cluster`
- **Service**: `minipam-dev-service`
- **ECR Repo**: `minipam-dev`

## Cost Saving

When not actively developing:
```bash
# Stop the service
make stop-service

# Later, start it again
make start-service
```

## Troubleshooting

If deployment fails:
```bash
# Check service status
make status

# View recent logs
make logs

# Validate configuration
make check
```

## Notes

- Always uses `latest` tag for simplicity
- Each `make redeploy` forces a new deployment
- No CloudFormation required
- Direct ECS service updates only