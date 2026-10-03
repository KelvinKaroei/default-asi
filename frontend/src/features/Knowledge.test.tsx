import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, expect, it, vi } from 'vitest';
import { Knowledge } from './Knowledge';
import { request } from '../services/backend';
vi.mock('@tauri-apps/api/core', () => ({ isTauri: () => true }));
vi.mock('../services/backend', () => ({ request: vi.fn() }));
vi.mock('./RetrievalPanel', () => ({ RetrievalPanel: () => null }));
const api = vi.mocked(request);
const material = {
  id: 'one',
  name: 'nota.md',
  extension: '.md',
  size: 10,
  created: '2026-09-30T10:00:00Z',
  encoding: 'utf-8',
  warning: '',
  pages: [{ page: 1, text: '<script>texto literal</script>' }],
};
beforeEach(() => {
  api.mockReset();
});

it('importa arquivo, mostra duplicado e visualiza texto sem interpretar HTML', async () => {
  api
    .mockResolvedValueOnce([])
    .mockResolvedValueOnce({ material, duplicate: true })
    .mockResolvedValueOnce([material]);
  const { container } = render(<Knowledge />);
  await screen.findByText(/Seu acervo está vazio/);
  const file = new File(['ação'], 'nota.md', { type: 'text/markdown' });
  fireEvent.change(container.querySelector('input[type=file]')!, { target: { files: [file] } });
  expect(await screen.findByText(/Nenhuma cópia foi criada/)).toBeVisible();
  expect(api.mock.calls[1][2]).toMatchObject({
    name: 'nota.md',
    encoding: 'utf-8',
    content: 'YcOnw6Nv',
  });
  expect(screen.getByText('<script>texto literal</script>')).toBeVisible();
  expect(container.querySelector('script')).toBeNull();
});

it('exige confirmação antes de remover e mantém material se a remoção falha', async () => {
  api.mockResolvedValueOnce([material]).mockRejectedValueOnce(new Error('Banco indisponível'));
  const user = userEvent.setup();
  render(<Knowledge />);
  await user.click(await screen.findByRole('button', { name: 'Remover nota.md' }));
  expect(api).toHaveBeenCalledTimes(1);
  await user.click(screen.getByRole('button', { name: 'Confirmar remoção' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Banco indisponível');
  expect(screen.getByRole('button', { name: 'Remover nota.md' })).toBeVisible();
});

it('notas sempre usam UTF-8 mesmo com Windows-1252 selecionado', async () => {
  api
    .mockResolvedValueOnce([])
    .mockResolvedValueOnce({ material, duplicate: false })
    .mockResolvedValueOnce([material]);
  const user = userEvent.setup();
  render(<Knowledge />);
  await screen.findByText(/Seu acervo está vazio/);
  await user.selectOptions(screen.getByLabelText('Codificação de texto'), 'cp1252');
  await user.click(screen.getByText('Criar anotação'));
  await user.type(screen.getByLabelText('Título da anotação'), 'Estudo');
  await user.type(screen.getByLabelText('Texto da anotação'), 'ação');
  await user.click(screen.getByRole('button', { name: 'Salvar anotação' }));
  await waitFor(() =>
    expect(api.mock.calls[1][2]).toMatchObject({ encoding: 'utf-8', name: 'Estudo.md' }),
  );
  expect(await screen.findByText(/Material importado e salvo/)).toBeVisible();
});

it('informa PDF sem texto sem exibir sucesso', async () => {
  api.mockResolvedValueOnce([]).mockRejectedValueOnce(new Error('PDF sem texto extraível.'));
  const { container } = render(<Knowledge />);
  await screen.findByText(/Seu acervo está vazio/);
  fireEvent.change(container.querySelector('input[type=file]')!, {
    target: { files: [new File(['pdf'], 'scan.pdf')] },
  });
  expect(await screen.findByRole('alert')).toHaveTextContent('PDF sem texto');
  expect(screen.queryByText(/Material importado e salvo/)).toBeNull();
});
