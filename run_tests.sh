#!/usr/bin/env bash
# akashi — clj/bb test suite (ADR-2606160842 py->clj port wave); wired into the fleet green-check.
set -euo pipefail
cd "$(dirname "$0")/../.."
exec bb -e '(require (quote clojure.test) (quote akashi.adapters.test-dry-run-fixtures) (quote akashi.adapters.test-regulator-bulk-fixture-parser) (quote akashi.adapters.test-lexicon-shape-validator))(let [r (clojure.test/run-tests (quote akashi.adapters.test-dry-run-fixtures) (quote akashi.adapters.test-regulator-bulk-fixture-parser) (quote akashi.adapters.test-lexicon-shape-validator))](System/exit (if (zero? (+ (:fail r) (:error r))) 0 1)))'
