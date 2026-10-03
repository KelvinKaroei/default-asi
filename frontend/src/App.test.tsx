import { describe, expect, it, vi } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import App from './App';
vi.mock('./services/chat', () => ({
  streamChat: vi.fn(async (_mode, _messages, _signal, receive) => {
    receive({ type: 'start', model: 'qwen3:8b', omitted_messages: 0 });
    receive({ type: 'delta', content: 'Resposta local de teste.' });
    receive({ type: 'done', reason: 'stop', tokens_per_second: 50 });
  }),
}));

describe('Interface da sessão local', () => {
  it('distingue a prévia de uma IA conectada e rejeita envio vazio', () => {
    render(<App />);
    expect(screen.getByText(/confira comandos e respostas/)).toBeVisible();
    expect(screen.getByRole('button', { name: 'Enviar mensagem' })).toBeDisabled();
    expect(screen.getByText(/Nenhum modelo selecionado/)).toBeVisible();
  });

  it('Enter insere nova linha e Ctrl+Enter envia uma única mensagem', async () => {
    const user = userEvent.setup();
    render(<App />);
    const input = screen.getByRole('textbox', { name: 'Sua mensagem' });
    await user.type(input, 'TCP{Enter}UDP');
    expect(input).toHaveValue('TCP\nUDP');
    expect(screen.queryByRole('log')).not.toBeInTheDocument();
    await user.keyboard('{Control>}{Enter}{/Control}');
    const messages = screen.getByRole('log');
    expect(within(messages).getAllByRole('article')).toHaveLength(2);
    expect(within(messages).getByText(/TCP\s+UDP/)).toBeVisible();
    expect(within(messages).getByText(/Resposta local de teste/)).toBeVisible();
    expect(input).toHaveValue('');
  });

  it('mantém rascunhos e modos separados entre conversas', async () => {
    const user = userEvent.setup();
    render(<App />);
    await user.type(screen.getByRole('textbox', { name: 'Sua mensagem' }), 'Rascunho Linux');
    await user.selectOptions(screen.getByRole('combobox', { name: 'Modo de aprendizado' }), 'QUIZ');
    await user.click(screen.getByRole('button', { name: 'Criar nova conversa' }));
    expect(screen.getByRole('textbox', { name: 'Sua mensagem' })).toHaveValue('');
    await user.selectOptions(screen.getByRole('combobox', { name: 'Modo de aprendizado' }), 'LAB');
    const chats = within(screen.getByLabelText('Histórico de conversas')).getAllByRole('button');
    await user.click(chats[1]);
    expect(screen.getByRole('textbox', { name: 'Sua mensagem' })).toHaveValue('Rascunho Linux');
    expect(screen.getByRole('combobox', { name: 'Modo de aprendizado' })).toHaveValue('QUIZ');
  });

  it('preenche sugestão sem enviar e atualiza assunto e modo', async () => {
    const user = userEvent.setup();
    render(<App />);
    await user.click(screen.getByRole('button', { name: /Construir um laboratório/ }));
    expect(
      (screen.getByRole('textbox', { name: 'Sua mensagem' }) as HTMLTextAreaElement).value,
    ).toContain('laboratório local');
    expect(screen.getByRole('textbox', { name: 'Sua mensagem' })).toHaveFocus();
    expect(screen.getByRole('combobox', { name: 'Modo de aprendizado' })).toHaveValue('LAB');
    expect(screen.getByRole('combobox', { name: 'Assunto da conversa' })).toHaveValue('Labs');
    expect(screen.queryByRole('log')).not.toBeInTheDocument();
  });

  it('pesquisa mensagens, filtra categorias e mostra lista vazia', async () => {
    const user = userEvent.setup();
    render(<App />);
    await user.type(screen.getByRole('textbox', { name: 'Sua mensagem' }), 'Como funciona DNS?');
    await user.click(screen.getByRole('button', { name: 'Enviar mensagem' }));
    await user.click(screen.getByRole('button', { name: 'Linux' }));
    expect(screen.getByText('Nenhuma conversa encontrada.')).toBeVisible();
    await user.click(screen.getByRole('button', { name: /Todas as conversas/ }));
    const search = screen.getByRole('textbox', { name: 'Buscar conversas' });
    await user.type(search, 'dns');
    expect(
      within(screen.getByLabelText('Histórico de conversas')).getByRole('button', {
        name: 'Como funciona DNS?',
      }),
    ).toBeVisible();
    await user.clear(search);
    await user.type(search, 'não-existe');
    expect(screen.getByText('Nenhuma conversa encontrada.')).toBeVisible();
  });

  it('trata HTML como texto e não executa código enviado', async () => {
    const user = userEvent.setup();
    const { container } = render(<App />);
    const payload = '<img src="https://invalid.example/x" onerror="alert(1)">';
    await user.type(screen.getByRole('textbox', { name: 'Sua mensagem' }), payload);
    await user.click(screen.getByRole('button', { name: 'Enviar mensagem' }));
    expect(within(screen.getByRole('log')).getByText(payload)).toBeVisible();
    expect(container.querySelector('img')).toBeNull();
  });

  it('navega para materiais e configurações sem fingir recursos disponíveis', async () => {
    const user = userEvent.setup();
    render(<App />);
    await user.click(screen.getByRole('button', { name: 'Base de conhecimento' }));
    expect(screen.getByRole('button', { name: 'Adicionar documento' })).toBeDisabled();
    await user.click(screen.getByRole('button', { name: 'Configurações' }));
    expect(screen.getByRole('combobox', { name: 'Modelo de conversa' })).toBeDisabled();
    expect(screen.getByText(/salvos no SQLite local/)).toBeVisible();
  });
});
