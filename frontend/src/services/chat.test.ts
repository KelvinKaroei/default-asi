import { describe, expect, it } from 'vitest';
import { consumeStream, type ChatEvent } from './chat';

function response(text: string, byteByByte = false) {
  const bytes = new TextEncoder().encode(text);
  return new Response(
    new ReadableStream({
      start(controller) {
        if (byteByByte) for (const byte of bytes) controller.enqueue(new Uint8Array([byte]));
        else controller.enqueue(bytes);
        controller.close();
      },
    }),
  );
}
describe('Leitura do streaming', () => {
  it('recompõe UTF-8 e JSON fragmentados e aceita a última linha sem quebra', async () => {
    const events: ChatEvent[] = [];
    await consumeStream(
      response(
        '{"type":"delta","content":"ação 🛡️"}\n{"type":"done","reason":"stop","tokens_per_second":42}',
        true,
      ),
      (e) => events.push(e),
    );
    expect(events[0]).toEqual({ type: 'delta', content: 'ação 🛡️' });
    expect(events.at(-1)?.type).toBe('done');
  });
  it('mantém os fragmentos entregues quando a conexão termina sem done', async () => {
    const events: ChatEvent[] = [];
    await expect(
      consumeStream(response('{"type":"delta","content":"parcial"}\n'), (e) => events.push(e)),
    ).rejects.toThrow('antes da resposta completa');
    expect(events).toHaveLength(1);
  });
  it('propaga erro estruturado sem transformar falha em sucesso', async () => {
    await expect(
      consumeStream(response('{"type":"error","message":"Ollama indisponível"}\n'), () => {}),
    ).rejects.toThrow('Ollama indisponível');
  });
});
