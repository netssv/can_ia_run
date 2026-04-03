import { CHIP_BW_GBS } from "./config";
import type { CliHardwareInfo } from "./types";

function run(command: string, args: string[]): string {
  const result = Bun.spawnSync([command, ...args], { stdout: "pipe", stderr: "pipe" });
  if (result.exitCode !== 0) return "";
  return new TextDecoder().decode(result.stdout).trim();
}

function parseAppleChip(value: string): string | null {
  const lower = value.toLowerCase();
  const candidates = Object.keys(CHIP_BW_GBS).sort((a, b) => b.length - a.length);
  for (const chip of candidates) {
    if (lower.includes(chip)) return chip;
  }
  return null;
}

function parseGpuCores(systemProfile: string): number | null {
  const match = systemProfile.match(/Total Number of Cores:\s*(\d+)/i);
  if (!match) return null;
  return Number.parseInt(match[1], 10);
}

export async function detectMacHardware(): Promise<CliHardwareInfo> {
  const memBytes = run("sysctl", ["-n", "hw.memsize"]);
  const cpuBrand = run("sysctl", ["-n", "machdep.cpu.brand_string"]);
  const cpuCoresRaw = run("sysctl", ["-n", "hw.perflevel0.physicalcpu"]);
  const gpuProfile = run("system_profiler", ["SPDisplaysDataType"]);

  const chip = parseAppleChip(cpuBrand) || "m1";
  const totalRamGB = Math.round((Number(memBytes || "0") / (1024 ** 3)) * 10) / 10 || null;
  const cpuCores = Number.parseInt(cpuCoresRaw || "0", 10) || null;
  const gpuCores = parseGpuCores(gpuProfile);
  const bandwidth = CHIP_BW_GBS[chip] || 68;

  return {
    gpuRenderer: `Apple ${chip.toUpperCase()}`,
    gpuVendor: "Apple",
    gpuCores,
    ramGB: totalRamGB,
    estimatedVRAM: null,
    memoryBandwidth: bandwidth,
    systemRAM: null,
    deviceMemoryRaw: null,
    webgpu: false,
    webgpuDevice: null,
    webgpuArch: chip,
    isAppleSilicon: true,
    totalUsableRAM: totalRamGB,
    platform: "macOS",
    cpuBenchmark: cpuCores ? cpuCores * 10 : null,
    isMobile: false,
    deviceName: `Apple ${chip.toUpperCase()}`,
  };
}
