import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi, beforeEach } from 'vitest';
import { Settings } from './Settings';
import { useLocalBackend } from './useLocalBackend';
import { request } from '../services/backend';

vi.mock('../services/backend', () => ({ request: vi.fn() }));
function Harness() {
  return <Settings backend={useLocalBackend()} />;
}
const api = vi.mocked(request);
beforeEach(() => {
  api.mockReset();
  api.mockImplementation(async (path, method, value) => {
    if (path === '/health')
      return { backend: 'ready', ollama: 'ready', version: 'test', message: 'Local' };
    if (path === '/hardware')
      return {
        cpu: 'Ryzen',
        ram_total_gib: 16,
        ram_available_gib: 8,
        disk_free_gib: 100,
        gpus: [],
        recommendation: 'Teste',
      };
    if (path === '/settings') return method === 'PUT' ? value : { model: null, num_ctx: 4096 };
    if (path === '/models')
      return { installed: [{ name: 'qwen3:8b', size: 5200000000 }], loaded: [] };
    if (path === '/probe')
      return {
        answer: 'conexão local funcionando',
        model: 'qwen3:8b',
        tokens_per_second: 30,
        total_seconds: 2,
        loaded: [],
      };
    throw new Error('unexpected route');
  });
});
describe('Conexão local', () => {
  it('salva o modelo antes do teste e apresenta a medição retornada', async () => {
    const user = userEvent.setup();
    render(<Harness />);
    const model = screen.getByRole('combobox', { name: 'Modelo de conversa' });
    await waitFor(() => expect(model).toBeEnabled());
    await user.selectOptions(model, 'qwen3:8b');
    expect(screen.getByRole('button', { name: 'Testar inferência local' })).toBeDisabled();
    await user.click(screen.getByRole('button', { name: 'Salvar configuração' }));
    await waitFor(() =>
      expect(screen.getByRole('button', { name: 'Testar inferência local' })).toBeEnabled(),
    );
    expect(api).toHaveBeenCalledWith('/settings', 'PUT', {
      model: 'qwen3:8b',
      num_ctx: 4096,
      max_output: 8192,
    });
    await user.click(screen.getByRole('button', { name: 'Testar inferência local' }));
    expect(await screen.findByText('conexão local funcionando')).toBeVisible();
    expect(screen.getByText(/30 tokens\/s/)).toBeVisible();
  });
  it('mostra erro de conexão e mantém o teste indisponível', async () => {
    api.mockRejectedValue(new Error('Backend indisponível'));
    render(<Harness />);
    expect(await screen.findByRole('alert')).toHaveTextContent('Backend indisponível');
    expect(screen.getByRole('button', { name: 'Testar inferência local' })).toBeDisabled();
    expect(screen.getByRole('button', { name: 'Atualizar diagnóstico' })).toBeEnabled();
  });
});
