# runai

Local AI runtime with hardware-aware model recommendations and an OpenAI-compatible API.

## Features

- GGUF model recommendations optimized for your machine.
- Guided model installation from the official catalog.
- Local terminal chat with streaming output.
- OpenAI-compatible local API (`/v1/chat/completions`, `/v1/completions`, `/v1/models`).
- `doctor` command to validate runtime, environment, and installed models.

## Requirements

- Supported installer platforms: macOS, Linux, and Windows.
- Model recommendation quality is currently optimized for macOS/Apple Silicon.
- [Bun](https://bun.sh/) installed.

## Development Setup

```bash
cd packages/runai
bun install
```

To run the local CLI binary:

```bash
bun run src/cli.ts --help
```

## Quick Start

### 1) Recommend and install models

```bash
bun run src/cli.ts recommend
```

Useful options:

```bash
bun run src/cli.ts recommend --top 5
bun run src/cli.ts recommend --json
bun run src/cli.ts recommend --install all
bun run src/cli.ts recommend --install 1,2
bun run src/cli.ts recommend --install qwen3-0.6b
```

### 2) Browse the catalog

```bash
bun run src/cli.ts browse qwen --limit 10
bun run src/cli.ts browse --json
```

### 3) Pull a GGUF model manually

```bash
bun run src/cli.ts pull "https://huggingface.co/<repo>/resolve/main/model.gguf?download=true" --name my-model.gguf
```

### 4) Start local interactive chat

```bash
bun run src/cli.ts chat
```

You can also pass a model path or ID:

```bash
bun run src/cli.ts chat --model /path/to/model.gguf
bun run src/cli.ts chat --model qwen3-0.6b
```

### 5) Start the OpenAI-compatible API

```bash
bun run src/cli.ts serve --model /path/to/model.gguf --port 11435
```

Equivalent alias:

```bash
bun run src/cli.ts api --model /path/to/model.gguf
```

Endpoints:

- `GET /health`
- `GET /v1/models`
- `POST /v1/chat/completions`
- `POST /v1/completions`

`chat.completions` example:

```bash
curl -s http://localhost:11435/v1/chat/completions \
  -H "content-type: application/json" \
  -d '{
    "model":"local",
    "messages":[{"role":"user","content":"Give me a short sentence about Bun"}],
    "stream": false
  }'
```

Streaming example:

```bash
curl -N http://localhost:11435/v1/chat/completions \
  -H "content-type: application/json" \
  -d '{
    "model":"local",
    "messages":[{"role":"user","content":"Count to 5"}],
    "stream": true
  }'
```

## Doctor Command

Validates runtime, directory access, `node-llama-cpp`, and model consistency:

```bash
bun run src/cli.ts doctor
bun run src/cli.ts doctor --json
bun run src/cli.ts doctor --model /path/to/model.gguf
```

## Environment Variables

- `RUNAI_MODEL_DIR`: model directory (default: `~/.runai/models`).
- `RUNAI_HOME_DIR`: home directory (default: `~/.runai`).
- `RUNAI_DB_PATH`: SQLite path for installed models (default: `~/.runai/runai.db`).
- `RUNAI_PORT`: default API port (default: `11435`).
- `RUNAI_MODEL`: default model for `serve/api`.
- `RUNAI_TELEMETRY_DISABLED=1`: disables anonymous telemetry.
- `RUNAI_TELEMETRY_ENDPOINT`: telemetry endpoint (optional).

## Package Scripts

```bash
bun run dev
bun run build
bun run test
bun run recommend
bun run browse
bun run serve
bun run api
```

Smoke test:

```bash
./scripts/smoke.sh
```

## Quick Installer

macOS / Linux:

```bash
./install/install.sh
```

Windows (PowerShell):

```powershell
.\install\install.ps1
```

These scripts install Bun if needed and then install `runai` globally.
