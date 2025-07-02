#!/bin/bash

# RAG Application Runner Script
# This script sets up and runs the RAG application with all dependencies

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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if port is in use
port_in_use() {
    lsof -i :$1 >/dev/null 2>&1
}

# Parse command line arguments
SETUP_ONLY=false
SKIP_SETUP=false
PORT=8000
HOST="localhost"

while [[ $# -gt 0 ]]; do
    case $1 in
        --setup-only)
            SETUP_ONLY=true
            shift
            ;;
        --skip-setup)
            SKIP_SETUP=true
            shift
            ;;
        --port)
            PORT="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --setup-only    Only run setup, don't start the server"
            echo "  --skip-setup    Skip setup and start server directly"
            echo "  --port PORT     Port to run the server on (default: 8000)"
            echo "  --host HOST     Host to bind to (default: localhost)"
            echo "  --help          Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

print_status "Starting RAG Application setup and deployment..."

# Check prerequisites
if ! command_exists python3; then
    print_error "Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

if ! command_exists pip; then
    print_error "pip is not installed. Please install pip first."
    exit 1
fi

# Setup phase
if [ "$SKIP_SETUP" = false ]; then
    print_status "Running environment setup..."
    
    # Make setup.sh executable and run it
    if [ -f "./setup.sh" ]; then
        chmod +x ./setup.sh
        print_status "Running setup.sh for database and dependencies..."
        ./setup.sh
        print_success "Environment setup completed"
    else
        print_warning "setup.sh not found, running manual setup..."
        
        # Install Python dependencies
        print_status "Installing Python dependencies..."
        pip install -r requirements.txt
        
        # Check if PostgreSQL is available
        if command_exists psql; then
            print_status "PostgreSQL client found, checking database connection..."
            if PGPASSWORD=password psql -h localhost -U postgres -d your_app_db -c '\q' 2>/dev/null; then
                print_success "Database connection successful"
                # Enable pgvector extension
                print_status "Ensuring pgvector extension is enabled..."
                PGPASSWORD=password psql -h localhost -U postgres -d your_app_db -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>/dev/null || print_warning "Could not enable pgvector extension"
            else
                print_warning "Could not connect to PostgreSQL database"
                print_warning "Make sure PostgreSQL is running with the correct credentials"
            fi
        else
            print_warning "PostgreSQL client not found"
        fi
    fi
    
    # Create logs directory
    print_status "Creating logs directory..."
    mkdir -p logs
    
    # Check environment file
    if [ ! -f ".env" ]; then
        print_warning ".env file not found"
        if [ -f ".env.example" ]; then
            print_status "Copying .env.example to .env"
            cp .env.example .env
            print_warning "Please configure your .env file with proper values before running the application"
        else
            print_warning "Please create a .env file with the required configuration"
        fi
    fi
    
    # Run database migrations
    if command_exists alembic; then
        print_status "Running database migrations..."
        alembic upgrade head || print_warning "Database migrations failed"
    else
        print_warning "Alembic not found, skipping database migrations"
    fi
fi

if [ "$SETUP_ONLY" = true ]; then
    print_success "Setup completed successfully!"
    print_status "To start the server, run: $0 --skip-setup"
    exit 0
fi

# Pre-flight checks
print_status "Running pre-flight checks..."

# Check if port is available
if port_in_use $PORT; then
    print_error "Port $PORT is already in use"
    print_status "You can specify a different port with --port <PORT>"
    exit 1
fi

# Check environment variables
ENV_VARS=("OAUTH_CLIENT_ID" "OAUTH_CLIENT_SECRET" "OAUTH_DOMAIN" "GEMINI_API_KEY" "JWT_SECRET_KEY")
MISSING_VARS=()

for var in "${ENV_VARS[@]}"; do
    if [ -z "${!var}" ] && ! grep -q "^$var=" .env 2>/dev/null; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    print_warning "Missing environment variables:"
    for var in "${MISSING_VARS[@]}"; do
        echo "  - $var"
    done
    print_warning "The application may not work correctly without these variables"
fi

print_success "Pre-flight checks completed"

# Start the application
print_status "Starting RAG application server..."
print_status "Server will be available at: http://$HOST:$PORT"
print_status "API documentation at: http://$HOST:$PORT/docs"
print_status "Press Ctrl+C to stop the server"

# Use uvicorn to start the server
if command_exists uvicorn; then
    exec uvicorn main:app --host "$HOST" --port "$PORT" --reload
else
    # Fallback to python if uvicorn command not found
    export APP_HOST="$HOST"
    export APP_PORT="$PORT"
    exec python main.py
fi