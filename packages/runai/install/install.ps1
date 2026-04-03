Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "Installing runai (Windows)..."

$bun = Get-Command bun -ErrorAction SilentlyContinue
if (-not $bun) {
  Write-Host "Bun not found. Installing Bun..."
  powershell -c "irm bun.sh/install.ps1 | iex"

  if (-not $env:BUN_INSTALL -or $env:BUN_INSTALL.Trim() -eq "") {
    $env:BUN_INSTALL = Join-Path $HOME ".bun"
  }
  $bunBin = Join-Path $env:BUN_INSTALL "bin"
  if (Test-Path $bunBin) {
    $env:Path = "$bunBin;$env:Path"
  }
}

$bun = Get-Command bun -ErrorAction SilentlyContinue
if (-not $bun) {
  Write-Error "Bun installation failed or Bun is not available in PATH. Reopen your terminal and run this script again."
}

Write-Host "Installing runai globally from npm registry..."
bun install -g runai

Write-Host ""
Write-Host "Done."
Write-Host "Try:"
Write-Host "  runai recommend"
Write-Host "  runai browse qwen"
Write-Host "  runai serve --model C:\path\to\model.gguf --port 11435"
