import { createWriteStream } from "node:fs";
import { rename, stat, unlink } from "node:fs/promises";
import { ensureModelDir, modelPathFromUrl } from "./model-store";

const ANSI = {
  reset: "\u001b[0m",
  cyan: "\u001b[36m",
  yellow: "\u001b[33m",
  hideCursor: "\u001b[?25l",
  showCursor: "\u001b[?25h",
};

const BYTES_FIELD_WIDTH = 20;
const SPEED_FIELD_WIDTH = 12;

function paint(text: string, color: string): string {
  if (!process.stdout.isTTY) return text;
  return `${color}${text}${ANSI.reset}`;
}

function waveGradient(text: string, phase: number): string {
  if (!process.stdout.isTTY) return text;
  const chars = [...text];
  return chars.map((ch, index) => {
    // Animated yellow-orange wave. Keeps high contrast while moving over time.
    const t = (index + phase) * 0.55;
    const mix = (Math.sin(t) + 1) / 2; // 0..1
    const r = Math.round(245 + (255 - 245) * mix);
    const g = Math.round(165 + (235 - 165) * mix);
    const b = Math.round(40 + (120 - 40) * mix);
    return `\u001b[38;2;${r};${g};${b}m${ch}`;
  }).join("") + ANSI.reset;
}

function clampPercent(value: number): number {
  if (!Number.isFinite(value)) return 0;
  if (value < 0) return 0;
  if (value > 100) return 100;
  return Math.round(value);
}

function formatBytes(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes <= 0) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let value = bytes;
  let idx = 0;
  while (value >= 1024 && idx < units.length - 1) {
    value /= 1024;
    idx += 1;
  }
  return `${value.toFixed(idx < 2 ? 0 : 1)} ${units[idx]}`;
}

function formatSpeed(bytesPerSecond: number): string {
  if (!Number.isFinite(bytesPerSecond) || bytesPerSecond <= 0) return "0 B/s";
  return `${formatBytes(bytesPerSecond)}/s`;
}

export function formatBar(percent: number, width = 28): string {
  const safe = clampPercent(percent);
  const filled = Math.round((safe / 100) * width);
  const empty = width - filled;
  return `${"█".repeat(filled)}${"░".repeat(empty)}`;
}

export function renderTwoLineBlock(line1: string, line2: string, hasRendered: boolean): boolean {
  if (!process.stdout.isTTY) return hasRendered;
  if (!hasRendered) {
    process.stdout.write(`${line1}\n${line2}`);
    return true;
  }
  process.stdout.write("\r\u001b[2K\u001b[1A\r\u001b[2K");
  process.stdout.write(`${line1}\n${line2}`);
  return true;
}

export function clearTwoLineBlock(hasRendered: boolean): void {
  if (!process.stdout.isTTY || !hasRendered) return;
  process.stdout.write("\r\u001b[2K\u001b[1A\r\u001b[2K\r");
}

export function setCursorVisible(visible: boolean): void {
  if (!process.stdout.isTTY) return;
  process.stdout.write(visible ? ANSI.showCursor : ANSI.hideCursor);
}

export async function pullModel(url: string, explicitName?: string, label = "download"): Promise<string> {
  await ensureModelDir();
  const targetPath = modelPathFromUrl(url, explicitName);
  const tempPath = `${targetPath}.part-${process.pid}-${Date.now()}`;
  const response = await fetch(url);
  if (!response.ok || !response.body) {
    throw new Error(`Download failed: ${response.status} ${response.statusText}`);
  }

  const total = Number(response.headers.get("content-length") || "0");
  const file = createWriteStream(tempPath);
  const reader = response.body.getReader();
  let downloaded = 0;
  let lastUpdate = 0;
  let lastPercentPrinted = -1;
  let spinnerTick = 0;
  let lastSampleTime = Date.now();
  let lastSampleBytes = 0;
  let speedBps = 0;
  let renderedTwoLineBlock = false;
  let gradientPhase = 0;
  const spinnerFrames = ["◐", "◓", "◑", "◒"];
  let cursorHidden = false;

  try {
    if (process.stdout.isTTY) {
      setCursorVisible(false);
      cursorHidden = true;
    }

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      if (!value) continue;
      downloaded += value.length;
      file.write(Buffer.from(value));
      const now = Date.now();
      if (now - lastUpdate < 80) continue;
      lastUpdate = now;
      const elapsedMs = now - lastSampleTime;
      if (elapsedMs > 0) {
        const deltaBytes = downloaded - lastSampleBytes;
        const instantBps = (deltaBytes / elapsedMs) * 1000;
        // Lightweight smoothing keeps speed stable without hiding real changes.
        speedBps = speedBps > 0 ? (speedBps * 0.7) + (instantBps * 0.3) : instantBps;
        lastSampleTime = now;
        lastSampleBytes = downloaded;
      }
      if (total > 0) {
        const pct = clampPercent((downloaded / total) * 100);
        if (pct !== lastPercentPrinted || process.stdout.isTTY) {
          lastPercentPrinted = pct;
          if (process.stdout.isTTY) {
            const bar = formatBar(pct);
            const pctLabel = `${String(pct).padStart(3, " ")}%`;
            const bytesText = `${formatBytes(downloaded)}/${formatBytes(total)}`.padEnd(BYTES_FIELD_WIDTH, " ");
            const speedText = formatSpeed(speedBps).padEnd(SPEED_FIELD_WIDTH, " ");
            const line1 = `✓ Installing ${label} [${bar}] ${pctLabel}`;
            const line2 = `${paint("⛁", ANSI.cyan)} ${paint(bytesText, ANSI.cyan)}  ${waveGradient(`⚡ ${speedText}`, gradientPhase)}`;
            gradientPhase += 1;
            renderedTwoLineBlock = renderTwoLineBlock(line1, line2, renderedTwoLineBlock);
          } else if (pct % 10 === 0) {
            console.log(
              `Installing ${label} (${pct}%) ${formatBytes(downloaded)}/${formatBytes(total)} ${formatSpeed(speedBps)}`,
            );
          }
        }
      } else {
        spinnerTick += 1;
        const frame = spinnerFrames[spinnerTick % spinnerFrames.length];
        if (process.stdout.isTTY) {
          const bytesText = formatBytes(downloaded).padEnd(BYTES_FIELD_WIDTH, " ");
          const speedText = formatSpeed(speedBps).padEnd(SPEED_FIELD_WIDTH, " ");
          const line1 = `${frame} Installing ${label}`;
          const line2 = `${paint("⛁", ANSI.cyan)} ${paint(bytesText, ANSI.cyan)}  ${waveGradient(`⚡ ${speedText}`, gradientPhase)}`;
          gradientPhase += 1;
          renderedTwoLineBlock = renderTwoLineBlock(line1, line2, renderedTwoLineBlock);
        } else if (downloaded % (5 * 1024 * 1024) < value.length) {
          console.log(`Installing ${label} ${formatBytes(downloaded)} ${formatSpeed(speedBps)}`);
        }
      }
    }

    await new Promise<void>((resolve, reject) => {
      file.once("error", reject);
      file.end(() => resolve());
    });
    await rename(tempPath, targetPath);
    const details = await stat(targetPath);
    console.log(`Installed ${label} (${formatBytes(details.size)})`);
    return targetPath;
  } catch (error) {
    file.destroy();
    await unlink(tempPath).catch(() => {});
    throw error;
  } finally {
    clearTwoLineBlock(renderedTwoLineBlock);
    if (cursorHidden) setCursorVisible(true);
  }
}
