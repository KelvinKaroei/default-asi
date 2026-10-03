import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, it, vi } from 'vitest';
import { MemoryPanel } from './MemoryPanel';
import { request } from '../services/backend';
vi.mock('@tauri-apps/api/core', () => ({ isTauri: () => true }));
vi.mock('../services/backend', () => ({ request: vi.fn() }));
it('exige opt-in e preserva texto se salvar falha', async () => {
  const api = vi.mocked(request);
  api
    .mockResolvedValueOnce({ enabled: false, items: [] })
    .mockResolvedValueOnce({ enabled: true, items: [] })
    .mockRejectedValueOnce(new Error('Falha de disco'));
  render(<MemoryPanel />);
  const user = userEvent.setup();
  await screen.findByText(/Desativada: o tutor/);
  expect(screen.getByRole('button', { name: 'Confirmar e salvar memória' })).toBeDisabled();
  await user.click(screen.getByLabelText('Usar memórias nas próximas respostas'));
  const input = screen.getByLabelText('Nova preferência confirmada');
  await user.type(input, 'Estudo DNS');
  await user.click(screen.getByRole('button', { name: 'Confirmar e salvar memória' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Falha de disco');
  expect(input).toHaveValue('Estudo DNS');
});
