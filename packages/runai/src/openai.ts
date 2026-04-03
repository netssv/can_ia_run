export interface ChatMessage {
  role: "system" | "user" | "assistant";
  content: string;
}

export interface ChatCompletionRequest {
  model?: string;
  messages: ChatMessage[];
  stream?: boolean;
  temperature?: number;
  max_tokens?: number;
}

export interface CompletionRequest {
  model?: string;
  prompt: string | string[];
  stream?: boolean;
  temperature?: number;
  max_tokens?: number;
}

export function buildPrompt(messages: ChatMessage[]): string {
  return messages.map((m) => `${m.role.toUpperCase()}: ${m.content}`).join("\n") + "\nASSISTANT:";
}

export function createChatResponse(model: string, content: string) {
  const now = Math.floor(Date.now() / 1000);
  const words = content.trim() ? content.trim().split(/\s+/).length : 0;
  return {
    id: `chatcmpl_${crypto.randomUUID().replaceAll("-", "")}`,
    object: "chat.completion",
    created: now,
    model,
    choices: [
      {
        index: 0,
        message: { role: "assistant", content },
        finish_reason: "stop",
      },
    ],
    usage: {
      prompt_tokens: 0,
      completion_tokens: words,
      total_tokens: words,
    },
  };
}

export function createSSEChunk(model: string, delta: string, done = false) {
  const now = Math.floor(Date.now() / 1000);
  return {
    id: `chatcmpl_${crypto.randomUUID().replaceAll("-", "")}`,
    object: "chat.completion.chunk",
    created: now,
    model,
    choices: [
      {
        index: 0,
        delta: done ? {} : { content: delta },
        finish_reason: done ? "stop" : null,
      },
    ],
  };
}

export function normalizeCompletionPrompt(prompt: CompletionRequest["prompt"]): string {
  if (typeof prompt === "string") return prompt;
  if (Array.isArray(prompt)) return prompt.join("\n");
  return "";
}

export function createCompletionResponse(model: string, text: string) {
  const now = Math.floor(Date.now() / 1000);
  const words = text.trim() ? text.trim().split(/\s+/).length : 0;
  return {
    id: `cmpl_${crypto.randomUUID().replaceAll("-", "")}`,
    object: "text_completion",
    created: now,
    model,
    choices: [
      {
        text,
        index: 0,
        finish_reason: "stop",
      },
    ],
    usage: {
      prompt_tokens: 0,
      completion_tokens: words,
      total_tokens: words,
    },
  };
}

export function createCompletionSSEChunk(model: string, text: string, done = false) {
  const now = Math.floor(Date.now() / 1000);
  return {
    id: `cmpl_${crypto.randomUUID().replaceAll("-", "")}`,
    object: "text_completion",
    created: now,
    model,
    choices: [
      {
        text,
        index: 0,
        finish_reason: done ? "stop" : null,
      },
    ],
  };
}
