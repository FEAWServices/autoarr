#!/bin/bash

# Quick runner for post-deployment tests
# This script is a convenience wrapper for the full test suite

cd "$(dirname "$0")/tests/post-deployment"
exec bash run-all-tests.sh
