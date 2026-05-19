import { pullModel } from "./pull";
import { log } from "@clack/prompts";
import type { RecommendedModel } from "./types";

interface HuggingFaceModelApi {
  siblings?: Array<{ rfilename?: string }>;
}

function getRepoFromModelUrl(modelUrl: string): string {
  let parsed: URL;
  try {
    parsed = new URL(modelUrl);
  } catch {
    throw new Error(`Invalid model URL: ${modelUrl}`);
  }
  if (parsed.hostname !== "huggingface.co") {
    throw new Error(`Unsupported source host (${parsed.hostname}). Only Hugging Face is supported for now.`);
  }
  const parts = parsed.pathname.split("/").filter(Boolean);
  if (parts.length < 2) {
    throw new Error(`Cannot parse Hugging Face repo from URL: ${modelUrl}`);
  }
  return `${parts[0]}/${parts[1]}`;
}

function stripNonAlnum(s: string): string {
  return s.toLowerCase().replace(/[^a-z0-9]/g, "");
}

function scoreCandidate(filename: string, quantName: string): number {
  const lower = filename.toLowerCase();
  const stripped = stripNonAlnum(filename);
  const quantLower = quantName.toLowerCase();
  const quantStripped = stripNonAlnum(quantName);
  let score = 0;
  if (lower.includes(quantLower)) score += 100;
  else if (stripped.includes(quantStripped)) score += 80;
  if (lower.includes("instruct")) score += 5;
  if (lower.includes("chat")) score += 3;
  if (lower.includes("q4_")) score += 2;
  if (lower.includes("q5_")) score += 2;
  if (lower.includes("q6_")) score += 2;
  if (lower.includes("q8_")) score += 1;
  return score;
}

function isMainModelGGUF(fileName: string): boolean {
  const normalized = fileName.toLowerCase();
  const blockedTokens = [
    "mmproj",
    "clip",
    "projector",
    "vision",
    "image",
    "encoder",
    "embed",
    "embedding",
    "rerank",
    "tei",
    "vocoder",
  ];
  return !blockedTokens.some((token) => normalized.includes(token));
}

function pickBestGGUFFile(files: string[], quantName: string): string | undefined {
  const preferredFiles = files.filter(isMainModelGGUF);
  const ranked = [...(preferredFiles.length > 0 ? preferredFiles : files)]
    .map((filename) => ({
      filename,
      score: scoreCandidate(filename, quantName),
    }))
    .sort((a, b) => b.score - a.score || a.filename.length - b.filename.length);
  return ranked[0]?.filename;
}

async function fetchRepoMetadata(repo: string): Promise<HuggingFaceModelApi | null> {
  const metadataUrl = `https://huggingface.co/api/models/${repo}`;
  const response = await fetch(metadataUrl);
  if (!response.ok) {
    return null;
  }
  return await response.json() as HuggingFaceModelApi;
}

function getGGUFFiles(payload: HuggingFaceModelApi): string[] {
  return (payload.siblings || [])
    .map((item) => item.rfilename || "")
    .filter((name) => name.toLowerCase().endsWith(".gguf"));
}

async function resolveHfGGUFDownload(model: RecommendedModel): Promise<{ url: string; repo: string; file: string }> {
  const sourceRepo = getRepoFromModelUrl(model.sourceUrl);
  const metadata = await fetchRepoMetadata(sourceRepo);
  if (!metadata) {
    throw new Error(`Cannot access Hugging Face metadata for official repo ${sourceRepo}.`);
  }

  const ggufs = getGGUFFiles(metadata);
  if (ggufs.length === 0) {
    throw new Error(
      `Official repo ${sourceRepo} does not expose GGUF files. Use \`runai pull <gguf-url>\` or choose another official model.`,
    );
  }

  const file = pickBestGGUFFile(ggufs, model.quant);
  if (!file) {
    throw new Error(`No suitable GGUF file found in official repo ${sourceRepo}.`);
  }

  const encodedFile = encodeURIComponent(file).replace(/%2F/g, "/");
  const url = `https://huggingface.co/${sourceRepo}/resolve/main/${encodedFile}?download=true`;
  return { url, repo: sourceRepo, file };
}

export async function installCatalogModel(model: RecommendedModel): Promise<{
  path: string;
  sourceRepo: string;
  sourceFile: string;
  sourceUrl: string;
}> {
  const resolved = await resolveHfGGUFDownload(model);
  log.info(`Source: ${resolved.repo}`);
  log.info(`File: ${resolved.file}`);
  console.log("");
  const installedPath = await pullModel(resolved.url, `${model.id}.gguf`, model.id);
  log.success(`Saved at ${installedPath}`);
  return {
    path: installedPath,
    sourceRepo: resolved.repo,
    sourceFile: resolved.file,
    sourceUrl: resolved.url,
  };
}

