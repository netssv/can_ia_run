import * as p from "@clack/prompts";
import { basename } from "node:path";
import {
  warmupModel,
  unloadModel,
  isModelLoaded,
  getLoadedModelPath,
  getModelMemoryUsage,
} from "../llamacpp";
import { getPromptOutput, usePromptLegend } from "../prompt-footer";
import { ANSI, paint } from "../terminal";
import { resolveChatModel, stripGguf } from "../cli-utils";

function formatBytes(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes <= 0) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  let value = bytes;
  let idx = 0;
  while (value >= 1024 && idx < units.length - 1) {
    value /= 1024;
    idx += 1;
  }
  return `${value.toFixed(idx < 2 ? 0 : 1)} ${units[idx]}`;
}

export async function handleLoad(args: string[]): Promise<void> {
  let modelPath: string;
  try {
    const resolved = await resolveChatModel(args);
    if (!resolved) return;
    modelPath = resolved;
  } catch (error) {
    p.log.error(error instanceof Error ? error.message : "Unable to resolve model.");
    return;
  }

  const modelName = stripGguf(basename(modelPath));

  if (isModelLoaded() && getLoadedModelPath() === modelPath) {
    p.log.success(`${paint(modelName, ANSI.cyan)} is already loaded.`);
    return;
  }

  const spinner = p.spinner();
  spinner.start(`Loading ${modelName} into memory...`);
  try {
    await warmupModel(modelPath);
    spinner.stop(`${paint(modelName, ANSI.cyan)} loaded and ready.`);
  } catch (error) {
    spinner.stop("Failed to load model");
    p.log.error(error instanceof Error ? error.message : "Model loading failed.");
  }
}

export async function handleUnload(): Promise<void> {
  if (!isModelLoaded()) {
    p.log.warn("No model is currently loaded.");
    return;
  }

  const modelPath = getLoadedModelPath();
  const modelName = modelPath ? stripGguf(basename(modelPath)) : "unknown";

  const spinner = p.spinner();
  spinner.start(`Unloading ${modelName}...`);
  await unloadModel();
  spinner.stop(`${paint(modelName, ANSI.cyan)} unloaded from memory.`);
}

export async function promptLoadAfterInstall(modelPath: string): Promise<boolean> {
  if (!process.stdin.isTTY) return false;

  const modelName = stripGguf(basename(modelPath));

  p.log.info(
    `${paint("Pre-loading keeps the model in RAM for instant responses.", ANSI.gray)}\n` +
    `${paint("Without it, each session starts with a delay while the model loads from disk.", ANSI.gray)}`,
  );

  usePromptLegend("default");
  const shouldLoad = await p.confirm({
    message: `Load ${paint(modelName, ANSI.cyan)} into memory?`,
    output: getPromptOutput(),
  });

  if (p.isCancel(shouldLoad) || !shouldLoad) return false;

  const spinner = p.spinner();
  spinner.start(`Loading ${modelName} into memory...`);
  try {
    await warmupModel(modelPath);
    spinner.stop(`${paint(modelName, ANSI.cyan)} loaded and ready.`);
    return true;
  } catch (error) {
    spinner.stop("Failed to load model");
    p.log.error(error instanceof Error ? error.message : "Model loading failed.");
    return false;
  }
}

export async function handlePs(): Promise<void> {
  if (!isModelLoaded()) {
    p.log.info("No model is currently loaded in memory.");
    return;
  }

  const modelPath = getLoadedModelPath()!;
  const modelName = stripGguf(basename(modelPath));
  const mem = getModelMemoryUsage();

  const lines = [
    `${paint("Model", ANSI.gray, true)}  ${paint(modelName, ANSI.cyan)}`,
    `${paint("Path", ANSI.gray, true)}   ${paint(modelPath, ANSI.gray)}`,
  ];

  if (mem) {
    lines.push(`${paint("RSS", ANSI.gray, true)}    ${paint(formatBytes(mem.rss), ANSI.yellow)}`);
    lines.push(`${paint("Heap", ANSI.gray, true)}   ${paint(formatBytes(mem.heapUsed), ANSI.yellow)}`);
  }

  for (const line of lines) {
    p.log.message(line, { symbol: " " });
  }
}
