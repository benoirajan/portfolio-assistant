#!/usr/bin/env bash

# ==============================================================================
# FolioGuard Live End-to-End Test Suite Wrapper
# Executes live browser, API, and multi-stage advisory validation.
# ==============================================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

chmod +x scripts/test_e2e_live.js

NODE_PATH="$PROJECT_ROOT/frontend/node_modules" node scripts/test_e2e_live.js "$@"
