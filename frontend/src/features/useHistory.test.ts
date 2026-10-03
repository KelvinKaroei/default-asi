import { act, renderHook, waitFor } from '@testing-library/react';
import { useState } from 'react';
import { beforeEach, expect, it, vi } from 'vitest';
import { useHistory } from './useHistory';
import { request } from '../services/backend';
import type { Chat } from '../types';
vi.mock('@tauri-apps/api/core', () => ({ isTauri: () => true }));
vi.mock('../services/backend', () => ({ request: vi.fn() }));
const api = vi.mocked(request);
const chat: Chat = {
  id: 'saved',
  title: 'Linux',
  category: 'Linux',
  mode: 'QUIZ',
  draft: 'rascunho',
  messages: [],
};
function useHarness() {
  const [chats, setChats] = useState<Chat[]>([{ ...chat, id: 'temporary' }]);
  return { chats, setChats, ...useHistory(chats, setChats) };
}
beforeEach(() => {
  api.mockReset();
});

it('carrega antes de gravar e recupera categoria, modo e rascunho', async () => {
  api.mockResolvedValue({ revision: 3, chats: [chat] });
  const { result } = renderHook(useHarness);
  expect(result.current.ready).toBe(false);
  await waitFor(() => expect(result.current.ready).toBe(true));
  expect(result.current.chats).toEqual([chat]);
  expect(api).toHaveBeenCalledTimes(1);
  expect(result.current.storageStatus).toContain('salvo');
});

it('reenvia a mesma mutação após resposta perdida, depois salva alterações mais recentes', async () => {
  api.mockResolvedValueOnce({ revision: 3, chats: [chat] });
  const { result } = renderHook(useHarness);
  await waitFor(() => expect(result.current.ready).toBe(true));
  act(() => result.current.setChats([{ ...chat, draft: 'primeiro' }]));
  api.mockRejectedValueOnce(new Error('Resposta perdida'));
  await act(() => result.current.retrySave());
  expect(result.current.error).toBe('Resposta perdida');
  const failedBody = api.mock.calls[1][2];
  act(() => result.current.setChats([{ ...chat, draft: 'segundo' }]));
  api.mockResolvedValueOnce({ revision: 4 }).mockResolvedValueOnce({ revision: 5 });
  await act(() => result.current.retrySave());
  expect(api.mock.calls[2][2]).toEqual(failedBody);
  expect(api.mock.calls[3][2]).toMatchObject({ revision: 4, chats: [{ draft: 'segundo' }] });
  expect(result.current.error).toBe('');
  expect(result.current.storageStatus).toContain('salvo');
});

it('não grava histórico vazio quando a leitura falha', async () => {
  api.mockRejectedValue(new Error('Banco indisponível'));
  const { result } = renderHook(useHarness);
  await waitFor(() => expect(result.current.error).toBe('Banco indisponível'));
  expect(result.current.ready).toBe(false);
  expect(api.mock.calls.every((call) => call[1] === undefined)).toBe(true);
});
