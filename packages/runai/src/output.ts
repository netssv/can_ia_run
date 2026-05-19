import type { CliHardwareInfo, RecommendedModel } from "./types";
import { log } from "@clack/prompts";

const ANSI = {
  reset: "\u001b[0m",
  bold: "\u001b[1m",
  gray: "\u001b[90m",
  cyan: "\u001b[36m",
  green: "\u001b[32m",
  yellow: "\u001b[33m",
  magenta: "\u001b[35m",
};

function paint(text: string, color: string): string {
  if (!process.stdout.isTTY) return text;
  return `${color}${text}${ANSI.reset}`;
}

function key(text: string): string {
  return paint(text, ANSI.bold);
}

function value(text: string, color: string): string {
  return paint(text, color);
}

function quantTag(text: string): string {
  return paint(`[${text}]`, ANSI.gray);
}

function statusLabel(status: RecommendedModel["status"]): string {
  switch (status) {
    case "can-run":
      return "CAN RUN";
    case "tight":
      return "TIGHT";
    case "can-run-slow":
      return "CAN RUN SLOW";
    case "cannot-run":
      return "CANNOT RUN";
    default:
      return "UNKNOWN";
  }
}

function fitScore(score: number): number {
  return Math.max(0, Math.min(100, Math.round(score * 0.72)));
}

export function printHardware(hw: CliHardwareInfo): void {
  const summary = [
    `${value(hw.deviceName || "Unknown", ANSI.cyan)}`,
    `${key("⛁ RAM")} ${value(`${hw.totalUsableRAM ?? "?"} GB`, ANSI.green)}`,
    `${key("⚡ BW")} ${value(`${hw.memoryBandwidth ?? "?"} GB/s`, ANSI.yellow)}`,
  ].join("  |  ");
  log.message(summary, { symbol: "◇" });
}

export function printRecommendations(list: RecommendedModel[]): void {
  if (list.length === 0) {
    log.warn("No viable models found for this machine.");
    return;
  }
  log.step("Top recommendations to install");
  list.forEach((item, index) => {
    const speed = item.expectedTokensPerSec ?? "?";
    const fit = fitScore(item.score);
    log.message(
      `${index + 1}. ${item.name} ${quantTag(item.quant)}\n`
      + `   ${value("☆ Fit:", ANSI.magenta)} ${value(`${fit}/100`, ANSI.green)}\n`
      + `   ${value("⛁ Disk:", ANSI.cyan)} ${item.diskNeededGB} GB   ${value("⛃ VRAM:", ANSI.cyan)} ~${item.memoryNeededGB} GB\n`
      + `   ${value("⚡Speed expected:", ANSI.yellow)} ${value(`~${speed} tok/s`, ANSI.yellow)}`,
      { symbol: "◆" },
    );
  });
}

export function printBrowseResults(list: RecommendedModel[]): void {
  if (list.length === 0) {
    log.warn("No models matched your search.");
    return;
  }
  log.step("Catalog matches");
  for (const [index, item] of list.entries()) {
    log.message(
      `${String(index + 1).padStart(2, " ")}. ${item.name} (${item.id})  [${item.quant}]  ⛁ ${item.diskNeededGB} GB  ⚡ ~${item.expectedTokensPerSec ?? "?"} tok/s  ${statusLabel(item.status)}`,
      { symbol: "•" },
    );
  }
}
