# MiniPAM API Specification

## Overview

MiniPAM provides a RESTful API for managing CIDR blocks with hierarchical relationships. The API is built with FastAPI and follows REST conventions.

**Base URL**: `http://localhost:8000/api/v1`

## Authentication

The API supports three authentication modes configured via the `auth.backend` setting:

1. **none**: No authentication required (default for development)
2. **apikey**: API key authentication via `X-API-Key` header
3. **oidc**: OpenID Connect authentication with JWT tokens

### API Key Authentication
```http
X-API-Key: your-api-key-here
```

### OIDC Authentication
```http
Authorization: Bearer <jwt-token>
```

## Common Response Formats

### Success Response
```json
{
  "status": "success",
  "data": { ... }
}
```

### Error Response
```json
{
  "error": "error_type",
  "message": "Human-readable error message",
  "details": { ... },
  "timestamp": "2024-01-19T12:00:00Z"
}
```

### HTTP Status Codes
- `200 OK`: Successful GET, PUT
- `201 Created`: Successful POST
- `204 No Content`: Successful DELETE
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource conflict (e.g., duplicate CIDR)
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

## API Endpoints

### 1. Health Check

#### GET /health/ready
Check if the service is ready to accept requests.

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-19T12:00:00Z",
  "storage": {
    "type": "file",
    "status": "connected"
  },
  "auth": {
    "backend": "none",
    "status": "ready"
  }
}
```

### 2. CIDR Block Management

#### GET /cidrs
List all CIDR blocks with optional filtering and pagination.

**Query Parameters**:
- `offset` (int, optional): Pagination offset (default: 0)
- `limit` (int, optional): Maximum items to return (default: 100, max: 1000)
- `parent` (string, optional): Filter by parent CIDR
- `tag` (string, optional): Filter by tag (can be repeated)

**Response**:
```json
{
  "blocks": [
    {
      "cidr": "10.0.0.0/16",
      "name": "Main Network",
      "description": "Primary corporate network",
      "parent": null,
      "tags": ["vlan:100", "location:DC1"],
      "created_at": "2024-01-19T12:00:00Z",
      "updated_at": null
    },
    {
      "cidr": "10.0.128.0/17",
      "name": "DMZ zone",
      "description": "Demilitarized zone",
      "parent": "10.0.0.0/16",
      "tags": ["vlan:200", "location:DC1"],
      "created_at": "2024-01-19T12:00:00Z",
      "updated_at": null
    }
  ],
  "total": 2,
  "offset": 0,
  "limit": 100
}
```

#### GET /cidrs/tree
Get all CIDR blocks organized in a hierarchical tree structure.

**Response**:
```json
[
  {
    "cidr": "10.0.0.0/16",
    "name": "Main Network",
    "description": "Primary corporate network",
    "parent": null,
    "tags": ["vlan:100", "location:DC1"],
    "created_at": "2024-01-19T12:00:00Z",
    "updated_at": null,
    "children": [
      {
        "cidr": "10.0.128.0/17",
        "name": "DMZ zone",
        "description": "Demilitarized zone",
        "parent": "10.0.0.0/16",
        "tags": ["vlan:200", "location:DC1"],
        "created_at": "2024-01-19T12:00:00Z",
        "updated_at": null,
        "children": [
          {
            "cidr": "10.0.128.0/23",
            "name": "DMZ production",
            "description": "Production DMZ servers",
            "parent": "10.0.128.0/17",
            "tags": ["vlan:201", "device:fw01", "customer:production"],
            "created_at": "2024-01-19T12:00:00Z",
            "updated_at": null,
            "children": []
          }
        ]
      }
    ]
  },
  {
    "cidr": "172.16.0.0/16",
    "name": "Internal network",
    "description": "Internal corporate network",
    "parent": null,
    "tags": ["vlan:300", "location:Office"],
    "created_at": "2024-01-19T12:00:00Z",
    "updated_at": null,
    "children": []
  }
]
```

#### GET /cidrs/{cidr}
Get a specific CIDR block by its CIDR notation.

**Path Parameters**:
- `cidr` (string, required): CIDR notation (URL-encoded, e.g., `10.0.0.0%2F16`)

**Response**:
```json
{
  "cidr": "10.0.0.0/16",
  "name": "Main Network",
  "description": "Primary corporate network",
  "parent": null,
  "tags": ["vlan:100", "location:DC1"],
  "created_at": "2024-01-19T12:00:00Z",
  "updated_at": null
}
```

**Error Response (404)**:
```json
{
  "error": "not_found",
  "message": "CIDR block '10.0.0.0/16' not found",
  "timestamp": "2024-01-19T12:00:00Z"
}
```

#### POST /cidrs
Create a new CIDR block.

**Request Body**:
```json
{
  "cidr": "10.0.0.0/24",
  "name": "Development Network",
  "description": "Network for development environment",
  "parent": "10.0.0.0/16",
  "tags": ["vlan:101", "environment:dev", "location:DC1"]
}
```

**Field Validation**:
- `cidr` (string, required): Valid IPv4 CIDR notation (not /0)
- `name` (string, required): Human-readable name
- `description` (string, optional): Detailed description
- `parent` (string, optional): Parent CIDR notation (must exist)
- `tags` (array[string], optional): List of tags

**Response (201 Created)**:
```json
{
  "cidr": "10.0.0.0/24",
  "name": "Development Network",
  "description": "Network for development environment",
  "parent": "10.0.0.0/16",
  "tags": ["vlan:101", "environment:dev", "location:dc1"],
  "created_at": "2024-01-19T12:00:00Z",
  "updated_at": null
}
```

**Error Responses**:
- **409 Conflict**: CIDR already exists
- **400 Bad Request**: Invalid CIDR notation
- **422 Unprocessable Entity**: Validation errors (overlapping CIDR, invalid parent, etc.)

#### PUT /cidrs/{cidr}
Update an existing CIDR block.

**Path Parameters**:
- `cidr` (string, required): CIDR notation (URL-encoded)

**Request Body** (all fields optional):
```json
{
  "name": "Updated Network Name",
  "description": "Updated description",
  "parent": "10.0.0.0/8",
  "tags": ["vlan:102", "environment:prod"]
}
```

**Note**: The CIDR notation itself cannot be changed.

**Response (200 OK)**:
```json
{
  "cidr": "10.0.0.0/24",
  "name": "Updated Network Name",
  "description": "Updated description",
  "parent": "10.0.0.0/8",
  "tags": ["vlan:102", "environment:prod"],
  "created_at": "2024-01-19T12:00:00Z",
  "updated_at": "2024-01-19T12:30:00Z"
}
```

#### DELETE /cidrs/{cidr}
Delete a CIDR block.

**Path Parameters**:
- `cidr` (string, required): CIDR notation (URL-encoded)

**Response**: 204 No Content

**Error Responses**:
- **404 Not Found**: CIDR block not found
- **409 Conflict**: Cannot delete CIDR with children

### 3. Validation Endpoints

#### POST /validate/cidr
Validate a CIDR block before creation.

**Request Body**:
```json
{
  "cidr": "10.0.0.0/24",
  "parent": "10.0.0.0/16"
}
```

**Response**:
```json
{
  "is_valid": true,
  "errors": [],
  "warnings": []
}
```

**Error Response**:
```json
{
  "is_valid": false,
  "errors": [
    "CIDR 10.0.0.0/24 overlaps with existing block 10.0.0.0/23"
  ],
  "warnings": [
    "CIDR 10.0.0.0/24 is a small subnet (/24)"
  ]
}
```

### 4. User Information (OIDC only)

#### GET /user/me
Get information about the authenticated user.

**Response**:
```json
{
  "id": "user-123",
  "username": "john.doe",
  "roles": ["admin"],
  "scopes": ["cidrs:read", "cidrs:write"]
}
```

## Tag Convention

MiniPAM uses a structured tag format for special attributes:

- `vlan:<value>` - VLAN identifier (e.g., `vlan:100`)
- `vrf:<value>` - VRF identifier (e.g., `vrf:mgmt`)
- `device:<value>` - Device name (e.g., `device:switch01`)
- `customer:<value>` - Customer identifier (e.g., `customer:acme`)
- `location:<value>` - Location identifier (e.g., `location:DC1`)

Other tags without a colon are treated as simple labels (e.g., `production`, `dmz`).

## Data Models

### CIDRBlock
```typescript
interface CIDRBlock {
  cidr: string;           // IPv4 CIDR notation (e.g., "10.0.0.0/16")
  name: string;           // Human-readable name
  description?: string;   // Optional description
  parent?: string;        // Parent CIDR notation (null for root blocks)
  tags: string[];         // Array of tags
  created_at: string;     // ISO 8601 timestamp
  updated_at?: string;    // ISO 8601 timestamp (null if never updated)
}
```

### TreeNode
```typescript
interface TreeNode extends CIDRBlock {
  children: TreeNode[];   // Array of child nodes
}
```

### ValidationResult
```typescript
interface ValidationResult {
  is_valid: boolean;
  errors: string[];
  warnings: string[];
}
```

## URL Encoding

When using CIDR notation in URL paths, ensure proper encoding:
- `/` should be encoded as `%2F`
- Example: `10.0.0.0/16` → `10.0.0.0%2F16`

JavaScript example:
```javascript
const cidr = "10.0.0.0/16";
const encoded = encodeURIComponent(cidr);  // "10.0.0.0%2F16"
const url = `/api/v1/cidrs/${encoded}`;
```

## Rate Limiting

Currently, no rate limiting is implemented. This may be added in future versions.

## CORS

CORS is enabled for all origins in development mode. Production deployments should configure appropriate CORS settings.

## WebSocket Support

Not currently implemented. Future versions may include WebSocket support for real-time updates.

## Example Usage

### Creating a hierarchical CIDR structure

1. Create root network:
```bash
curl -X POST http://localhost:8000/api/v1/cidrs \
  -H "Content-Type: application/json" \
  -d '{
    "cidr": "10.0.0.0/16",
    "name": "Corporate Network",
    "tags": ["vlan:100", "location:DC1"]
  }'
```

2. Create child subnet:
```bash
curl -X POST http://localhost:8000/api/v1/cidrs \
  -H "Content-Type: application/json" \
  -d '{
    "cidr": "10.0.1.0/24",
    "name": "Web Servers",
    "parent": "10.0.0.0/16",
    "tags": ["vlan:101", "device:fw01", "customer:web-team"]
  }'
```

3. Get hierarchical tree:
```bash
curl http://localhost:8000/api/v1/cidrs/tree
```

## Frontend Integration Notes

1. **State Management**: The tree structure from `/cidrs/tree` is ideal for hierarchical display
2. **Real-time Updates**: Currently requires polling; consider implementing periodic refresh
3. **Validation**: Use `/validate/cidr` endpoint before form submission for better UX
4. **Tag Parsing**: Extract structured tags (vlan:, vrf:, etc.) for dedicated UI fields
5. **Error Handling**: Display user-friendly messages based on error responses

## Version

Current API version: v1

Future versions will be available at `/api/v2`, `/api/v3`, etc.