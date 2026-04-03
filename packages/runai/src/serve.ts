import { basename } from "node:path";
import { RUNAI_DEFAULT_MODEL, RUNAI_DEFAULT_PORT } from "./config";
import { modelPathFromId } from "./model-store";
import { isModelFilePresent, listInstalledModels } from "./db";
import { runLlamaOnce, runLlamaStream } from "./llamacpp";
import {
  buildPrompt,
  createChatResponse,
  createCompletionResponse,
  createCompletionSSEChunk,
  createSSEChunk,
  normalizeCompletionPrompt,
  type ChatCompletionRequest,
  type CompletionRequest,
} from "./openai";
import { sendInferenceTelemetry } from "./telemetry";

interface ServeOptions {
  model?: string;
  port?: number;
}

function resolveModelPath(input?: string): string {
  const model = input || RUNAI_DEFAULT_MODEL;
  if (!model) throw new Error("Model is required. Use --model <path|id> or RUNAI_MODEL.");
  if (model.includes("/") || model.endsWith(".gguf")) return model;
  return modelPathFromId(model);
}

interface ResolvedApiModel {
  id: string;
  path: string;
}

function stripGguf(value: string): string {
  return value.replace(/\.gguf$/i, "");
}

async function resolveApiModel(requestedModel: string | undefined, fallbackPath: string): Promise<ResolvedApiModel> {
  if (!requestedModel) {
    return {
      id: stripGguf(basename(fallbackPath)),
      path: fallbackPath,
    };
  }

  const token = requestedModel.trim();
  if (!token) {
    return {
      id: stripGguf(basename(fallbackPath)),
      path: fallbackPath,
    };
  }

  if (token.includes("/") || token.endsWith(".gguf")) {
    if (!isModelFilePresent(token)) {
      throw new Error(`Model file not found: ${token}`);
    }
    return {
      id: stripGguf(basename(token)),
      path: token,
    };
  }

  const normalized = token.toLowerCase();
  const installed = await listInstalledModels();
  const availableInstalled = installed.filter((item) => isModelFilePresent(item.path));
  if (normalized === "auto") {
    const first = availableInstalled[0];
    if (first) {
      return { id: first.id, path: first.path };
    }
    if (isModelFilePresent(fallbackPath)) {
      return {
        id: stripGguf(basename(fallbackPath)),
        path: fallbackPath,
      };
    }
    throw new Error("No installed models found for \"auto\". Use /v1/models to inspect available models.");
  }

  const match = installed.find((item) => {
    const idMatch = item.id.toLowerCase() === normalized;
    const nameMatch = item.name.toLowerCase() === normalized;
    const fileName = basename(item.path).toLowerCase();
    const fileNameNoExt = stripGguf(fileName);
    return idMatch || nameMatch || fileName === normalized || fileNameNoExt === normalized;
  });
  if (match && isModelFilePresent(match.path)) {
    return { id: match.id, path: match.path };
  }

  const derivedPath = modelPathFromId(token);
  if (isModelFilePresent(derivedPath)) {
    return {
      id: stripGguf(basename(derivedPath)),
      path: derivedPath,
    };
  }

  throw new Error(`Unknown model "${token}". Use /v1/models to list installed models.`);
}

function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "content-type": "application/json; charset=utf-8",
      ...CORS_HEADERS,
    },
  });
}

const CORS_HEADERS = {
  "access-control-allow-origin": "*",
  "access-control-allow-headers": "authorization,content-type",
  "access-control-allow-methods": "GET,POST,OPTIONS",
};

function sse(stream: ReadableStream<Uint8Array>): Response {
  return new Response(stream, {
    headers: {
      "content-type": "text/event-stream",
      "cache-control": "no-cache",
      connection: "keep-alive",
      ...CORS_HEADERS,
    },
  });
}

function optionsResponse(): Response {
  return new Response(null, { status: 204, headers: CORS_HEADERS });
}

export function startServer(options: ServeOptions): void {
  const modelPath = resolveModelPath(options.model);
  const modelLabel = stripGguf(basename(modelPath));
  const port = options.port || RUNAI_DEFAULT_PORT;

  Bun.serve({
    port,
    routes: {
      "/v1/chat/completions": {
        POST: async (req) => {
          let body: ChatCompletionRequest;
          try {
            body = await req.json() as ChatCompletionRequest;
          } catch {
            return json({ error: { message: "Invalid JSON body", type: "invalid_request_error" } }, 400);
          }

          if (!body.messages?.length) {
            return json({ error: { message: "messages is required", type: "invalid_request_error" } }, 400);
          }
          const prompt = buildPrompt(body.messages);
          const temperature = typeof body.temperature === "number" ? body.temperature : 0.7;
          const maxTokens = typeof body.max_tokens === "number" ? body.max_tokens : 512;
          let activeModel: ResolvedApiModel;
          try {
            activeModel = await resolveApiModel(body.model, modelPath);
          } catch (error) {
            return json(
              { error: { message: error instanceof Error ? error.message : "Invalid model", type: "invalid_request_error" } },
              400,
            );
          }

          if (!body.stream) {
            const startedAt = performance.now();
            try {
              const output = await runLlamaOnce({
                modelPath: activeModel.path,
                prompt,
                temperature,
                maxTokens,
              });
              sendInferenceTelemetry({
                model: activeModel.id,
                stream: false,
                success: true,
                latencyMs: performance.now() - startedAt,
                outputText: output,
                temperature,
                maxTokens,
              });
              return json(createChatResponse(activeModel.id, output));
            } catch (error) {
              sendInferenceTelemetry({
                model: activeModel.id,
                stream: false,
                success: false,
                latencyMs: performance.now() - startedAt,
                outputText: "",
                temperature,
                maxTokens,
              });
              return json(
                { error: { message: error instanceof Error ? error.message : "Inference failed", type: "server_error" } },
                500,
              );
            }
          }

          const stream = new ReadableStream({
            start: async (controller) => {
              const startedAt = performance.now();
              let aggregated = "";
              const encoder = new TextEncoder();
              try {
                await runLlamaStream(
                  { modelPath: activeModel.path, prompt, temperature, maxTokens },
                  (chunk) => {
                    aggregated += chunk;
                    const payload = createSSEChunk(activeModel.id, chunk);
                    controller.enqueue(encoder.encode(`data: ${JSON.stringify(payload)}\n\n`));
                  },
                );
                sendInferenceTelemetry({
                  model: activeModel.id,
                  stream: true,
                  success: true,
                  latencyMs: performance.now() - startedAt,
                  outputText: aggregated,
                  temperature,
                  maxTokens,
                });
                controller.enqueue(encoder.encode(`data: ${JSON.stringify(createSSEChunk(activeModel.id, "", true))}\n\n`));
                controller.enqueue(encoder.encode("data: [DONE]\n\n"));
                controller.close();
              } catch (error) {
                sendInferenceTelemetry({
                  model: activeModel.id,
                  stream: true,
                  success: false,
                  latencyMs: performance.now() - startedAt,
                  outputText: aggregated,
                  temperature,
                  maxTokens,
                });
                const payload = {
                  error: {
                    message: error instanceof Error ? error.message : "stream failed",
                    type: "server_error",
                  },
                };
                controller.enqueue(encoder.encode(`data: ${JSON.stringify(payload)}\n\n`));
                controller.close();
              }
            },
          });

          return sse(stream);
        },
        OPTIONS: optionsResponse,
      },
      "/v1/completions": {
        POST: async (req) => {
          let body: CompletionRequest;
          try {
            body = await req.json() as CompletionRequest;
          } catch {
            return json({ error: { message: "Invalid JSON body", type: "invalid_request_error" } }, 400);
          }

          const prompt = normalizeCompletionPrompt(body.prompt);
          if (!prompt.trim()) {
            return json({ error: { message: "prompt is required", type: "invalid_request_error" } }, 400);
          }

          const temperature = typeof body.temperature === "number" ? body.temperature : 0.7;
          const maxTokens = typeof body.max_tokens === "number" ? body.max_tokens : 512;
          let activeModel: ResolvedApiModel;
          try {
            activeModel = await resolveApiModel(body.model, modelPath);
          } catch (error) {
            return json(
              { error: { message: error instanceof Error ? error.message : "Invalid model", type: "invalid_request_error" } },
              400,
            );
          }

          if (!body.stream) {
            const startedAt = performance.now();
            try {
              const output = await runLlamaOnce({
                modelPath: activeModel.path,
                prompt,
                temperature,
                maxTokens,
              });
              sendInferenceTelemetry({
                model: activeModel.id,
                stream: false,
                success: true,
                latencyMs: performance.now() - startedAt,
                outputText: output,
                temperature,
                maxTokens,
              });
              return json(createCompletionResponse(activeModel.id, output));
            } catch (error) {
              sendInferenceTelemetry({
                model: activeModel.id,
                stream: false,
                success: false,
                latencyMs: performance.now() - startedAt,
                outputText: "",
                temperature,
                maxTokens,
              });
              return json(
                { error: { message: error instanceof Error ? error.message : "Inference failed", type: "server_error" } },
                500,
              );
            }
          }

          const stream = new ReadableStream({
            start: async (controller) => {
              const startedAt = performance.now();
              let aggregated = "";
              const encoder = new TextEncoder();
              try {
                await runLlamaStream(
                  { modelPath: activeModel.path, prompt, temperature, maxTokens },
                  (chunk) => {
                    aggregated += chunk;
                    const payload = createCompletionSSEChunk(activeModel.id, chunk);
                    controller.enqueue(encoder.encode(`data: ${JSON.stringify(payload)}\n\n`));
                  },
                );
                sendInferenceTelemetry({
                  model: activeModel.id,
                  stream: true,
                  success: true,
                  latencyMs: performance.now() - startedAt,
                  outputText: aggregated,
                  temperature,
                  maxTokens,
                });
                controller.enqueue(
                  encoder.encode(`data: ${JSON.stringify(createCompletionSSEChunk(activeModel.id, "", true))}\n\n`),
                );
                controller.enqueue(encoder.encode("data: [DONE]\n\n"));
                controller.close();
              } catch (error) {
                sendInferenceTelemetry({
                  model: activeModel.id,
                  stream: true,
                  success: false,
                  latencyMs: performance.now() - startedAt,
                  outputText: aggregated,
                  temperature,
                  maxTokens,
                });
                const payload = {
                  error: {
                    message: error instanceof Error ? error.message : "stream failed",
                    type: "server_error",
                  },
                };
                controller.enqueue(encoder.encode(`data: ${JSON.stringify(payload)}\n\n`));
                controller.close();
              }
            },
          });

          return sse(stream);
        },
        OPTIONS: optionsResponse,
      },
      "/v1/models": {
        GET: async () => {
          const now = Math.floor(Date.now() / 1000);
          const installed = await listInstalledModels();
          const available = installed.filter((item) => isModelFilePresent(item.path));
          const data = available.map((item) => ({
            id: item.id,
            object: "model",
            created: now,
            owned_by: "runai",
          }));
          if (data.length === 0 && isModelFilePresent(modelPath)) {
            data.push({
              id: modelLabel,
              object: "model",
              created: now,
              owned_by: "runai",
            });
          }
          if (data.length > 0) {
            data.unshift({
              id: "auto",
              object: "model",
              created: now,
              owned_by: "runai",
            });
          }
          return json({
            object: "list",
            data,
          });
        },
        OPTIONS: optionsResponse,
      },
      "/health": {
        GET: () => json({ ok: true, model: modelLabel }),
        OPTIONS: optionsResponse,
      },
    },
    fetch() {
      return json({ error: { message: "Not found", type: "invalid_request_error" } }, 404);
    },
  });

  console.log(`runai API listening at http://localhost:${port}`);
  console.log(`OpenAI-compatible endpoint: http://localhost:${port}/v1/chat/completions`);
  console.log(`Model: ${modelPath}`);
}
