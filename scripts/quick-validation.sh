#!/bin/bash

# ==============================================================================
# AutoArr - Quick Validation Script
# ==============================================================================
# Run this BEFORE pushing to catch errors locally (like C's build/link step)
#
# Usage:
#   ./scripts/quick-validation.sh          # Full validation
#   ./scripts/quick-validation.sh --fast   # Fast mode (skip slow checks)
#   ./scripts/quick-validation.sh --fix    # Auto-fix what can be fixed
#   ./scripts/quick-validation.sh --python # Python only
#   ./scripts/quick-validation.sh --frontend # Frontend only
#
# ==============================================================================

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Parse arguments
FAST_MODE=false
FIX_MODE=false
PYTHON_ONLY=false
FRONTEND_ONLY=false

for arg in "$@"; do
  case $arg in
    --fast) FAST_MODE=true ;;
    --fix) FIX_MODE=true ;;
    --python) PYTHON_ONLY=true ;;
    --frontend) FRONTEND_ONLY=true ;;
  esac
done

echo ""
echo "${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo "${CYAN}║        AutoArr - Quick Validation (Pre-Push Check)            ║${NC}"
echo "${CYAN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

ERRORS=0
WARNINGS=0
START_TIME=$(date +%s)

# Determine what to check
CHECK_PYTHON=true
CHECK_FRONTEND=true

if [ "$PYTHON_ONLY" = true ]; then
  CHECK_FRONTEND=false
fi
if [ "$FRONTEND_ONLY" = true ]; then
  CHECK_PYTHON=false
fi

# ==============================================================================
# Step 1: Python Type Checking (MyPy - like TypeScript's tsc)
# ==============================================================================
if [ "$CHECK_PYTHON" = true ]; then
  echo "${BLUE}[1/5] Python Type Check (MyPy)${NC}"
  echo "      This catches type errors across Python files"
  echo ""

  if [ "$FIX_MODE" = false ]; then
    echo "  → Running MyPy..."
    if poetry run mypy autoarr/api/ autoarr/shared/ --config-file=pyproject.toml --ignore-missing-imports 2>&1; then
      echo "  ${GREEN}✓ MyPy: No type errors${NC}"
    else
      echo "  ${YELLOW}⚠ MyPy: Type issues found (non-blocking)${NC}"
      WARNINGS=$((WARNINGS + 1))
    fi
  else
    echo "  ${YELLOW}⏭ MyPy doesn't have auto-fix${NC}"
  fi
  echo ""
fi

# ==============================================================================
# Step 2: Python Linting (Flake8 + Black)
# ==============================================================================
if [ "$CHECK_PYTHON" = true ]; then
  echo "${BLUE}[2/5] Python Lint & Format${NC}"
  echo "      Black (formatting) + Flake8 (linting)"
  echo ""

  if [ "$FIX_MODE" = true ]; then
    echo "  → Auto-formatting with Black..."
    poetry run black autoarr/ 2>&1
    echo "  ${GREEN}✓ Black formatting applied${NC}"

    echo "  → Auto-sorting imports with isort..."
    poetry run isort --profile black autoarr/ 2>&1
    echo "  ${GREEN}✓ Imports sorted${NC}"
  else
    echo "  → Checking Black formatting..."
    if poetry run black --check autoarr/ 2>&1; then
      echo "  ${GREEN}✓ Black: Formatting correct${NC}"
    else
      echo "  ${RED}✗ Black: Formatting issues found${NC}"
      echo "  ${YELLOW}💡 Run with --fix to auto-format${NC}"
      ERRORS=$((ERRORS + 1))
    fi

    echo "  → Checking isort..."
    if poetry run isort --check-only --profile black autoarr/ 2>&1; then
      echo "  ${GREEN}✓ isort: Imports sorted correctly${NC}"
    else
      echo "  ${RED}✗ isort: Import order issues${NC}"
      ERRORS=$((ERRORS + 1))
    fi
  fi

  echo "  → Running Flake8..."
  if poetry run flake8 autoarr/ 2>&1; then
    echo "  ${GREEN}✓ Flake8: No linting issues${NC}"
  else
    echo "  ${RED}✗ Flake8: Linting issues found${NC}"
    ERRORS=$((ERRORS + 1))
  fi
  echo ""
