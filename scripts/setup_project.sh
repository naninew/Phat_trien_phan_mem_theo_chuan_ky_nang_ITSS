#!/bin/bash

# Rescue System - Project Setup Script
# This script helps you set up and run the entire project

set -e

echo "=========================================="
echo "  Roadside Rescue System - Setup Script"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Check if PostgreSQL is installed
check_postgresql() {
    if command -v psql &> /dev/null; then
        print_success "PostgreSQL is installed"
        return 0
    else
        print_error "PostgreSQL is not installed"
        return 1
    fi
}

# Check if Python is installed
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version)
        print_success "Python is installed: $PYTHON_VERSION"
        return 0
    else
        print_error "Python 3 is not installed"
        return 1
    fi
}

# Install Python dependencies
install_dependencies() {
    echo ""
    echo "Installing Python dependencies..."
    
    cd /workspace
    
    if [ -f "backend/requirements.txt" ]; then
        pip3 install -r backend/requirements.txt
        print_success "Backend dependencies installed"
    else
        print_error "requirements.txt not found"
        return 1
    fi
    
    if [ -f "frontend/requirements.txt" ]; then
        pip3 install -r frontend/requirements.txt
        print_success "Frontend dependencies installed"
    else
        print_warning "Frontend requirements.txt not found, skipping..."
    fi
}

# Initialize PostgreSQL database
init_database() {
    echo ""
    echo "Initializing PostgreSQL database..."
    
    DB_NAME="rescue_system"
    DB_USER="postgres"
    
    # Check if database exists
    if psql -U "$DB_USER" -lqt | cut -d \| -f 1 | grep -qw "$DB_NAME"; then
        print_warning "Database '$DB_NAME' already exists"
        read -p "Do you want to recreate it? (y/N): " confirm
        if [[ $confirm == [yY] ]]; then
            psql -U "$DB_USER" -c "DROP DATABASE IF EXISTS $DB_NAME;"
            print_success "Dropped existing database"
        else
            print_warning "Skipping database creation"
            return 0
        fi
    fi
    
    # Run initialization script
    if [ -f "/workspace/scripts/init_postgres.sql" ]; then
        # Run as postgres user
        sudo -u postgres psql -f /workspace/scripts/init_postgres.sql
        print_success "Database initialized successfully"
    else
        print_error "init_postgres.sql not found"
        return 1
    fi
}

# Start backend server
start_backend() {
    echo ""
    echo "Starting Backend Server..."
    cd /workspace/backend
    python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
    BACKEND_PID=$!
    print_success "Backend started on http://localhost:8000 (PID: $BACKEND_PID)"
    echo $BACKEND_PID > /tmp/rescue_backend.pid
}

# Start frontend server
start_frontend() {
    echo ""
    echo "Starting Frontend Server..."
    cd /workspace/frontend
    python3 -m nicegui.run --host 0.0.0.0 --port 8080 &
    FRONTEND_PID=$!
    print_success "Frontend started on http://localhost:8080 (PID: $FRONTEND_PID)"
    echo $FRONTEND_PID > /tmp/rescue_frontend.pid
}

# Stop all servers
stop_servers() {
    echo ""
    echo "Stopping all servers..."
    
    if [ -f /tmp/rescue_backend.pid ]; then
        kill $(cat /tmp/rescue_backend.pid) 2>/dev/null || true
        rm /tmp/rescue_backend.pid
        print_success "Backend stopped"
    fi
    
    if [ -f /tmp/rescue_frontend.pid ]; then
        kill $(cat /tmp/rescue_frontend.pid) 2>/dev/null || true
        rm /tmp/rescue_frontend.pid
        print_success "Frontend stopped"
    fi
}

# Main menu
show_menu() {
    echo ""
    echo "=========================================="
    echo "  Setup Menu"
    echo "=========================================="
    echo "1. Install dependencies"
    echo "2. Initialize database"
    echo "3. Start backend server"
    echo "4. Start frontend server"
    echo "5. Start all servers"
    echo "6. Stop all servers"
    echo "7. Check status"
    echo "8. Exit"
    echo ""
}

# Check server status
check_status() {
    echo ""
    echo "Server Status:"
    
    if [ -f /tmp/rescue_backend.pid ] && kill -0 $(cat /tmp/rescue_backend.pid) 2>/dev/null; then
        print_success "Backend is running (PID: $(cat /tmp/rescue_backend.pid))"
    else
        print_warning "Backend is not running"
    fi
    
    if [ -f /tmp/rescue_frontend.pid ] && kill -0 $(cat /tmp/rescue_frontend.pid) 2>/dev/null; then
        print_success "Frontend is running (PID: $(cat /tmp/rescue_frontend.pid))"
    else
        print_warning "Frontend is not running"
    fi
    
    echo ""
    echo "Access URLs:"
    echo "  - Backend API: http://localhost:8000"
    echo "  - API Docs: http://localhost:8000/docs"
    echo "  - Frontend: http://localhost:8080"
}

# Full setup
full_setup() {
    echo ""
    echo "Starting full setup..."
    check_python || exit 1
    install_dependencies
    check_postgresql || {
        print_warning "PostgreSQL not found. Please install PostgreSQL first."
        echo "See HOW_TO_START_PROJECT.md for installation instructions."
        exit 1
    }
    init_database
    echo ""
    print_success "Setup completed!"
    echo ""
    echo "You can now start the servers:"
    echo "  - Run option 5 to start all servers"
    echo "  - Or run backend: cd backend && python3 -m uvicorn app.main:app --reload"
    echo "  - Or run frontend: cd frontend && python3 -m nicegui.run"
}

# Main loop
while true; do
    show_menu
    read -p "Select an option (1-8): " choice
    
    case $choice in
        1)
            install_dependencies
            ;;
        2)
            init_database
            ;;
        3)
            start_backend
            ;;
        4)
            start_frontend
            ;;
        5)
            start_backend
            sleep 2
            start_frontend
            ;;
        6)
            stop_servers
            ;;
        7)
            check_status
            ;;
        8)
            echo "Goodbye!"
            exit 0
            ;;
        *)
            print_error "Invalid option"
            ;;
    esac
done
