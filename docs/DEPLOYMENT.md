# MiniPAM Deployment Guide

This document provides instructions for deploying MiniPAM in production environments.

## Deployment Options

### 1. Docker Deployment (Recommended)

#### Using Docker Compose

```bash
# Clone repository
git clone https://github.com/remijnoel/minipam.git
cd minipam

# Create production configuration
cp config.yaml.example config.yaml
# Edit config.yaml with your settings

# Start services
docker-compose up -d

# Check status
docker-compose ps
docker-compose logs -f
```

#### Using Docker Run

```bash
# Build image
docker build -t minipam .

# Run container
docker run -d \
  --name minipam \
  -p 8000:8000 \
  -v minipam-data:/app/data \
  -v ./config.yaml:/etc/minipam/config.yaml:ro \
  -e MINIPAM_STORAGE_TYPE=file \
  -e MINIPAM_STORAGE_PATH=/app/data \
  minipam
```

### 2. Kubernetes Deployment

#### Basic Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: minipam
spec:
  replicas: 2
  selector:
    matchLabels:
      app: minipam
  template:
    metadata:
      labels:
        app: minipam
    spec:
      containers:
      - name: minipam
        image: minipam:latest
        ports:
        - containerPort: 8000
        env:
        - name: MINIPAM_STORAGE_TYPE
          value: "file"
        - name: MINIPAM_STORAGE_PATH
          value: "/data"
        livenessProbe:
          httpGet:
            path: /api/v1/health/live
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /api/v1/health/ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: data
          mountPath: /data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: minipam-data
---
apiVersion: v1
kind: Service
metadata:
  name: minipam-service
spec:
  selector:
    app: minipam
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

#### Persistent Volume Claim

```yaml
# pvc.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: minipam-data
spec:
  accessModes:
  - ReadWriteOnce
  resources:
    requests:
      storage: 1Gi
```

### 3. Systemd Service

#### Installation

```bash
# Install MiniPAM
pip install minipam

# Create service user
sudo useradd -r -s /bin/false minipam

# Create directories
sudo mkdir -p /etc/minipam /var/lib/minipam
sudo chown minipam:minipam /var/lib/minipam

# Create configuration
sudo cp config.yaml.example /etc/minipam/config.yaml
# Edit /etc/minipam/config.yaml
```

#### Service Configuration

```ini
# /etc/systemd/system/minipam.service
[Unit]
Description=MiniPAM IPAM Service
After=network.target

[Service]
Type=simple
User=minipam
Group=minipam
WorkingDirectory=/var/lib/minipam
Environment=MINIPAM_STORAGE_PATH=/var/lib/minipam/data
ExecStart=/usr/local/bin/minipam serve --config /etc/minipam/config.yaml
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Service Management

```bash
# Enable and start service
sudo systemctl enable minipam
sudo systemctl start minipam

# Check status
sudo systemctl status minipam

# View logs
sudo journalctl -u minipam -f
```

## Configuration

### Environment Variables

All configuration can be overridden with environment variables:

```bash
# Server configuration
MINIPAM_SERVER_HOST=0.0.0.0
MINIPAM_SERVER_PORT=8000
MINIPAM_SERVER_DEBUG=false

# Storage configuration
MINIPAM_STORAGE_TYPE=file
MINIPAM_STORAGE_PATH=/var/lib/minipam/data

# Authentication configuration
MINIPAM_AUTH_BACKEND=oidc
MINIPAM_AUTH_OIDC_ISSUER_URL=https://auth.example.com
MINIPAM_AUTH_OIDC_CLIENT_ID=minipam-prod
MINIPAM_AUTH_OIDC_CLIENT_SECRET=your-secret
```

### Configuration Files

#### Basic Configuration

```yaml
# config.yaml
server:
  host: "0.0.0.0"
  port: 8000
  debug: false

storage:
  type: "file"
  path: "/var/lib/minipam/data"

auth:
  backend: "none"

ui:
  enabled: true
  path: "/ui"
```

#### API Key Authentication

```yaml
# config.yaml
auth:
  backend: "apikey"
  apikey:
    keys:
      - "your-production-api-key"
