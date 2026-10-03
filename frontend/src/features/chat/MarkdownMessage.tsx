import { Children, isValidElement, memo, useState } from 'react';
import type { ReactNode } from 'react';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Highlight, Prism, themes } from 'prism-react-renderer';

export function CopyButton({ text, label }: { text: string; label: string }) {
  const [copied, setCopied] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);
  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(text);
      setFailed(false);
    } catch {
      setFailed(true);
    }
  }
  return (
    <span className="copy-control">
      <button type="button" onClick={() => void copy()} aria-label={label}>
        {copied === text && !failed ? 'Copiado' : label}
      </button>
      {failed && (
        <small role="status">Não foi possível copiar. Selecione o texto e use Ctrl+C.</small>
      )}
    </span>
  );
}

function CodeBlock({ children }: { children?: ReactNode }) {
  const child = Children.toArray(children)[0];
  const props = isValidElement<{ children?: string; className?: string }>(child) ? child.props : {};
  // O conversor Markdown acrescenta uma quebra de linha estrutural ao <code>.
  // Removemos somente essa quebra, mantendo espaços, tabs e linhas vazias do conteúdo.
  const code = String(props.children ?? '').replace(/\n$/, '');
  const label = /language-([^\s]+)/.exec(props.className ?? '')?.[1] ?? 'texto';
  const aliases: Record<string, string> = {
    js: 'javascript',
    ts: 'typescript',
    py: 'python',
    sh: 'bash',
    shell: 'bash',
    html: 'markup',
  };
  const language = aliases[label.toLowerCase()] ?? label.toLowerCase();
  const highlighted = !!Prism.languages[language] && code.length <= 20000;
  return (
    <section className="code-block" aria-label={`Código ${label}`}>
      <header>
        <span>
          {label}
          {!highlighted ? ' · texto simples' : ''}
        </span>
        <CopyButton text={code} label="Copiar código" />
      </header>
      {highlighted ? (
        <Highlight code={code} language={language} theme={themes.vsDark}>
          {({ tokens, getTokenProps }) => (
            <pre tabIndex={0}>
              <code>
                {tokens.map((line, index) => (
                  <span key={index}>
                    {index > 0 && '\n'}
                    {line.map((token, key) => (
                      <span key={key} {...getTokenProps({ token })} />
                    ))}
                  </span>
                ))}
              </code>
            </pre>
          )}
        </Highlight>
      ) : (
        <pre tabIndex={0}>
          <code>{code}</code>
        </pre>
      )}
    </section>
  );
}

export const MarkdownMessage = memo(function MarkdownMessage({ content }: { content: string }) {
  return (
    <div className="markdown-message">
      <Markdown
        remarkPlugins={[remarkGfm]}
        components={{
          pre: ({ children }) => <CodeBlock>{children}</CodeBlock>,
          img: ({ alt }) => (
            <span className="blocked-image">[Imagem não carregada{alt ? `: ${alt}` : ''}]</span>
          ),
          // Referências permanecem visíveis, sem navegar para páginas ou executar protocolos.
          a: ({ children, href }) => (
            <span className="markdown-reference">
              {children}
              {href && ` (${href})`}
            </span>
          ),
          table: ({ children }) => (
            <div className="markdown-table" tabIndex={0}>
              <table>{children}</table>
            </div>
          ),
        }}
      >
        {content}
      </Markdown>
    </div>
  );
});
