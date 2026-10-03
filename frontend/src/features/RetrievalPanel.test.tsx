import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, it, vi } from 'vitest';
import { RetrievalPanel } from './RetrievalPanel';
import { request } from '../services/backend';
vi.mock('../services/backend', () => ({ request: vi.fn() }));
it('mostra estado do índice e preserva erro da preparação', async () => {
  vi.mocked(request)
    .mockResolvedValueOnce({ ready: true, running: false, chunks: 4, error: '' })
    .mockRejectedValueOnce(new Error('Aguarde a operação atual'));
  render(<RetrievalPanel desktop revision={1} />);
  expect(await screen.findByText('Índice pronto · 4 trechos')).toBeVisible();
  await userEvent.click(screen.getByRole('button', { name: 'Preparar índice local' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Aguarde a operação atual');
});
