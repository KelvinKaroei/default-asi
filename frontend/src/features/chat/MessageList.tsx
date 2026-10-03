import { useEffect, useRef } from 'react';
import { Shield } from 'lucide-react';
import type { Message } from '../../types';
import { CopyButton, MarkdownMessage } from './MarkdownMessage';

export function MessageList({
  messages,
  onRetry,
  onContinue,
  busy,
}: {
  messages: Message[];
  onRetry: () => void;
  onContinue?: () => void;
  busy: boolean;
}) {
  const bottom = useRef<HTMLDivElement>(null);
  useEffect(() => {
    bottom.current?.scrollIntoView({ block: 'end' });
  }, [messages]);
  return (
    <div
      className="messages"
      role="log"
      aria-label="Mensagens"
      aria-live="polite"
      aria-relevant="additions"
    >
      {messages.map((message) => (
        <article key={message.id} className={`message ${message.role}`}>
          <div className={`message-avatar ${message.role}`}>
            {message.role === 'assistant' ? <Shield size={18} /> : 'EU'}
          </div>
          <div className="message-body">
            <div className="message-heading">
              <strong>{message.role === 'assistant' ? 'Default (ASI)' : 'Você'}</strong>
              <span>
                {message.role === 'assistant' ? (message.model ?? 'LOCAL') : message.mode}
              </span>
            </div>
            {message.role === 'assistant' && message.content ? (
              <MarkdownMessage content={message.content} />
            ) : (
              <p>
                {message.content ||
                  (message.status === 'generating'
                    ? 'Preparando resposta local…'
                    : 'Nenhum texto recebido.')}
              </p>
            )}
            {message.content && <CopyButton text={message.content} label="Copiar mensagem" />}
            {!!message.sources?.length && (
              <details className="message-sources">
                <summary>Fontes consultadas ({message.sources.length})</summary>
                {message.sources.map((source) => (
                  <blockquote key={source.label}>
                    <strong>
                      [{source.label}] {source.name} · página {source.page}
                    </strong>
                    <p>{source.text}</p>
                  </blockquote>
                ))}
                <small>
                  Trechos usados nesta resposta; não garantem que cada afirmação do modelo esteja
                  correta.
                </small>
              </details>
            )}
            {message.status === 'generating' && <small role="status">Gerando resposta…</small>}
            {message.status === 'cancelled' && (
              <small>Geração cancelada · texto parcial preservado.</small>
            )}
            {message.error && (
              <p role="alert" className="diagnostic-error">
                {message.error}
              </p>
            )}
            {message === messages.at(-1) &&
              message.role === 'assistant' &&
              message.content &&
              message.status !== 'generating' &&
              onContinue && (
                <div className="diagnostic-actions">
                  <button disabled={busy} onClick={onContinue}>
                    Continuar resposta
                  </button>
                </div>
              )}
            {message.note && <p className="setting-note">{message.note}</p>}
            {message.tokensPerSecond != null && (
              <small>
                {message.tokensPerSecond} tokens/s · {message.mode}
              </small>
            )}
            {message === messages.at(-1) &&
              (message.status === 'error' || message.status === 'cancelled') && (
                <div className="diagnostic-actions">
                  <button disabled={busy} onClick={onRetry}>
                    Tentar novamente
                  </button>
                </div>
              )}
          </div>
        </article>
      ))}
      <div ref={bottom} />
    </div>
  );
}
