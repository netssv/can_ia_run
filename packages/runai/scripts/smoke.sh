#!/usr/bin/env bash
set -euo pipefail

echo "== runai smoke test =="

echo "[1/4] recommend"
bun run src/cli.ts recommend --top 3 >/dev/null

echo "[2/4] browse"
bun run src/cli.ts browse qwen --limit 5 >/dev/null

echo "[3/4] openai payload contract via tests"
bun test tests/openai-contract.test.ts >/dev/null

echo "[4/4] recommendation tests"
bun test tests/recommend.test.ts >/dev/null

echo "Smoke test passed."
