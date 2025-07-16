#!/bin/bash

# FastAPI Application Startup Script
# This script sets up the environment and starts the FastAPI service

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if script is run from project root
check_project_structure() {
    print_status "Checking project structure..."
    
    if [[ ! -f "pyproject.toml" ]] || [[ ! -d "app" ]] || [[ ! -f "app/main.py" ]]; then
        print_error "This script must be run from the project root directory"
        print_error "Expected structure: pyproject.toml, app/, app/main.py"
        exit 1
    fi
    
    print_success "Project structure validated"
}

# Check Python version
check_python() {
    print_status "Checking Python version..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 is not installed or not in PATH"
        exit 1
    fi
    
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    required_version="3.12"
    
    if [[ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]]; then
        print_warning "Python version $python_version detected. Required: >= $required_version"
        print_warning "Continuing anyway, but you may encounter issues..."
    else
        print_success "Python $python_version is compatible"
    fi
}

# Install uv package manager if not present
install_uv() {
    print_status "Checking for uv package manager..."
    
    if ! command -v uv &> /dev/null; then
        print_status "Installing uv package manager..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.local/bin:$PATH"
        
        # Verify installation
        if ! command -v uv &> /dev/null; then
            print_error "Failed to install uv package manager"
            print_status "Falling back to pip installation..."
            return 1
        fi
        
        print_success "uv package manager installed successfully"
    else
        print_success "uv package manager is already installed"
    fi
    
    return 0
}

# Install dependencies using uv
install_dependencies_uv() {
    print_status "Installing dependencies using uv..."
    
    if [[ -f "uv.lock" ]]; then
        uv sync
    else
        uv sync --generate-lockfile
    fi
    
    print_success "Dependencies installed using uv"
}

# Fallback: Install dependencies using pip
install_dependencies_pip() {
    print_status "Installing dependencies using pip..."
    
    # Create virtual environment if it doesn't exist
    if [[ ! -d "venv" ]]; then
        print_status "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install dependencies
    if [[ -f "requirements.txt" ]]; then
        pip install -r requirements.txt
    else
        # Install from pyproject.toml
        pip install -e .
    fi
    
    print_success "Dependencies installed using pip"
}

# Install dependencies
install_dependencies() {
    if install_uv; then
        install_dependencies_uv
    else
        install_dependencies_pip
    fi
}

# Set environment variables
setup_environment() {
    print_status "Setting up environment variables..."
    
    # Get the current working directory (project root)
    local project_root="$(pwd)"
    
    # Set default values if not already set
    export PYTHONPATH="${PYTHONPATH:-$project_root:$project_root/app}"
    export POD_NAMESPACE="${POD_NAMESPACE:-development}"
    
    # Create .env file if it doesn't exist
    if [[ ! -f ".env" ]]; then
        print_status "Creating .env file..."
        cat > .env << EOF
# Environment Configuration
POD_NAMESPACE=development
PYTHONPATH=$project_root:$project_root/app
EOF
        print_success "Created .env file with default values"
    fi
    
    print_success "Environment setup complete"
}

# Health check function
health_check() {
    local max_attempts=30
    local attempt=1
    local port=${1:-8000}
    
    print_status "Performing health check on port $port..."
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -s -f "http://localhost:$port/healthz" > /dev/null 2>&1; then
            print_success "Application is healthy and responding"
            return 0
        fi
        
        if [[ $attempt -eq 1 ]]; then
            print_status "Waiting for application to start..."
        fi
        
        sleep 2
        ((attempt++))
    done
    
    print_warning "Health check timed out after $max_attempts attempts"
    return 1
}

# Start the application
start_application() {
    local api_mode="${1:-ALL}"
    local port="${2:-8000}"
    
    print_status "Starting FastAPI application..."
    print_status "API Mode: $api_mode"
    print_status "Port: $port"
    
    # Run the application
    if command -v uv &> /dev/null && [[ -f "uv.lock" ]]; then
        print_status "Using uv to run the application..."
        uv run python -m app.main --api-mode "$api_mode" &
    elif [[ -d "venv" ]]; then
        print_status "Using virtual environment to run the application..."
        source venv/bin/activate
        python -m app.main --api-mode "$api_mode" &
    else
        print_status "Running with system Python..."
        python3 -m app.main --api-mode "$api_mode" &
    fi
    
    local app_pid=$!
    
    # Wait a moment for the application to start
    sleep 3
    
    # Check if the process is still running
    if ! kill -0 $app_pid 2>/dev/null; then
        print_error "Application failed to start"
        exit 1
    fi
    
    print_success "Application started with PID: $app_pid"
    
    # Perform health check
    health_check "$port"
    
    print_success "FastAPI application is running!"
    print_status "Access the application at: http://localhost:$port"
    print_status "API documentation available at: http://localhost:$port/docs"
    print_status "Press Ctrl+C to stop the application"
    
    # Wait for the application process
    wait $app_pid
}

# Cleanup function
cleanup() {
    print_status "Shutting down application..."
    # Kill any remaining Python processes running our app
    pkill -f "python.*app.main" 2>/dev/null || true
    print_success "Cleanup complete"
}

# Set up signal handlers
trap cleanup EXIT INT TERM

# Main execution
main() {
    print_status "Starting FastAPI Application Setup"
    print_status "=================================="
    
    # Parse command line arguments
    API_MODE="all"
    PORT="8000"
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --api-mode)
                API_MODE="$2"
                shift 2
                ;;
            --port)
                PORT="$2"
                shift 2
                ;;
            --help|-h)
                echo "Usage: $0 [options]"
                echo "Options:"
                echo "  --api-mode MODE    Set API mode (default: ALL)"
                echo "  --port PORT        Set port number (default: 8000)"
                echo "  --help, -h         Show this help message"
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                exit 1
                ;;
        esac
    done
    
    # Execute setup steps
    check_project_structure
    check_python
    install_dependencies
    setup_environment
    
    # Start the application
    start_application "$API_MODE" "$PORT"
}

# Check if script is being sourced or executed
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi