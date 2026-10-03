import { useCallback, useEffect, useState } from 'react';
import {
  request,
  type Health,
  type Models,
  type Hardware,
  type Preferences,
  type Probe,
} from '../services/backend';

export function useLocalBackend() {
  const [health, setHealth] = useState<Health | null>(null);
  const [hardware, setHardware] = useState<Hardware | null>(null);
  const [models, setModels] = useState<Models>({ installed: [], loaded: [] });
  const [settings, setSettings] = useState<Preferences>({ model: null, num_ctx: 32768 });
  const [probe, setProbe] = useState<Probe | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState('');
  const refresh = useCallback(async () => {
    setBusy('Atualizando');
    setError('');
    try {
      const [status, machine, preferences] = await Promise.all([
        request<Health>('/health'),
        request<Hardware>('/hardware'),
        request<Preferences>('/settings'),
      ]);
      setHealth(status);
      setHardware(machine);
      setSettings(preferences);
      setModels(
        status.ollama === 'ready'
          ? await request<Models>('/models')
          : { installed: [], loaded: [] },
      );
    } catch (e) {
      setError(String(e instanceof Error ? e.message : e));
      setHealth(null);
      setModels({ installed: [], loaded: [] });
    } finally {
      setBusy('');
    }
  }, []);
  useEffect(() => {
    void refresh();
  }, [refresh]);
  async function save(value: Preferences) {
    setBusy('Salvando');
    setError('');
    setProbe(null);
    try {
      setSettings(await request<Preferences>('/settings', 'PUT', value));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy('');
    }
  }
  async function test() {
    setBusy('Testando inferência');
    setError('');
    setProbe(null);
    try {
      const result = await request<Probe>('/probe', 'POST');
      setProbe(result);
      setModels((old) => ({ ...old, loaded: result.loaded }));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy('');
    }
  }
  async function start() {
    setBusy('Iniciando Ollama');
    setError('');
    try {
      await request('/ollama/start', 'POST');
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy('');
    }
  }
  return { health, hardware, models, settings, probe, error, busy, refresh, save, test, start };
}
export type LocalBackend = ReturnType<typeof useLocalBackend>;
