import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, it, vi } from 'vitest';
import { Courses } from './Courses';
import { request } from '../services/backend';
vi.mock('@tauri-apps/api/core', () => ({ isTauri: () => true }));
vi.mock('../services/backend', () => ({ request: vi.fn() }));
it('separa leitura de quiz e encaminha aprofundamento sem enviar automaticamente', async () => {
  const course = {
    title: 'Redes',
    status: 'Autoral',
    modules: [
      {
        id: 'm',
        title: 'Módulo',
        lessons: [
          {
            id: 'ip',
            title: 'Endereços',
            body: 'Uma interface tem endereço.',
            quiz: { question: 'Qual opção?', choices: ['A', 'B'] },
            progress: { complete: false, attempts: 0, passed: false },
          },
        ],
      },
    ],
  };
  vi.mocked(request)
    .mockResolvedValueOnce(course)
    .mockResolvedValueOnce({ correct: false, explanation: 'Revise o endereço.' })
    .mockResolvedValueOnce(course);
  const study = vi.fn();
  render(<Courses onStudy={study} />);
  const user = userEvent.setup();
  await screen.findByText('Qual opção?');
  await user.click(screen.getByLabelText('A'));
  await user.click(screen.getByRole('button', { name: 'Conferir resposta' }));
  expect(await screen.findByText(/Vamos revisar/)).toHaveTextContent('Revise o endereço.');
  expect(screen.getByText('0/1 leituras concluídas · 0/1 quizzes aprovados')).toBeVisible();
  await user.click(screen.getByRole('button', { name: 'Aprofundar com o tutor' }));
  expect(study).toHaveBeenCalledWith(expect.stringContaining('Endereços'));
});
