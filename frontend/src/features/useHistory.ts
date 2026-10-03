import { isTauri } from '@tauri-apps/api/core';
import { useCallback, useEffect, useRef, useState } from 'react';
import type { Dispatch, SetStateAction } from 'react';
import type { Chat } from '../types';
import { request } from '../services/backend';

type Snapshot = { revision: number; chats: Chat[] };

export function useHistory(chats: Chat[], setChats: Dispatch<SetStateAction<Chat[]>>) {
  const desktop = isTauri();
  const [ready, setReady] = useState(!desktop);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [saved, setSaved] = useState<Chat[] | null>(null);
  const [busy, setBusy] = useState(false);
  const latest = useRef(chats);
  latest.current = chats;
  const revision = useRef(0);
  const acknowledged = useRef<Chat[] | null>(null);
  const pending = useRef<{ revision: number; mutation: string; chats: Chat[] } | null>(null);
  const saving = useRef<Promise<void> | null>(null);
  const paused = useRef(false);
  const failed = useRef(false);

  const load = useCallback(async () => {
    try {
      const result = await request<Snapshot>('/history');
      revision.current = result.revision;
      if (result.chats.length) {
        latest.current = result.chats;
        setChats(result.chats);
        acknowledged.current = result.chats;
        setSaved(result.chats);
      }
      failed.current = false;
      setError('');
      setReady(true);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Não foi possível carregar o histórico.');
    }
  }, [setChats]);

  useEffect(() => {
    if (desktop) void load();
  }, [desktop, load]);

  const flush = useCallback(async () => {
    if (saving.current) return saving.current;
    const work = async () => {
      while (pending.current || acknowledged.current !== latest.current) {
        pending.current ??= {
          revision: revision.current,
          mutation: crypto.randomUUID(),
          chats: latest.current,
        };
        const sent = pending.current;
        const result = await request<{ revision: number }>('/history', 'PUT', sent);
        revision.current = result.revision;
        acknowledged.current = sent.chats;
        setSaved(sent.chats);
        pending.current = null;
      }
      failed.current = false;
      setError('');
    };
    saving.current = work()
      .catch((cause) => {
        failed.current = true;
        setError(cause instanceof Error ? cause.message : 'Falha ao salvar histórico.');
        throw cause;
      })
      .finally(() => {
        saving.current = null;
      });
    return saving.current;
  }, []);

  useEffect(() => {
    if (!desktop || !ready) return;
    const timer = window.setInterval(() => {
      if (!paused.current && !failed.current) void flush().catch(() => {});
    }, 750);
    return () => window.clearInterval(timer);
  }, [desktop, ready, flush]);

  async function retrySave() {
    if (!ready) return load();
    await flush().catch(() => {});
  }

  async function maintenance(restore: boolean) {
    if (!desktop || !ready || paused.current) return;
    paused.current = true;
    setBusy(true);
    setNotice('');
    try {
      await flush();
      if (restore) {
        const result = await request<Snapshot>('/history/restore', 'POST', {
          revision: revision.current,
        });
        revision.current = result.revision;
        const restored = result.chats.length
          ? result.chats
          : [
              {
                ...latest.current[0],
                id: crypto.randomUUID(),
                title: 'Nova conversa',
                draft: '',
                messages: [],
              },
            ];
        latest.current = restored;
        acknowledged.current = result.chats.length ? restored : null;
        setChats(restored);
        setSaved(acknowledged.current);
        setNotice(
          'Backup restaurado. O estado anterior foi preservado em history.before-restore.sqlite3.',
        );
      } else {
        const result = await request<{ path: string }>('/history/backup', 'POST');
        setNotice(`Backup criado em ${result.path}`);
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Falha na operação de backup.');
    } finally {
      paused.current = false;
      setBusy(false);
    }
  }

  return {
    desktop,
    ready,
    error,
    busy,
    notice,
    retrySave,
    maintenance,
    storageStatus: !desktop
      ? 'Prévia · histórico temporário'
      : saved === chats
        ? 'Histórico salvo neste computador'
        : 'Salvando histórico…',
  };
}
