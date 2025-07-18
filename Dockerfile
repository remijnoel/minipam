# Multi-stage Docker build for MiniPAM

# Build stage
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt ./
COPY pyproject.toml ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY docs/ ./docs/
COPY README.md LICENSE ./

# Install the package (use version override for Docker build)
ENV SETUPTOOLS_SCM_PRETEND_VERSION="1.0.0"
RUN pip install -e .

# Production stage
FROM python:3.11-slim as production

# Create non-root user
RUN groupadd -r minipam && useradd -r -g minipam minipam

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy application source
COPY --from=builder /app/src/ ./src/
COPY --from=builder /app/README.md /app/LICENSE ./

# Create data directory
RUN mkdir -p /app/data && chown -R minipam:minipam /app/data

# Create config directory
RUN mkdir -p /etc/minipam && chown -R minipam:minipam /etc/minipam

# Switch to non-root user
USER minipam

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8000/api/v1/health/live')" || exit 1

# Default command
CMD ["minipam", "serve"]

# Development stage
FROM builder as development

# Install development dependencies
RUN pip install --no-cache-dir -r requirements-dev.txt

# Don't switch to non-root user in development
USER root

# Install additional development tools
RUN apt-get update && apt-get install -y \
    curl \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Development command
CMD ["minipam", "serve", "--debug"]