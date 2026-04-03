import { basename, join } from "node:path";
import { mkdir, readdir } from "node:fs/promises";
import { RUNAI_MODEL_DIR } from "./config";

export async function ensureModelDir(): Promise<string> {
  await mkdir(RUNAI_MODEL_DIR, { recursive: true });
  return RUNAI_MODEL_DIR;
}

export function sanitizeModelFileName(name: string): string {
  return name.replace(/[^a-zA-Z0-9._-]/g, "-").replace(/-+/g, "-").toLowerCase();
}

export function modelPathFromId(id: string): string {
  const file = sanitizeModelFileName(id.endsWith(".gguf") ? id : `${id}.gguf`);
  return join(RUNAI_MODEL_DIR, file);
}

export function modelPathFromUrl(url: string, explicitName?: string): string {
  const fromUrl = basename(new URL(url).pathname) || "model.gguf";
  const file = sanitizeModelFileName(explicitName || fromUrl);
  return join(RUNAI_MODEL_DIR, file.endsWith(".gguf") ? file : `${file}.gguf`);
}

export async function listInstalledModelPaths(): Promise<string[]> {
  await ensureModelDir();
  const entries = await readdir(RUNAI_MODEL_DIR, { withFileTypes: true });
  return entries
    .filter((entry) => entry.isFile() && entry.name.toLowerCase().endsWith(".gguf"))
    .map((entry) => join(RUNAI_MODEL_DIR, entry.name))
    .sort();
}
