# MiniPAM Web UI

A modern, responsive web interface for the MiniPAM CIDR Management Service built with Vue.js and Tailwind CSS.

## Features

- **CIDR Block Management**: Create, read, update, and delete CIDR blocks
- **Network Information**: Automatic calculation of network details (subnet mask, usable IPs, etc.)
- **Search & Filter**: Search through CIDR blocks by name, description, or tags
- **Tag Management**: Visual tag editor with easy add/remove functionality
- **Hierarchy Visualization**: View parent/child relationships between CIDR blocks
- **Responsive Design**: Works on desktop, tablet, and mobile devices
- **Real-time Status**: Connection status indicator and manual refresh
- **Form Validation**: Client-side validation for CIDR format and required fields

## Technology Stack

- **Vue.js 3**: Progressive JavaScript framework with Composition API
- **Vite**: Fast build tool and development server
- **Tailwind CSS**: Utility-first CSS framework for styling
- **Axios**: Promise-based HTTP client for API communication
- **Headless UI**: Unstyled, accessible UI components

## Development

### Prerequisites

- Node.js 18+ and npm
- MiniPAM API server running (usually on <http://localhost:8000>)

### Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Development Server

The development server runs on <http://localhost:3000> and includes:

- Hot module replacement
- Proxy to API server (`/api/*` → `http://localhost:8000/*`)
- Source maps for debugging

### Building

The build process creates optimized static files in the `dist/` directory:

```bash
npm run build
```

The built files are automatically served by the FastAPI backend when available.

## Components

### Main Components

- **App.vue**: Main application shell with health monitoring and error handling
- **CidrTable.vue**: Sortable, searchable table of CIDR blocks
- **CidrForm.vue**: Modal form for creating/editing CIDR blocks
- **CidrDetails.vue**: Modal for viewing detailed CIDR information

### API Integration

- **api/client.js**: Axios-based API client with error handling and logging

## Usage

### Viewing CIDR Blocks

The main interface shows a table of all CIDR blocks with:

- CIDR notation (e.g., 192.168.1.0/24)
- Name and description
- Tags (color-coded badges)
- Parent/child relationships
- Creation timestamp
- Action buttons (view, edit, delete)

### Creating CIDR Blocks

1. Click "Add CIDR Block" button
2. Fill in the form:
   - **CIDR Block**: Required, e.g., "192.168.1.0/24"
   - **Name**: Optional display name
   - **Description**: Optional details
   - **Tags**: Key-value pairs for categorization
   - **Parent CIDR**: Optional parent network
   - **Child CIDRs**: Optional list of subnets
3. Click "Create" to save

### Viewing Details

Click the eye icon to view detailed information including:

- Network calculations (subnet mask, usable IPs, IP ranges)
- Complete tag list
- Parent/child hierarchy
- Metadata (creation date, etc.)

### Editing CIDR Blocks

1. Click the edit icon (pencil)
2. Modify fields in the form (CIDR notation cannot be changed)
3. Click "Update" to save changes

### Searching

Use the search box to filter CIDR blocks by:

- CIDR notation
- Name
- Description
- Tag keys or values

## API Proxy

The Vite development server proxies API requests:

- Frontend: <http://localhost:3000>
- API calls: `/api/*` → <http://localhost:8000/>*

In production, the FastAPI server serves both the API and static files.

## Styling

The interface uses Tailwind CSS with a clean, professional design:

- **Colors**: Indigo primary, gray neutrals, semantic colors for status
- **Typography**: System font stack, proper hierarchy
- **Layout**: Responsive grid and flexbox layouts
- **Interactive Elements**: Hover states, focus indicators, loading spinners
- **Accessibility**: Proper ARIA labels, keyboard navigation, screen reader support

## Error Handling

- Network errors display user-friendly messages
- Form validation prevents invalid submissions
- Loading states provide visual feedback
- Graceful degradation when API is unavailable

## Browser Support

- Chrome 88+
- Firefox 85+
- Safari 14+
- Edge 88+

Requires ES2020 support and modern CSS features.
