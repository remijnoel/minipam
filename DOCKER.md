# MiniPAM Docker Deployment Guide

This guide covers running MiniPAM using Docker for development and production environments.

## 🚀 Quick Start

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd minipam

# Start with Docker Compose
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop
docker-compose down
```

### Option 2: Docker Run

```bash
# Build and run
docker build -t minipam .
docker run -p 8000:8000 -v minipam-data:/app/data minipam
```

## 📁 File Structure

```
minipam/
├── Dockerfile              # Multi-stage build for production
├── docker-compose.yml      # Complete Docker Compose setup
├── docker-entrypoint.sh    # Container startup script
├── config.docker.yaml      # Docker-optimized configuration
├── test-docker.sh          # Docker setup validation
└── .dockerignore           # Docker build exclusions
```

## 🔧 Configuration

### Environment Variables

MiniPAM supports configuration through environment variables:

```bash
# Storage
MINIPAM_STORAGE_TYPE=file                    # "memory" or "file"
MINIPAM_STORAGE_FILE_PATH=/app/data/cidrs.json

# Server
MINIPAM_SERVER_HOST=0.0.0.0
MINIPAM_SERVER_PORT=8000
MINIPAM_SERVER_LOG_LEVEL=info

# Features
MINIPAM_DEBUG=false
```

### Custom Configuration File

Mount a custom config file:

```bash
# Create your config
cp config.docker.yaml my-config.yaml
# Edit my-config.yaml

# Run with custom config
docker run -p 8000:8000 \
  -v $(pwd)/my-config.yaml:/app/config.yaml:ro \
  -v minipam-data:/app/data \
  minipam
```

## 🏗️ Docker Compose Configurations

### Basic Setup

```yaml
services:
  minipam:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - minipam-data:/app/data
    environment:
      - MINIPAM_STORAGE_TYPE=file
      - MINIPAM_STORAGE_FILE_PATH=/app/data/cidrs.json
volumes:
  minipam-data:
```

### Production Setup

```yaml
services:
  minipam:
    build: .
    ports:
      - "80:8000"
    volumes:
      - minipam-data:/app/data
      - ./config.prod.yaml:/app/config.yaml:ro
    environment:
      - MINIPAM_STORAGE_TYPE=file
      - MINIPAM_STORAGE_FILE_PATH=/app/data/cidrs.json
      - MINIPAM_SERVER_LOG_LEVEL=warning
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/api/health', timeout=5)"]
      interval: 30s
      timeout: 10s
      retries: 3
volumes:
  minipam-data:
```

### Development Setup

```yaml
services:
  minipam:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - minipam-data:/app/data
      - ./src:/app/src  # Mount source for development
    environment:
      - MINIPAM_DEBUG=true
      - MINIPAM_SERVER_LOG_LEVEL=debug
      - MINIPAM_STORAGE_TYPE=file
      - MINIPAM_STORAGE_FILE_PATH=/app/data/cidrs.json
volumes:
  minipam-data:
```

## 🔍 Health Checks

The Docker image includes comprehensive health checks:

```bash
# Check container health
docker ps
docker inspect minipam | grep -A 10 "Health"

# Manual health check
curl http://localhost:8000/api/health
```

## 💾 Data Persistence

### File-based Storage

```bash
# Create named volume
docker volume create minipam-data

# Run with persistent storage
docker run -d \
  --name minipam \
  -p 8000:8000 \
  -v minipam-data:/app/data \
  -e MINIPAM_STORAGE_TYPE=file \
  -e MINIPAM_STORAGE_FILE_PATH=/app/data/cidrs.json \
  minipam

# Backup data
docker cp minipam:/app/data/cidrs.json backup-$(date +%Y%m%d).json

# Restore data
docker cp backup-20231201.json minipam:/app/data/cidrs.json
docker restart minipam
```

### Host Directory Mount

```bash
# Create local data directory
mkdir -p ./data

# Run with host directory
docker run -d \
  --name minipam \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -e MINIPAM_STORAGE_TYPE=file \
  -e MINIPAM_STORAGE_FILE_PATH=/app/data/cidrs.json \
  minipam
```

## 🛠️ Troubleshooting

### Common Issues

1. **Permission Errors**

   ```bash
   # Fix data directory permissions
   sudo chown -R 1000:1000 ./data
   ```

2. **Port Already in Use**

   ```bash
   # Use different port
   docker run -p 8080:8000 minipam
   ```

3. **Container Won't Start**

   ```bash
   # Check logs
   docker logs minipam
   ```

### Debug Mode

```bash
# Run in debug mode
docker run -p 8000:8000 \
  -e MINIPAM_DEBUG=true \
  -e MINIPAM_SERVER_LOG_LEVEL=debug \
  minipam

# Or with Docker Compose
MINIPAM_DEBUG=true docker-compose up
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
./test-docker.sh
```

This will:

- Build the Docker image
- Test basic functionality
- Validate health endpoints
- Test API endpoints
- Test web UI
- Test Docker Compose setup

## 🌐 Networking

### Reverse Proxy Setup

#### Nginx

```nginx
server {
    listen 80;
    server_name ipam.yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### Traefik

```yaml
version: '3.8'
services:
  minipam:
    build: .
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.minipam.rule=Host(`ipam.yourdomain.com`)"
      - "traefik.http.routers.minipam.entrypoints=websecure"
      - "traefik.http.routers.minipam.tls.certresolver=letsencrypt"
      - "traefik.http.services.minipam.loadbalancer.server.port=8000"
```

## 🔐 Security

### Production Security

1. **Use specific CORS origins**

   ```yaml
   environment:
     - MINIPAM_CORS_ORIGINS=["https://ipam.yourdomain.com"]
   ```

2. **Run behind reverse proxy**

   ```yaml
   ports:
     - "127.0.0.1:8000:8000"  # Bind to localhost only
   ```

3. **Use secrets for sensitive data**

   ```yaml
   secrets:
     - minipam_config
   ```

## 📊 Monitoring

### Container Metrics

```bash
# Resource usage
docker stats minipam

# Container info
docker inspect minipam

# Process list
docker exec minipam ps aux
```

### Application Metrics

```bash
# Health check
curl http://localhost:8000/api/health

# API status
curl http://localhost:8000/api/cidrs/

# Application logs
docker logs -f minipam
```

## 🔄 Updates

### Update Container

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Rolling Updates

```bash
# Build new image
docker build -t minipam:new .

# Stop old container
docker stop minipam

# Start new container
docker run -d \
  --name minipam-new \
  -p 8000:8000 \
  -v minipam-data:/app/data \
  minipam:new

# Remove old container
docker rm minipam
docker rename minipam-new minipam
```
