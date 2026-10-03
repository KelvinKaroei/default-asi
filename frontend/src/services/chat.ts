import { localFetch } from './backend';
import type { Mode, Source } from '../types';

export type ChatEvent =
  | { type: 'start'; model: string; omitted_messages: number; sources?: Source[] }
  | { type: 'delta'; content: string }
  | { type: 'done'; reason: string; tokens_per_second: number | null }
  | { type: 'error'; message: string };

export async function consumeStream(response: Response, receive: (event: ChatEvent) => void) {
  if (!response.ok) {
    const data = await response.json();
    throw new Error(
      typeof data.detail === 'string'
        ? data.detail
        : 'Mensagem inválida ou grande demais. Divida em partes menores.',
    );
  }
  if (!response.body) throw new Error('Resposta sem conteúdo de streaming.');
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';
  let finished = false;
  function processLine(line: string) {
    if (!line.trim()) return;
    const event = JSON.parse(line) as ChatEvent;
    if (!['start', 'delta', 'done', 'error'].includes(event.type))
      throw new Error('Evento inválido do backend.');
    if (event.type === 'error') throw new Error(event.message);
    if (event.type === 'delta' && typeof event.content !== 'string')
      throw new Error('Fragmento inválido.');
    receive(event);
    if (event.type === 'done') finished = true;
  }
  try {
    while (!finished) {
      const { value, done } = await reader.read();
      buffer += decoder.decode(value, { stream: !done });
      if (buffer.length > 262144) throw new Error('Evento grande demais.');
      let newline: number;
      while ((newline = buffer.indexOf('\n')) !== -1) {
        const line = buffer.slice(0, newline);
        buffer = buffer.slice(newline + 1);
        processLine(line);
        if (finished) break;
      }
      if (done) {
        if (!finished && buffer.trim()) processLine(buffer);
        break;
      }
    }
    if (!finished) throw new Error('A conexão terminou antes da resposta completa.');
  } finally {
    await reader.cancel().catch(() => undefined);
    reader.releaseLock();
  }
}

export async function streamChat(
  mode: Mode,
  messages: { role: 'user' | 'assistant'; content: string }[],
  signal: AbortSignal,
  receive: (event: ChatEvent) => void,
  useMaterials = false,
  continuation = false,
) {
  const timeout = AbortSignal.timeout(910000);
  const response = await localFetch(
    '/chat',
    'POST',
    { mode, messages, use_materials: useMaterials, continue_response: continuation },
    AbortSignal.any([signal, timeout]),
  );
  await consumeStream(response, receive);
}
