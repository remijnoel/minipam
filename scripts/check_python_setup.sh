#!/bin/bash
# Check Python setup script for MiniPAM

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to log messages
log() {
    echo -e "${GREEN}✓ $1${NC}"
}

warn() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

error() {
    echo -e "${RED}✗ $1${NC}"
}

info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

echo "MiniPAM Python Setup Check"
echo "=========================="

# Check Python version
echo ""
info "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -ge 9 ]; then
    log "Python $PYTHON_VERSION is supported"
else
    error "Python $PYTHON_VERSION is not supported. Requires Python 3.9+"
    exit 1
fi

# Check if virtual environment exists
echo ""
info "Checking virtual environment..."
if [ -d ".venv" ]; then
    log "Virtual environment found at .venv"
else
    warn "Virtual environment not found. Creating..."
    python3 -m venv .venv
    log "Virtual environment created"
fi

# Check if virtual environment is activated
echo ""
info "Checking virtual environment activation..."
if [ -n "$VIRTUAL_ENV" ]; then
    log "Virtual environment is activated: $VIRTUAL_ENV"
else
    warn "Virtual environment not activated. Activating..."
    source .venv/bin/activate
    log "Virtual environment activated"
fi

# Check pip version
echo ""
info "Checking pip version..."
pip --version
log "pip is available"

# Check if requirements are installed
echo ""
info "Checking installed packages..."
MISSING_PACKAGES=()

# Check main requirements
while IFS= read -r package; do
    if [ -n "$package" ] && [[ ! "$package" =~ ^#.* ]]; then
        PACKAGE_NAME=$(echo $package | cut -d'>' -f1 | cut -d'=' -f1 | cut -d'[' -f1)
        if ! pip show "$PACKAGE_NAME" >/dev/null 2>&1; then
            MISSING_PACKAGES+=("$PACKAGE_NAME")
        fi
    fi
done < requirements.txt

if [ ${#MISSING_PACKAGES[@]} -eq 0 ]; then
    log "All main requirements are installed"
else
    warn "Missing packages: ${MISSING_PACKAGES[*]}"
    info "Installing missing packages..."
    pip install -r requirements.txt
    log "Main requirements installed"
fi

# Check development requirements
echo ""
info "Checking development requirements..."
DEV_MISSING_PACKAGES=()

while IFS= read -r package; do
    if [ -n "$package" ] && [[ ! "$package" =~ ^#.* ]]; then
        PACKAGE_NAME=$(echo $package | cut -d'>' -f1 | cut -d'=' -f1 | cut -d'[' -f1)
        if ! pip show "$PACKAGE_NAME" >/dev/null 2>&1; then
            DEV_MISSING_PACKAGES+=("$PACKAGE_NAME")
        fi
    fi
done < requirements-dev.txt

if [ ${#DEV_MISSING_PACKAGES[@]} -eq 0 ]; then
    log "All development requirements are installed"
else
    warn "Missing development packages: ${DEV_MISSING_PACKAGES[*]}"
    info "Installing missing development packages..."
    pip install -r requirements-dev.txt
    log "Development requirements installed"
fi

# Check if package is installed in development mode
echo ""
info "Checking MiniPAM package installation..."
if pip show minipam >/dev/null 2>&1; then
    log "MiniPAM package is installed"
else
    warn "MiniPAM package not installed. Installing in development mode..."
    pip install -e .
    log "MiniPAM package installed in development mode"
fi

# Check if minipam command is available
echo ""
info "Checking minipam command..."
if command -v minipam >/dev/null 2>&1; then
    log "minipam command is available"
    minipam --help | head -5
else
    error "minipam command not found. Installation may have failed."
    exit 1
fi

# Check directory structure
echo ""
info "Checking directory structure..."
REQUIRED_DIRS=("src/minipam" "tests" "docs/specs")
for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        log "Directory $dir exists"
    else
        error "Required directory $dir is missing"
        exit 1
    fi
done

# Check required files
echo ""
info "Checking required files..."
REQUIRED_FILES=("requirements.txt" "requirements-dev.txt" "pyproject.toml" "README.md")
for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        log "File $file exists"
    else
        error "Required file $file is missing"
        exit 1
    fi
done

# Summary
echo ""
echo "Setup Check Summary"
echo "==================="
log "Python environment is properly configured"
log "All dependencies are installed"
log "MiniPAM package is installed and accessible"
log "Directory structure is correct"
echo ""
info "You can now run:"
info "  ./dev-server.sh                 # Start development server"
info "  python tests/run_tests.py       # Run tests"
info "  minipam --help                  # See CLI help"
info "  minipam init                    # Initialize configuration"
info "  minipam serve                   # Start server"