# MiniPAM Web UI

A modern, responsive web interface for managing CIDR blocks in the MiniPAM service.

## Features

- **Modern UI**: Clean, responsive design with Tailwind CSS
- **Full CRUD Operations**: Create, read, update, and delete CIDR blocks
- **Real-time Status**: Health check indicator and connection status
- **Search & Filter**: Search through CIDR blocks efficiently
- **Tag Management**: Add and manage key-value tags for CIDR blocks
- **Hierarchy Support**: View parent-child relationships between CIDR blocks
- **Responsive Design**: Works perfectly on desktop and mobile devices

## Getting Started

### Prerequisites

- Node.js 18+ and npm (for development)
- Python 3.9+ with MiniPAM backend running

### Quick Start

1. **Start the backend server:**

   ```bash
   cd /path/to/minipam
   uvicorn src.minipam.main:app --reload
   ```

2. **Access the web UI:**
   Open your browser and navigate to `http://localhost:8000`

### Development Mode

For development with hot reload:

1. **Start both backend and frontend in development mode:**

   ```bash
   ./dev-server.sh
   ```

2. **Access the development servers:**
   - Backend: `http://localhost:8000`
   - Frontend (dev): `http://localhost:3001`

## Usage

### Managing CIDR Blocks

1. **View CIDR Blocks**: The main page displays all CIDR blocks in a table format
2. **Search**: Use the search bar to find specific CIDR blocks
3. **Create New**: Click "Create New CIDR" to add a new block
4. **Edit**: Click the edit icon on any CIDR block to modify it
5. **Delete**: Click the delete icon to remove a CIDR block
6. **View Details**: Click on any CIDR block to see detailed information

### CIDR Block Fields

- **CIDR**: Network address in CIDR notation (e.g., `192.168.1.0/24`)
- **Name**: Optional human-readable name
- **Description**: Optional description
- **Tags**: Key-value pairs for categorization
- **Parent**: Parent CIDR block (for hierarchy)
- **Children**: Child CIDR blocks (automatically managed)

### Tag Management

Tags are key-value pairs that help organize and categorize CIDR blocks:

```json
{
  "environment": "production",
  "region": "us-east-1",
  "team": "network-ops"
}
```

### Example CIDR Blocks

```json
{
  "cidr": "10.0.0.0/8",
  "name": "Private Network",
  "description": "RFC 1918 private network",
  "tags": {
    "type": "private",
    "rfc": "1918"
  }
}
```

## API Integration

The web UI communicates with the MiniPAM FastAPI backend through REST endpoints:

- `GET /health` - Health check
- `GET /cidrs/` - List all CIDR blocks
- `POST /cidrs/` - Create a new CIDR block
- `GET /cidrs/{cidr}` - Get a specific CIDR block
- `PUT /cidrs/{cidr}` - Update a CIDR block
- `DELETE /cidrs/{cidr}` - Delete a CIDR block

## Architecture

- **Frontend**: Vue.js 3 with Composition API
- **Styling**: Tailwind CSS for responsive design
- **HTTP Client**: Axios for API communication
- **Build Tool**: Vite for fast development and optimized production builds
- **Backend Integration**: FastAPI serves the built frontend at the root path

## Project Structure

```text
webui/
├── src/
│   ├── components/
│   │   ├── CidrTable.vue      # Main table component
│   │   ├── CidrForm.vue       # Create/edit form
│   │   └── CidrDetails.vue    # Detail view modal
│   ├── api/
│   │   └── client.js          # API client
│   ├── App.vue                # Main application component
│   ├── main.js                # Application entry point
│   └── style.css              # Global styles
├── dist/                      # Built production files
├── package.json               # Dependencies and scripts
├── vite.config.js             # Vite configuration
└── tailwind.config.js         # Tailwind CSS configuration
```

## Development

### Building for Production

```bash
cd webui
npm run build
```

The built files will be in the `dist/` directory and automatically served by the FastAPI backend.

### Running Tests

Backend tests (ensure the web UI integration doesn't break existing functionality):

```bash
python -m pytest tests/ -v
```

### Code Quality

The project follows modern JavaScript/Vue.js best practices:

- Composition API for reactive state management
- Component-based architecture
- Error handling and loading states
- Responsive design patterns
- Accessibility considerations

## Troubleshooting

### Common Issues

1. **Web UI not loading**: Ensure the backend is running and the frontend is built
2. **API errors**: Check the browser console for detailed error messages
3. **Port conflicts**: The dev server will automatically try alternative ports

### Health Check

The web UI includes a health status indicator in the top-right corner:

- Green: Connected to backend
- Red: Connection issues

### Debug Mode

For development debugging:

1. Open browser developer tools
2. Check the Console tab for API request logs
3. Check the Network tab for API response details

## Contributing

When making changes to the web UI:

1. Test in development mode first
2. Ensure all backend tests still pass
3. Build and test the production version
4. Test both desktop and mobile layouts

## License

Same as the main MiniPAM project.
