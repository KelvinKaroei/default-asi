import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, it, vi } from 'vitest';
import { Labs } from './Labs';
import { request } from '../services/backend';
vi.mock('@tauri-apps/api/core', () => ({ isTauri: () => true }));
vi.mock('../services/backend', () => ({ request: vi.fn() }));
it('salva somente checklist e preserva estado quando falha', async () => {
  vi.mocked(request)
    .mockResolvedValueOnce([
      {
        id: 'loopback',
        title: 'Local',
        level: 'Inicial',
        objective: 'Teste',
        requirements: ['Windows'],
        isolation: 'Loopback',
        steps: [
          {
            title: 'Observar',
            command: 'ping -n 4 127.0.0.1',
            explanation: 'ICMP',
            expected: 'Resposta local',
          },
        ],
        errors: [],
        defense: 'Confira',
        cleanup: 'Nada',
        reflection: 'Por quê?',
        completed: [],
      },
    ])
    .mockRejectedValueOnce(new Error('Disco indisponível'));
  render(<Labs onStudy={vi.fn()} />);
  const checkbox = await screen.findByLabelText('Concluí esta etapa');
  await userEvent.click(checkbox);
  expect(await screen.findByRole('alert')).toHaveTextContent('Disco indisponível');
  expect(checkbox).not.toBeChecked();
  expect(request).toHaveBeenLastCalledWith('/learning/labs/loopback/steps/0', 'PUT', {
    complete: true,
  });
});
