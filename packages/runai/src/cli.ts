#!/usr/bin/env bun
import { handleBrowse, handleChat, handleDoctor, handleHome, handlePull, handleRecommend, handleServe } from "./commands";

function setupHardExitOnCtrlC(): void {
  let exiting = false;
  const hardExit = (): void => {
    if (exiting) return;
    exiting = true;
    process.stdout.write("\n");
    process.exit(130);
  };

  process.on("SIGINT", hardExit);
  if (process.stdin.isTTY) {
    process.stdin.on("data", (chunk: string | Buffer) => {
      if (typeof chunk !== "string" && chunk.length === 1 && chunk[0] === 0x03) {
        hardExit();
      }
    });
  }
}

function printHelp(): void {
  console.log(`
runai - local AI runtime for macOS (Bun + llama.cpp)

Usage:
  runai
  runai recommend [--top 3] [--install [1,2|all|model-id]] [--json]
  runai browse [query] [--limit 25] [--json]
  runai pull <gguf-url> [--name model.gguf]
  runai chat [--model <path-or-id>]
  runai doctor [--json] [--model <path-or-file>]
  runai serve [--model <path-or-id>] [--port 11435]
  runai api [--model <path-or-id>] [--port 11435]
  runai --help

Notes:
  - Recommendations are based on canirun.ai scoring logic.
  - API compatibility: /v1/models, /v1/chat/completions, /v1/completions.
  - Anonymous telemetry can be disabled with RUNAI_TELEMETRY_DISABLED=1.
`);
}

async function main(): Promise<void> {
  const [, , cmd, ...args] = process.argv;

  if (!cmd) {
    await handleHome();
    return;
  }

  if (cmd === "--help" || cmd === "-h" || cmd === "help") {
    printHelp();
    return;
  }
  if (cmd === "--version" || cmd === "-v") {
    console.log("runai 0.1.0");
    return;
  }

  if (cmd === "recommend") {
    await handleRecommend(args);
    return;
  }
  if (cmd === "browse") {
    await handleBrowse(args);
    return;
  }
  if (cmd === "pull") {
    await handlePull(args);
    return;
  }
  if (cmd === "serve" || cmd === "api") {
    await handleServe(args);
    return;
  }
  if (cmd === "chat") {
    await handleChat(args);
    return;
  }
  if (cmd === "doctor") {
    await handleDoctor(args);
    return;
  }

  console.error(`Unknown command: ${cmd}`);
  printHelp();
  process.exit(1);
}

setupHardExitOnCtrlC();
await main();
