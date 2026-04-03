#!/usr/bin/env bash
set -euo pipefail

OS="$(uname -s)"
case "${OS}" in
  Darwin) OS_LABEL="macOS" ;;
  Linux) OS_LABEL="Linux" ;;
  *)
    echo "Unsupported OS: ${OS}"
    echo "Use the Windows installer on PowerShell: ./install/install.ps1"
    exit 1
    ;;
esac

echo "Installing runai (${OS_LABEL})..."

if ! command -v bun >/dev/null 2>&1; then
  echo "Bun not found. Installing Bun..."
  curl -fsSL https://bun.sh/install | bash
  export BUN_INSTALL="${HOME}/.bun"
  export PATH="${BUN_INSTALL}/bin:${PATH}"
fi

if ! command -v bun >/dev/null 2>&1; then
  echo "Bun installation failed or Bun is not in PATH."
  echo "Please add ~/.bun/bin to your PATH and run this installer again."
  exit 1
fi

echo "Installing runai globally from npm registry..."
bun install -g runai

echo ""
echo "Done."
echo "Try:"
echo "  runai recommend"
echo "  runai browse qwen"
echo "  runai serve --model /path/to/model.gguf --port 11435"
