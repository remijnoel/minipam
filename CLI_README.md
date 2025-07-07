# MiniPAM CLI

Command-line interface for the MiniPAM CIDR Block Management Service.

## Installation

Install the package in development mode:

```bash
pip install -e .
```

Or install from requirements:

```bash
pip install -r requirements.txt
```

## Prerequisites

Make sure the MiniPAM API server is running:

```bash
# Start the API server
python -m minipam.main

# Or using uvicorn directly
uvicorn minipam.main:app --reload
```

## Usage

### Global Options

- `--api-url TEXT`: Base URL of the MiniPAM API (default: <http://localhost:8000>)
- `--format [table|json]`: Output format (default: table)
- `--help`: Show help message

### Commands

#### Health Check

Check the API server health status:

```bash
minipam health
```

Example output:

```
API Status: healthy
Backend: memory
```

#### List CIDR Blocks

List all CIDR blocks:

```bash
minipam list
```

With JSON output:

```bash
minipam --format json list
```

#### Get CIDR Block

Get details of a specific CIDR block:

```bash
minipam get 192.168.1.0/24
```

#### Create CIDR Block

Create a new CIDR block:

```bash
# Basic creation
minipam create 192.168.1.0/24

# With additional metadata
minipam create 192.168.1.0/24 \
  --name "Test Network" \
  --description "Development network" \
  --tag env=dev \
  --tag owner=devops

# With parent/child relationships
minipam create 192.168.1.0/24 \
  --parent 192.168.0.0/16 \
  --child 192.168.1.0/25 \
  --child 192.168.1.128/25
```

#### Update CIDR Block

Update an existing CIDR block:

```bash
# Update specific fields
minipam update 192.168.1.0/24 \
  --name "Updated Network" \
  --description "Updated description"

# Update tags
minipam update 192.168.1.0/24 \
  --tag env=production \
  --tag owner=network-team
```

#### Delete CIDR Block

Delete a CIDR block:

```bash
# With confirmation prompt
minipam delete 192.168.1.0/24

# Force deletion without confirmation
minipam delete 192.168.1.0/24 --force
```

## Examples

### Basic Workflow

```bash
# Check API health
minipam health

# Create a network
minipam create 10.0.0.0/16 --name "Corporate Network"

# Create subnets
minipam create 10.0.1.0/24 \
  --name "DMZ Network" \
  --parent 10.0.0.0/16 \
  --tag zone=dmz

minipam create 10.0.2.0/24 \
  --name "Internal Network" \
  --parent 10.0.0.0/16 \
  --tag zone=internal

# List all networks
minipam list

# Get specific network details
minipam get 10.0.1.0/24

# Update network
minipam update 10.0.1.0/24 \
  --description "DMZ for external services"

# Delete network
minipam delete 10.0.2.0/24
```

### JSON Output

For programmatic use, use JSON format:

```bash
# Get all networks as JSON
minipam --format json list

# Get specific network as JSON
minipam --format json get 10.0.1.0/24

# Parse with jq
minipam --format json list | jq '.[] | select(.tags.env == "production")'
```

### Different API Endpoints

Connect to different API servers:

```bash
# Production API
minipam --api-url https://ipam.company.com list

# Development API
minipam --api-url http://dev.company.com:8000 list

# Local API on different port
minipam --api-url http://localhost:8080 list
```

## Error Handling

The CLI provides clear error messages:

- **Connection errors**: When the API server is not reachable
- **HTTP errors**: When the API returns error responses
- **Validation errors**: When CIDR format is invalid
- **Not found errors**: When trying to access non-existent resources

## Return Codes

- `0`: Success
- `1`: General error (API error, validation error, etc.)
- `2`: Command usage error (invalid arguments, etc.)

## Environment Variables

You can set default values using environment variables:

```bash
export MINIPAM_API_URL=https://ipam.company.com
export MINIPAM_FORMAT=json

# Now you can use shorter commands
minipam list
```

## Development

### Running Tests

```bash
# Make sure API server is running
python -m minipam.main &

# Test CLI commands
minipam health
minipam create 192.168.1.0/24 --name "Test"
minipam list
minipam delete 192.168.1.0/24 --force
```

### Adding New Commands

The CLI is built with Click. To add new commands:

1. Add the command function to `src/minipam/cli.py`
2. Use the `@cli.command()` decorator
3. Add appropriate options and arguments
4. Update this README with documentation

### API Client

The CLI uses an `APIClient` class that wraps HTTP requests. This can be reused for other Python scripts that need to interact with the MiniPAM API.

```python
from minipam.cli import APIClient

with APIClient("http://localhost:8000") as client:
    cidrs = client.list_cidrs()
    print(cidrs)
```
