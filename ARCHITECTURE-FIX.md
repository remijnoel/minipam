# Architecture Fix for ECS Deployment

## Problem
The "Exec format error" in CloudWatch logs indicates that you're building Docker images on Apple Silicon (ARM64) but AWS Fargate runs on AMD64 (x86_64) architecture.

## Solution
The Makefile has been updated to automatically build for the correct architecture.

## Updated Commands

### For ECS Deployment
```bash
# This now builds for AMD64 automatically
make redeploy
```

### For Local Testing
```bash
# This builds for your native architecture (ARM64 on Mac)
make local
```

## What Changed

1. **Main build target**: Now uses `docker buildx` with `--platform linux/amd64`
2. **Fallback**: If buildx isn't available, uses `DOCKER_DEFAULT_PLATFORM=linux/amd64`
3. **Separate local build**: `build-local` target for native architecture testing

## Architecture Details

- **Your Mac**: ARM64 (Apple Silicon)
- **AWS Fargate**: AMD64 (x86_64)
- **Solution**: Cross-platform build using Docker buildx

## Verify the Fix

After running `make redeploy`, check CloudWatch logs:
- ✅ **Success**: Application starts normally
- ❌ **Still failing**: "Exec format error" means architecture mismatch

## Manual Architecture Check

```bash
# Check what architecture your image was built for
docker inspect minipam-dev:latest | grep Architecture

# Should show: "Architecture": "amd64"
```

## Troubleshooting

If you still get architecture errors:

1. **Clean and rebuild**:
   ```bash
   make clean
   make redeploy
   ```

2. **Check Docker buildx**:
   ```bash
   docker buildx version
   docker buildx ls
   ```

3. **Manual build for AMD64**:
   ```bash
   docker buildx build --platform linux/amd64 -f Dockerfile.dev -t minipam-dev:latest --load .
   ```

## Alternative: Use GitHub Actions

For guaranteed AMD64 builds, consider using GitHub Actions to build and push to ECR from a Linux runner.

## Future Prevention

Always build for AMD64 when deploying to AWS:
- ECS Fargate: AMD64
- Lambda (container): AMD64  
- EC2: Usually AMD64 (unless specifically ARM instances)