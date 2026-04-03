export type RunStatus = "can-run" | "tight" | "can-run-slow" | "cannot-run" | "unknown";

export interface CliHardwareInfo {
  gpuRenderer: string | null;
  gpuVendor: string | null;
  gpuCores: number | null;
  ramGB: number | null;
  estimatedVRAM: number | null;
  memoryBandwidth: number | null;
  systemRAM: number | null;
  deviceMemoryRaw: number | null;
  webgpu: boolean;
  webgpuDevice: string | null;
  webgpuArch: string | null;
  isAppleSilicon: boolean;
  totalUsableRAM: number | null;
  platform: string | null;
  cpuBenchmark: number | null;
  isMobile: boolean;
  deviceName: string | null;
}

export interface RecommendedModel {
  id: string;
  name: string;
  provider: string;
  ollamaId?: string;
  sourceUrl: string;
  quant: string;
  score: number;
  grade: string;
  status: RunStatus;
  expectedTokensPerSec: number | null;
  memoryNeededGB: number;
  diskNeededGB: number;
  paramsBillions: number;
  downloaded: boolean;
}
