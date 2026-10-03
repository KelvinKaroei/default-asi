import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import { MarkdownMessage, CopyButton } from './MarkdownMessage';

it('renderiza tabelas, listas, títulos e código inline', () => {
  const { container } = render(
    <MarkdownMessage
      content={
        '## Permissões\n\n- **Ler**\n- `chmod`\n\n| Tipo | Valor |\n| --- | --- |\n| Leitura | 4 |'
      }
    />,
  );
  expect(screen.getByRole('heading', { name: 'Permissões' })).toBeVisible();
  expect(screen.getByRole('table')).toHaveTextContent('Leitura');
  expect(container.querySelectorAll('li')).toHaveLength(2);
  expect(container.querySelector('code')).toHaveTextContent('chmod');
});

it.each(['python', 'javascript', 'json', 'desconhecida'])(
  'copia exatamente código %s sem números nem marcação',
  async (language) => {
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText } });
    const source = '  print("ação <tag>")\n\tlinha  \n';
    render(<MarkdownMessage content={'```' + language + '\n' + source + '\n```'} />);
    fireEvent.click(screen.getByRole('button', { name: 'Copiar código' }));
    await waitFor(() => expect(writeText).toHaveBeenCalledWith(source));
    expect(await screen.findByText('Copiado')).toBeVisible();
  },
);

it('não cria HTML ativo, imagens, iframes ou links executáveis', () => {
  const { container } = render(
    <MarkdownMessage
      content={
        '<script>alert(1)</script>\n\n<img src="https://example.test/pixel" onerror="alert(1)">\n\n![remota](https://example.test/a.png)\n\n![local](file:///C:/secret.txt)\n\n[executar](javascript:alert%281%29)\n\n<iframe src="https://example.test"></iframe>'
      }
    />,
  );
  expect(container.querySelector('script,img,iframe,a,object')).toBeNull();
  expect(screen.getByText(/Imagem não carregada: remota/)).toBeVisible();
});

it('mostra falha de clipboard e aceita bloco incompleto durante streaming', async () => {
  Object.defineProperty(navigator, 'clipboard', {
    configurable: true,
    value: { writeText: vi.fn().mockRejectedValue(new Error('negado')) },
  });
  const { rerender } = render(<MarkdownMessage content={'```python\nprint('} />);
  fireEvent.click(screen.getByRole('button', { name: 'Copiar código' }));
  expect(await screen.findByRole('status')).toHaveTextContent('Ctrl+C');
  rerender(<MarkdownMessage content={'```python\nprint("ok")\n```'} />);
  expect(screen.getByLabelText('Código python')).toHaveTextContent('print');
});

it('copia a mensagem original em Markdown', async () => {
  const writeText = vi.fn().mockResolvedValue(undefined);
  Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText } });
  render(<CopyButton text={'**texto**\n\n`código`'} label="Copiar mensagem" />);
  fireEvent.click(screen.getByRole('button', { name: 'Copiar mensagem' }));
  await waitFor(() => expect(writeText).toHaveBeenCalledWith('**texto**\n\n`código`'));
});
