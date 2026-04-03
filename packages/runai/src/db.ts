import { existsSync } from "node:fs";
import { mkdir } from "node:fs/promises";
import { dirname } from "node:path";
import { Database } from "bun:sqlite";
import { RUNAI_DB_PATH } from "./config";

export interface InstalledModelRecord {
  id: string;
  name: string;
  path: string;
  sourceUrl: string | null;
  sourceRepo: string | null;
  sourceFile: string | null;
  installedAt: string;
}

async function openDb(): Promise<Database> {
  await mkdir(dirname(RUNAI_DB_PATH), { recursive: true });
  const db = new Database(RUNAI_DB_PATH);
  db.exec(`
    CREATE TABLE IF NOT EXISTS installed_models (
      id TEXT PRIMARY KEY,
      name TEXT NOT NULL,
      path TEXT NOT NULL UNIQUE,
      source_url TEXT,
      source_repo TEXT,
      source_file TEXT,
      installed_at TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_installed_models_installed_at
      ON installed_models(installed_at DESC);
  `);
  return db;
}

export async function upsertInstalledModel(input: {
  id: string;
  name: string;
  path: string;
  sourceUrl?: string | null;
  sourceRepo?: string | null;
  sourceFile?: string | null;
}): Promise<void> {
  const db = await openDb();
  try {
    db.query(`
      INSERT INTO installed_models (
        id, name, path, source_url, source_repo, source_file, installed_at
      ) VALUES (?, ?, ?, ?, ?, ?, ?)
      ON CONFLICT(id) DO UPDATE SET
        name = excluded.name,
        path = excluded.path,
        source_url = excluded.source_url,
        source_repo = excluded.source_repo,
        source_file = excluded.source_file,
        installed_at = excluded.installed_at
    `).run(
      input.id,
      input.name,
      input.path,
      input.sourceUrl ?? null,
      input.sourceRepo ?? null,
      input.sourceFile ?? null,
      new Date().toISOString(),
    );
  } finally {
    db.close();
  }
}

export async function removeInstalledModelByPath(path: string): Promise<void> {
  const db = await openDb();
  try {
    db.query("DELETE FROM installed_models WHERE path = ?").run(path);
  } finally {
    db.close();
  }
}

export async function removeInstalledModelById(id: string): Promise<void> {
  const db = await openDb();
  try {
    db.query("DELETE FROM installed_models WHERE id = ?").run(id);
  } finally {
    db.close();
  }
}

export async function listInstalledModels(): Promise<InstalledModelRecord[]> {
  const db = await openDb();
  try {
    const rows = db.query(`
      SELECT id, name, path, source_url, source_repo, source_file, installed_at
      FROM installed_models
      ORDER BY installed_at DESC
    `).all() as Array<{
      id: string;
      name: string;
      path: string;
      source_url: string | null;
      source_repo: string | null;
      source_file: string | null;
      installed_at: string;
    }>;
    return rows.map((row) => ({
      id: row.id,
      name: row.name,
      path: row.path,
      sourceUrl: row.source_url,
      sourceRepo: row.source_repo,
      sourceFile: row.source_file,
      installedAt: row.installed_at,
    }));
  } finally {
    db.close();
  }
}

export async function getInstalledModelById(id: string): Promise<InstalledModelRecord | null> {
  const db = await openDb();
  try {
    const row = db.query(`
      SELECT id, name, path, source_url, source_repo, source_file, installed_at
      FROM installed_models
      WHERE id = ?
      LIMIT 1
    `).get(id) as {
      id: string;
      name: string;
      path: string;
      source_url: string | null;
      source_repo: string | null;
      source_file: string | null;
      installed_at: string;
    } | null;
    if (!row) return null;
    return {
      id: row.id,
      name: row.name,
      path: row.path,
      sourceUrl: row.source_url,
      sourceRepo: row.source_repo,
      sourceFile: row.source_file,
      installedAt: row.installed_at,
    };
  } finally {
    db.close();
  }
}

export function isModelFilePresent(path: string): boolean {
  return existsSync(path);
}
