import { invoke, isTauri } from '@tauri-apps/api/core';
type Connection = { url: string; token: string };
let connection: Promise<Connection> | undefined;
export async function localFetch(
  path: string,
  method = 'GET',
  body?: unknown,
  signal?: AbortSignal,
): Promise<Response> {
  if (!isTauri()) throw new Error('Abra o aplicativo desktop para conectar o backend local.');
  connection ??= invoke<Connection>('backend_connection').catch((error) => {
    connection = undefined;
    throw error;
  });
  const session = await connection;
  let response: Response;
  try {
    response = await fetch(`${session.url}${path}`, {
      method,
      headers: { Authorization: `Bearer ${session.token}`, 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: signal ?? AbortSignal.timeout(path === '/probe' ? 190000 : 20000),
    });
  } catch (error) {
    if (signal?.aborted) throw error;
    connection = undefined;
    throw new Error('O backend não respondeu. Tente atualizar a conexão.');
  }
  return response;
}
export async function request<T>(path: string, method = 'GET', body?: unknown): Promise<T> {
  const response = await localFetch(path, method, body);
  const result = await response.json();
  if (!response.ok)
    throw new Error(
      typeof result.detail === 'string' ? result.detail : 'Requisição local inválida.',
    );
  return result as T;
}
export type Health = { backend: string; ollama: string; version: string | null; message: string };
export type Model = {
  name: string;
  size: number;
  size_vram?: number;
  details?: { quantization_level?: string };
};
export type Models = { installed: Model[]; loaded: Model[] };
export type Preferences = { model: string | null; num_ctx: number; max_output?: number };
export type Hardware = {
  cpu: string;
  os: string;
  ram_total_gib: number;
  ram_available_gib: number;
  disk_free_gib: number;
  gpus: { name: string; total_mib: number; free_mib: number }[];
  recommendation: string;
};
export type Probe = {
  answer: string;
  model: string;
  tokens_per_second: number | null;
  total_seconds: number;
  loaded: Model[];
};
