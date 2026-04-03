import { RUNAI_TELEMETRY_DISABLED, RUNAI_TELEMETRY_ENDPOINT, RUNAI_VERSION } from "./config";
import type { CliHardwareInfo, RecommendedModel } from "./types";

interface TelemetryBase {
  event: string;
  timestamp: string;
  runaiVersion: string;
  anonymous: true;
}

interface RecommendEvent extends TelemetryBase {
  event: "recommendation_generated";
  hardware: {
    platform: string | null;
    deviceClass: "apple_silicon" | "discrete_or_other";
    ramBucketGB: number | null;
    bandwidthBucketGBs: number | null;
  };
  recommendations: Array<{
    modelId: string;
    quant: string;
    score: number;
    status: string;
    expectedTokensPerSec: number | null;
    memoryNeededGB: number;
  }>;
}

interface BrowseEvent extends TelemetryBase {
  event: "catalog_browse";
  queryLength: number;
  resultCount: number;
}

interface InferenceEvent extends TelemetryBase {
  event: "inference_completed";
  model: string;
  stream: boolean;
  success: boolean;
  latencyMs: number;
  outputTokensApprox: number;
  temperature: number;
  maxTokens: number;
}

type TelemetryPayload = RecommendEvent | BrowseEvent | InferenceEvent;

function bucket(value: number | null, step: number): number | null {
  if (value === null || Number.isNaN(value) || value <= 0) return null;
  return Math.round(value / step) * step;
}

function base(event: TelemetryPayload["event"]): TelemetryBase {
  return {
    event,
    timestamp: new Date().toISOString(),
    runaiVersion: RUNAI_VERSION,
    anonymous: true,
  };
}

async function postTelemetry(payload: TelemetryPayload): Promise<void> {
  if (RUNAI_TELEMETRY_DISABLED) return;
  const ctrl = new AbortController();
  const timeout = setTimeout(() => ctrl.abort(), 1200);
  try {
    await fetch(RUNAI_TELEMETRY_ENDPOINT, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(payload),
      signal: ctrl.signal,
    });
  } catch {
    // best effort only: telemetry never blocks CLI flow
  } finally {
    clearTimeout(timeout);
  }
}

export function createRecommendationTelemetryPayload(hw: CliHardwareInfo, recommendations: RecommendedModel[]): RecommendEvent {
  return {
    ...base("recommendation_generated"),
    hardware: {
      platform: hw.platform,
      deviceClass: hw.isAppleSilicon ? "apple_silicon" : "discrete_or_other",
      ramBucketGB: bucket(hw.totalUsableRAM, 4),
      bandwidthBucketGBs: bucket(hw.memoryBandwidth, 25),
    },
    recommendations: recommendations.map((item) => ({
      modelId: item.id,
      quant: item.quant,
      score: item.score,
      status: item.status,
      expectedTokensPerSec: item.expectedTokensPerSec,
      memoryNeededGB: item.memoryNeededGB,
    })),
  };
}

export function sendRecommendationTelemetry(hw: CliHardwareInfo, recommendations: RecommendedModel[]): void {
  const payload = createRecommendationTelemetryPayload(hw, recommendations);
  void postTelemetry(payload);
}

export function createBrowseTelemetryPayload(query: string, resultCount: number): BrowseEvent {
  return {
    ...base("catalog_browse"),
    queryLength: query.trim().length,
    resultCount,
  };
}

export function sendBrowseTelemetry(query: string, resultCount: number): void {
  const payload = createBrowseTelemetryPayload(query, resultCount);
  void postTelemetry(payload);
}

export function createInferenceTelemetryPayload(input: {
  model: string;
  stream: boolean;
  success: boolean;
  latencyMs: number;
  outputText: string;
  temperature: number;
  maxTokens: number;
}): InferenceEvent {
  return {
    ...base("inference_completed"),
    model: input.model,
    stream: input.stream,
    success: input.success,
    latencyMs: Math.round(input.latencyMs),
    outputTokensApprox: input.outputText.trim() ? input.outputText.trim().split(/\s+/).length : 0,
    temperature: input.temperature,
    maxTokens: input.maxTokens,
  };
}

export function sendInferenceTelemetry(input: {
  model: string;
  stream: boolean;
  success: boolean;
  latencyMs: number;
  outputText: string;
  temperature: number;
  maxTokens: number;
}): void {
  const payload = createInferenceTelemetryPayload(input);
  void postTelemetry(payload);
}
