import { existsSync } from "node:fs";
import { models } from "../../../src/data/models.ts";
import { evaluateModelComplete } from "../../../src/lib/hardware.ts";
import type { RecommendedModel, CliHardwareInfo } from "./types";
import { modelPathFromId } from "./model-store";

const OFFICIAL_MODEL_URLS = new Set([
  "https://huggingface.co/lmstudio-community/Qwen3-0.6B-GGUF",
  "https://huggingface.co/lmstudio-community/Qwen3.5-9B-GGUF",
  "https://huggingface.co/lmstudio-community/Qwen3.5-4B-GGUF",
  "https://huggingface.co/lmstudio-community/Qwen3.5-2B-GGUF",
  "https://huggingface.co/lmstudio-community/Qwen3.5-0.8B-GGUF",
  "https://huggingface.co/lmstudio-community/Qwen3.5-35B-A3B-GGUF",
  "https://huggingface.co/lmstudio-community/Qwen3.5-122B-A10B-GGUF",
  "https://huggingface.co/lmstudio-community/Qwen3.5-27B-GGUF",
]);

const catalogModels = models.filter((model) => OFFICIAL_MODEL_URLS.has(model.url));
type CatalogModel = (typeof catalogModels)[number];

function parseReleaseDate(value: string | null): number | null {
  if (!value) return null;
  const parsed = Date.parse(`${value}-01`);
  return Number.isFinite(parsed) ? parsed : null;
}

const releaseTimeline = catalogModels
  .map((model) => parseReleaseDate(model.releaseDate))
  .filter((value): value is number => value !== null);
const minReleaseTs = releaseTimeline.length ? Math.min(...releaseTimeline) : 0;
const maxReleaseTs = releaseTimeline.length ? Math.max(...releaseTimeline) : 1;

function recencyScore(releaseDate: string | null): number {
  const ts = parseReleaseDate(releaseDate);
  if (ts === null || maxReleaseTs <= minReleaseTs) return 0;
  const normalized = (ts - minReleaseTs) / (maxReleaseTs - minReleaseTs);
  return normalized * 20;
}

function memorySweetSpotScore(memPct: number | null): number {
  if (memPct === null) return 0;
  const distance = Math.abs(memPct - 65);
  return Math.max(0, 20 - distance * 0.5);
}

function paramsQualityScore(paramsBillions: number): number {
  return Math.min(56, Math.log2(paramsBillions + 1) * 10);
}

function statusPreference(status: RecommendedModel["status"]): number {
  if (status === "can-run") return 12;
  if (status === "tight") return 4;
  if (status === "can-run-slow") return -16;
  return -30;
}

function speedPenalty(toksPerSec: number | null): number {
  if (toksPerSec === null) return 0;
  if (toksPerSec >= 16) return 0;
  return -Math.min(25, (16 - toksPerSec) * 2.2);
}

function modelCapabilityBonus(model: CatalogModel): number {
  let bonus = 0;
  if (model.tools) bonus += 2;
  if (model.thinking) bonus += 2;
  if (model.featured) bonus += 1.5;
  return bonus;
}

function computeRankingScore(
  model: CatalogModel,
  quantBits: number,
  evalScore: number,
  status: RecommendedModel["status"],
  toksPerSec: number | null,
  memPct: number | null,
): number {
  const score =
    evalScore * 0.45
    + paramsQualityScore(model.paramsBillions)
    + Math.min(24, model.paramsBillions * 0.45)
    + recencyScore(model.releaseDate)
    + memorySweetSpotScore(memPct)
    + statusPreference(status)
    + modelCapabilityBonus(model)
    + (quantBits * 1.1)
    + speedPenalty(toksPerSec);
  return Math.round(score);
}

function compareRecommendations(a: RecommendedModel, b: RecommendedModel): number {
  if (b.score !== a.score) return b.score - a.score;
  if (b.paramsBillions !== a.paramsBillions) return b.paramsBillions - a.paramsBillions;
  if (a.memoryNeededGB !== b.memoryNeededGB) return b.memoryNeededGB - a.memoryNeededGB;
  return a.name.localeCompare(b.name);
}

function pickBestQuant(
  model: CatalogModel,
  hw: CliHardwareInfo,
): RecommendedModel | null {
  const byQuality = [...model.quants].sort((a, b) => b.bits - a.bits);
  let best: RecommendedModel | null = null;

  for (const quant of byQuality) {
    const evalResult = evaluateModelComplete(quant.vramGB, hw, model.paramsBillions);
    if (evalResult.status === "cannot-run" || evalResult.status === "unknown") continue;
    const downloaded = existsSync(modelPathFromId(model.id));
    const diskNeededGB = Math.round((quant.vramGB * 1.05) * 10) / 10;
    const rankingScore = computeRankingScore(
      model,
      quant.bits,
      evalResult.score,
      evalResult.status,
      evalResult.toksPerSec,
      evalResult.memPct,
    );

    const candidate: RecommendedModel = {
      id: model.id,
      name: model.name,
      provider: model.provider,
      ollamaId: model.ollamaId,
      sourceUrl: model.url,
      quant: quant.name,
      score: Math.round(rankingScore),
      grade: evalResult.grade,
      status: evalResult.status,
      expectedTokensPerSec: evalResult.toksPerSec,
      memoryNeededGB: quant.vramGB,
      diskNeededGB,
      paramsBillions: model.paramsBillions,
      downloaded,
    };

    if (
      !best
      || candidate.score > best.score
      || (candidate.score === best.score && candidate.paramsBillions > best.paramsBillions)
    ) {
      best = candidate;
    }
  }

  return best;
}

export function recommendTopModels(hw: CliHardwareInfo, limit = 3): RecommendedModel[] {
  const candidates: RecommendedModel[] = [];
  for (const model of catalogModels) {
    const best = pickBestQuant(model, hw);
    if (best) candidates.push(best);
  }
  return candidates.sort(compareRecommendations).slice(0, limit);
}

export function searchCatalog(query: string, hw: CliHardwareInfo, limit = 25): RecommendedModel[] {
  const q = query.toLowerCase().trim();
  const results: RecommendedModel[] = [];
  for (const model of catalogModels) {
    if (!q) {
      const best = pickBestQuant(model, hw);
      if (best) results.push(best);
      continue;
    }
    const haystack = [
      model.name,
      model.provider,
      model.family,
      model.id,
      ...(model.useCase || []),
      model.ollamaId || "",
    ].join(" ").toLowerCase();
    if (!haystack.includes(q)) continue;
    const best = pickBestQuant(model, hw);
    if (best) results.push(best);
  }
  return results.sort(compareRecommendations).slice(0, limit);
}
