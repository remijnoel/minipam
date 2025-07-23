# MiniPAM Development Guide

## Quick Start

### First Time Setup
```bash
# Deploy to AWS Fargate for the first time
make first-deploy

# Get your API URL
make status
```

### Daily Development Workflow
```bash
# Make code changes...

# Quick redeploy with latest code
make redeploy

# Check status and get URLs
make status

# View logs
make logs

# Test the deployment
make test
```

### Local Development
```bash
# Run locally with Docker
make local

# Get shell access to container
make shell
```

## Available Commands

| Command | Description |
|---------|-------------|
| `make help` | Show all available commands |
| `make deploy` | Full deployment (first time) |
| `make redeploy` | Quick redeploy with latest code |
| `make status` | Show deployment status and URLs |
| `make logs` | Show recent application logs |
| `make test` | Run tests against deployed service |
| `make local` | Run locally with Docker |
| `make clean` | Clean up local Docker images |
| `make destroy` | Destroy the deployment |

## Development Features

### Pre-loaded Sample Data
The development Docker image comes with sample CIDR data:
- Hierarchical network structure
- Structured tags (vlan, location, device, customer)
- Multiple network types (corporate, DMZ, development, office)

### Development Configuration
- Debug mode enabled
- CORS enabled for all origins
- File-based storage with persistence
- No authentication required

### Quick Iteration
The `make redeploy` command:
1. Builds the latest Docker image
2. Pushes to ECR
3. Forces ECS to deploy the new image
4. Waits for deployment to complete

## API Endpoints

After deployment, your API will be available at:
- **Base URL**: `http://your-alb-url.amazonaws.com/api/v1`
- **Health Check**: `http://your-alb-url.amazonaws.com/api/v1/health/ready`
- **CIDR Tree**: `http://your-alb-url.amazonaws.com/api/v1/cidrs/tree`

## Frontend Integration

Update your Lovable frontend to use the deployed API:

```javascript
// Get your API URL from 'make status'
const API_BASE_URL = 'http://minipam-dev-alb-123456789.us-east-1.elb.amazonaws.com/api/v1';

// Test connection
fetch(`${API_BASE_URL}/health/ready`)
  .then(response => response.json())
  .then(data => console.log('Backend healthy:', data));

// Get CIDR tree
fetch(`${API_BASE_URL}/cidrs/tree`)
  .then(response => response.json())
  .then(data => console.log('CIDR tree:', data));
```

## Troubleshooting

### Common Issues

1. **AWS CLI not configured**
   ```bash
   aws configure
   # or
   export AWS_PROFILE=your-profile
   ```

2. **Service not starting**
   ```bash
   make logs  # Check application logs
   ```

3. **Health check failing**
   - Wait a few minutes for container to start
   - Check logs for errors
   - Verify image builds correctly with `make local`

4. **Cannot connect to API**
   - Check security groups allow inbound traffic
   - Verify ALB target group health

### Manual AWS Console Access

- **ECS Service**: AWS Console → ECS → Clusters → minipam-dev-cluster
- **Load Balancer**: AWS Console → EC2 → Load Balancers → minipam-dev-alb
- **Logs**: AWS Console → CloudWatch → Log Groups → /ecs/minipam-dev

## Cost Optimization

Development environment costs approximately:
- **Fargate**: ~$10-15/month (1 task, 0.25 vCPU, 0.5 GB)
- **ALB**: ~$20/month
- **Total**: ~$30-35/month

To minimize costs:
- Use `make destroy` when not actively developing
- The stack can be redeployed quickly with `make deploy`

## Next Steps

1. **Set up CI/CD**: Automate deployments on code changes
2. **Add HTTPS**: Configure SSL certificate for production-like testing
3. **Add monitoring**: Set up CloudWatch dashboards
4. **Environment variables**: Configure different settings per environment