```

#### OIDC Authentication

```yaml
# config.yaml
auth:
  backend: "oidc"
  oidc:
    issuer_url: "https://auth.example.com"
    client_id: "minipam-prod"
    # Set client_secret via environment variable
    # MINIPAM_AUTH_OIDC_CLIENT_SECRET=your-secret
```

## Security Considerations

### Authentication

- **Never use NoAuth in production** - it's for development only
- Use OIDC for enterprise SSO integration
- Store API keys securely and rotate regularly
- Use environment variables for secrets, never config files

### Network Security

- Use HTTPS in production (reverse proxy with SSL termination)
- Restrict network access to authorized users only
- Consider IP allowlisting for sensitive environments

### Container Security

- Containers run as non-root user
- Use multi-stage builds for smaller attack surface
- Regularly update base images
- Scan images for vulnerabilities

### Data Security

- File storage uses atomic operations with locking
- Regular backups of data directory
- Secure file permissions (600 for data files)
- Consider encryption at rest for sensitive data

## Monitoring and Logging

### Health Checks

```bash
# Liveness check
curl http://localhost:8000/api/v1/health/live

# Readiness check
curl http://localhost:8000/api/v1/health/ready
```

### Logging

Configure logging levels via environment variables:

```bash
MINIPAM_SERVER_DEBUG=true  # Enable debug logging
```

### Metrics

Health endpoints provide basic metrics:

```json
{
  "status": "ready",
  "storage": {
    "type": "file",
    "status": "healthy",
    "total_blocks": 150
  }
}
```

## Backup and Recovery

### File Storage Backup

```bash
# Create backup
tar -czf minipam-backup-$(date +%Y%m%d).tar.gz /var/lib/minipam/data/

# Restore backup
tar -xzf minipam-backup-20231201.tar.gz -C /
sudo chown -R minipam:minipam /var/lib/minipam/data/
```

### Database Backup (Future)

When SQL backends are added:

```bash
# PostgreSQL backup
pg_dump minipam > minipam-backup.sql

# MySQL backup
mysqldump minipam > minipam-backup.sql
```

## Performance Tuning

### Resource Requirements

**Minimum Requirements:**
- CPU: 1 core
- Memory: 512MB
- Storage: 1GB

**Recommended for Production:**
- CPU: 2 cores
- Memory: 2GB
- Storage: 10GB

### Scaling

**Horizontal Scaling:**
- Run multiple instances behind load balancer
- Use shared storage (NFS, cloud storage)
- Consider eventual consistency

**Vertical Scaling:**
- Increase CPU/memory for higher concurrency
- Use SSD storage for better I/O performance

## Troubleshooting

### Common Issues

#### Service Won't Start

```bash
# Check logs
sudo journalctl -u minipam -f

# Check configuration
minipam config-show

# Test configuration
minipam --config /etc/minipam/config.yaml serve --dry-run
```

#### Health Check Failures

```bash
# Check service status
curl -v http://localhost:8000/api/v1/health/live

# Check storage
ls -la /var/lib/minipam/data/

# Check permissions
sudo -u minipam touch /var/lib/minipam/data/test
```

#### Authentication Issues

```bash
# Test API key
curl -H "Authorization: Bearer your-api-key" \
     http://localhost:8000/api/v1/cidrs

# Check OIDC configuration
curl https://your-oidc-provider/.well-known/jwks.json
```

### Debug Mode

Enable debug mode for detailed logging:

```bash
# Via environment variable
export MINIPAM_SERVER_DEBUG=true

# Via configuration file
echo "server:\n  debug: true" >> /etc/minipam/config.yaml
```

## Updating

### Docker Update

```bash
# Pull latest image
docker pull minipam:latest

# Update services
docker-compose down
docker-compose up -d
```

### Package Update

```bash
# Update package
pip install --upgrade minipam

# Restart service
sudo systemctl restart minipam
```

## Support

For deployment issues:

1. Check logs first
2. Verify configuration
3. Test health endpoints
4. Review security settings
5. Consult documentation

For additional support:
- GitHub Issues: https://github.com/remijnoel/minipam/issues
- Documentation: https://github.com/remijnoel/minipam/docs