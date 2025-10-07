#!/bin/bash
# Auto-format code to match project standards

set -e

# Color output
BLUE='\033[0;34m'
GREEN='\033[0;32m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}==>${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

echo ""
print_status "Formatting Python code with Black..."
poetry run black .
print_success "Python code formatted"

echo ""
print_status "Organizing imports..."
poetry run python -m isort . 2>/dev/null || echo "isort not installed, skipping..."
print_success "Imports organized"

echo ""
print_success "All formatting complete! ✨"
