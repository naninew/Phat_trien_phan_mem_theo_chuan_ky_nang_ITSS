#!/bin/bash
# Run All Tests Script
# Executes the complete test suite for the project

set -e

echo "=========================================="
echo "  Running Complete Test Suite"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:8080}"
TEST_RESULTS_DIR="test_results_$(date +%Y%m%d_%H%M%S)"

echo -e "${BLUE}Test Configuration:${NC}"
echo "  Backend URL: $BACKEND_URL"
echo "  Frontend URL: $FRONTEND_URL"
echo "  Results Directory: $TEST_RESULTS_DIR"
echo ""

# Create results directory
mkdir -p "$TEST_RESULTS_DIR"

# Step 1: Run Backend Unit Tests
echo -e "${YELLOW}[1/4] Running Backend Unit Tests...${NC}"
echo "-------------------------------------------"
if pytest tests/backend_tests/test_services.py -v --tb=short --html="$TEST_RESULTS_DIR/backend_unit_tests.html" --self-contained-html; then
    echo -e "${GREEN}✓ Backend Unit Tests Passed${NC}"
else
    echo -e "${RED}✗ Backend Unit Tests Failed${NC}"
    echo "Check $TEST_RESULTS_DIR/backend_unit_tests.html for details"
fi
echo ""

# Step 2: Run API Integration Tests
echo -e "${YELLOW}[2/4] Running API Integration Tests...${NC}"
echo "-------------------------------------------"
if pytest tests/backend_tests/test_api.py -v --tb=short --html="$TEST_RESULTS_DIR/api_integration_tests.html" --self-contained-html; then
    echo -e "${GREEN}✓ API Integration Tests Passed${NC}"
else
    echo -e "${RED}✗ API Integration Tests Failed${NC}"
    echo "Check $TEST_RESULTS_DIR/api_integration_tests.html for details"
fi
echo ""

# Step 3: Run UI Tests (Command Line)
echo -e "${YELLOW}[3/4] Running UI Tests...${NC}"
echo "-------------------------------------------"
if python tests/ui_tests/run_ui_tests.py --url "$FRONTEND_URL" --export="$TEST_RESULTS_DIR/ui_tests.json"; then
    echo -e "${GREEN}✓ UI Tests Passed${NC}"
else
    echo -e "${RED}✗ UI Tests Failed${NC}"
    echo "Check $TEST_RESULTS_DIR/ui_tests.json for details"
fi
echo ""

# Step 4: Generate Coverage Report
echo -e "${YELLOW}[4/4] Generating Coverage Report...${NC}"
echo "-------------------------------------------"
if command -v pytest &> /dev/null && command -v coverage &> /dev/null; then
    if pytest tests/ --cov=backend --cov-report=html --cov-report=xml --cov-report=term -o addopts=""; then
        echo -e "${GREEN}✓ Coverage Report Generated${NC}"
        echo "  HTML Report: $TEST_RESULTS_DIR/htmlcov/index.html"
        echo "  XML Report: $TEST_RESULTS_DIR/coverage.xml"
    else
        echo -e "${YELLOW}⚠ Coverage Report Generation Failed${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Coverage tools not installed, skipping...${NC}"
    echo "  Install with: pip install pytest-cov coverage"
fi
echo ""

# Summary
echo "=========================================="
echo "  Test Suite Complete"
echo "=========================================="
echo ""
echo -e "${BLUE}Results saved to:${NC} $TEST_RESULTS_DIR"
echo ""
echo "Generated Files:"
ls -la "$TEST_RESULTS_DIR/" 2>/dev/null || echo "  (No files generated)"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "  1. Review failed tests in HTML reports"
echo "  2. Check coverage report for untested code"
echo "  3. Fix failing tests and re-run"
echo ""
echo -e "For more details, see ${GREEN}HOW_TO_RUN_TEST.md${NC}"
echo ""
