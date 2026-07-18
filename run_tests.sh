#!/usr/bin/env bash
# akashi — clj/bb test suite (ADR-2606160842 py->clj port wave); wired into the fleet green-check.
set -euo pipefail
cd "$(dirname "$0")"
exec bb test