fi

# ==============================================================================
# Step 3: Frontend TypeScript Type Check
# ==============================================================================
if [ "$CHECK_FRONTEND" = true ]; then
  echo "${BLUE}[3/5] Frontend TypeScript Type Check${NC}"
  echo "      This catches type errors in React/TypeScript code"
  echo ""

  echo "  → Running tsc --noEmit..."
  if cd autoarr/ui && pnpm exec tsc --noEmit 2>&1; then
    echo "  ${GREEN}✓ TypeScript: No type errors${NC}"
  else
    echo "  ${RED}✗ TypeScript: Type errors found${NC}"
    ERRORS=$((ERRORS + 1))
  fi
  cd ../..
  echo ""
fi

# ==============================================================================
# Step 4: Frontend ESLint
# ==============================================================================
if [ "$CHECK_FRONTEND" = true ]; then
  echo "${BLUE}[4/5] Frontend ESLint${NC}"
  echo "      Static analysis for React/TypeScript"
  echo ""

  ESLINT_OPTS=""
  if [ "$FIX_MODE" = true ]; then
    ESLINT_OPTS="--fix"
  fi

  echo "  → Running ESLint..."
  if cd autoarr/ui && pnpm run lint $ESLINT_OPTS 2>&1; then
    echo "  ${GREEN}✓ ESLint: No issues${NC}"
  else
    echo "  ${RED}✗ ESLint: Issues found${NC}"
    if [ "$FIX_MODE" = false ]; then
      echo "  ${YELLOW}💡 Run with --fix to auto-fix some issues${NC}"
    fi
    ERRORS=$((ERRORS + 1))
  fi
  cd ../..
  echo ""
fi

# ==============================================================================
# Step 5: Build Test (optional)
# ==============================================================================
echo "${BLUE}[5/5] Build Verification${NC}"
echo "      Quick build test to ensure everything compiles"
echo ""

if [ "$FAST_MODE" = false ]; then
  if [ "$CHECK_FRONTEND" = true ]; then
    echo "  → Building frontend..."
    if cd autoarr/ui && pnpm run build 2>&1 | tail -3; then
      echo "  ${GREEN}✓ Frontend build succeeded${NC}"
    else
      echo "  ${RED}✗ Frontend build failed${NC}"
      ERRORS=$((ERRORS + 1))
    fi
    cd ../..
  fi

  if [ "$CHECK_PYTHON" = true ]; then
    echo "  → Verifying Python imports..."
    if poetry run python -c "import autoarr.api; import autoarr.shared" 2>&1; then
      echo "  ${GREEN}✓ Python imports verified${NC}"
    else
      echo "  ${RED}✗ Python import errors${NC}"
      ERRORS=$((ERRORS + 1))
    fi
  fi
else
  echo "  ${YELLOW}⏭ Skipped in fast mode${NC}"
fi

# ==============================================================================
# Summary
# ==============================================================================
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
echo "${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo "${CYAN}║                      Validation Summary                       ║${NC}"
echo "${CYAN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "  Duration: ${DURATION}s"
echo "  Errors:   ${ERRORS}"
echo "  Warnings: ${WARNINGS}"
echo ""

if [ $ERRORS -gt 0 ]; then
  echo "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo "${RED}  ✗ VALIDATION FAILED - Fix errors before pushing!${NC}"
  echo "${RED}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo ""
  echo "  Tips:"
  echo "  • Python: poetry run black autoarr/ && poetry run isort --profile black autoarr/"
  echo "  • Frontend: cd autoarr/ui && pnpm run lint --fix"
  echo "  • Auto-fix: ./scripts/quick-validation.sh --fix"
  echo ""
  exit 1
elif [ $WARNINGS -gt 0 ]; then
  echo "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo "${YELLOW}  ⚠ VALIDATION PASSED WITH WARNINGS${NC}"
  echo "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo ""
  echo "  You can push, but consider addressing warnings."
  echo ""
  exit 0
else
  echo "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo "${GREEN}  ✓ ALL CHECKS PASSED - Safe to push!${NC}"
  echo "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo ""
  exit 0
fi
