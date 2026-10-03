import { act, renderHook, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { useChatSession } from './useChatSession';
import { streamChat } from '../../services/chat';
import type { ChatEvent } from '../../services/chat';

vi.mock('../../services/chat', () => ({ streamChat: vi.fn() }));
const api = vi.mocked(streamChat);
beforeEach(() => {
  api.mockReset();
});
describe('Sessão durante uma geração', () => {
  it('mantém o parcial na conversa original ao trocar, cancela e permite nova tentativa', async () => {
    let receive!: (event: ChatEvent) => void;
    api.mockImplementation((_mode, _messages, signal, callback) => {
      receive = callback;
      return new Promise((_resolve, reject) =>
        signal.addEventListener(
          'abort',
          () => reject(new DOMException('Cancelado', 'AbortError')),
          { once: true },
        ),
      );
    });
    const { result } = renderHook(useChatSession);
    const original = result.current.active.id;
    act(() => result.current.updateActive({ draft: 'Explique DNS' }));
    act(() => {
      result.current.send();
      result.current.send();
    });
    expect(api).toHaveBeenCalledTimes(1);
    act(() => receive({ type: 'delta', content: 'DNS traduz nomes.' }));
    act(() => result.current.newChat());
    expect(result.current.active.messages).toHaveLength(0);
    act(() => receive({ type: 'delta', content: ' Usa registros.' }));
    act(() => result.current.cancel());
    await waitFor(() => expect(result.current.generatingChatId).toBeNull());
    act(() => result.current.setActiveId(original));
    expect(result.current.active.messages.at(-1)?.content).toBe('DNS traduz nomes. Usa registros.');
    expect(result.current.active.messages.at(-1)?.status).toBe('cancelled');
    api.mockImplementation(async (_mode, messages, _signal, callback) => {
      expect(messages).toEqual([{ role: 'user', content: 'Explique DNS' }]);
      callback({ type: 'delta', content: 'Nova resposta' });
      callback({ type: 'done', reason: 'stop', tokens_per_second: 50 });
    });
    act(() => result.current.retry());
    await waitFor(() => expect(result.current.generatingChatId).toBeNull());
    expect(result.current.active.messages).toHaveLength(2);
    expect(result.current.active.messages.at(-1)?.status).toBe('complete');
  });
  it('preserva o texto parcial e mostra erro sem completar a resposta', async () => {
    api.mockImplementation(async (_mode, _messages, _signal, callback) => {
      callback({ type: 'delta', content: 'Texto parcial' });
      throw new Error('Servidor interrompido');
    });
    const { result } = renderHook(useChatSession);
    act(() => result.current.updateActive({ draft: 'TCP?' }));
    act(() => result.current.send());
    await waitFor(() => expect(result.current.generatingChatId).toBeNull());
    expect(result.current.active.messages.at(-1)).toMatchObject({
      content: 'Texto parcial',
      status: 'error',
      error: 'Servidor interrompido',
    });
  });
});

it('continua uma resposta longa preservando o parcial e o rascunho', async () => {
  api.mockImplementation(async (_mode, _messages, _signal, callback) => {
    callback({ type: 'delta', content: 'Parte longa '.repeat(2000) });
    callback({ type: 'done', reason: 'length', tokens_per_second: 40 });
  });
  const { result } = renderHook(useChatSession);
  act(() => result.current.updateActive({ draft: 'Explique redes' }));
  act(() => result.current.send());
  await waitFor(() => expect(result.current.generatingChatId).toBeNull());
  const partial = result.current.active.messages[1].content;
  act(() => result.current.updateActive({ draft: 'Pergunta para depois' }));
  api.mockImplementation(async (_mode, messages, _signal, callback, _materials, continuation) => {
    expect(continuation).toBe(true);
    expect(messages[1].content).toBe(partial);
    callback({ type: 'delta', content: 'Conclusão.' });
    callback({ type: 'done', reason: 'stop', tokens_per_second: 40 });
  });
  act(() => result.current.continueResponse());
  await waitFor(() => expect(result.current.generatingChatId).toBeNull());
  expect(result.current.active.messages).toHaveLength(4);
  expect(result.current.active.messages[1].content).toBe(partial);
  expect(result.current.active.draft).toBe('Pergunta para depois');
});
