import { ArrowUp, ChevronDown, SlidersHorizontal, Square } from 'lucide-react';
import { forwardRef } from 'react';
import { modes, type Mode } from '../../types';

type Props = {
  draft: string;
  mode: Mode;
  onDraft: (value: string) => void;
  onMode: (mode: Mode) => void;
  onSend: () => void;
  generating: boolean;
  onCancel: () => void;
};

export const Composer = forwardRef<HTMLTextAreaElement, Props>(function Composer(
  { draft, mode, onDraft, onMode, onSend, generating, onCancel },
  ref,
) {
  const selected = modes.find((item) => item.id === mode)!;
  return (
    <div className="composer-area">
      <div className="composer">
        <label className="sr-only" htmlFor="message">
          Sua mensagem
        </label>
        <textarea
          id="message"
          ref={ref}
          value={draft}
          maxLength={12000}
          onChange={(event) => onDraft(event.target.value)}
          rows={3}
          placeholder="O que você quer entender hoje?"
          onKeyDown={(event) => {
            if (event.key === 'Enter' && event.ctrlKey && !event.nativeEvent.isComposing) {
              event.preventDefault();
              if (!generating) onSend();
            }
          }}
        />
        <div className="composer-tools">
          <label className="mode-select" title={selected.description}>
            <SlidersHorizontal size={14} />
            <span className="sr-only">Modo de aprendizado</span>
            <select
              aria-label="Modo de aprendizado"
              value={mode}
              onChange={(event) => onMode(event.target.value as Mode)}
            >
              {modes.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.label}
                </option>
              ))}
            </select>
            <ChevronDown size={13} />
          </label>
          <span className="mode-description">{selected.description}</span>
          <button
            className="send-button"
            disabled={!generating && !draft.trim()}
            onClick={generating ? onCancel : onSend}
            aria-label={generating ? 'Parar geração' : 'Enviar mensagem'}
            title={generating ? 'Cancelar a geração em andamento' : 'Enviar · Ctrl+Enter'}
          >
            {generating ? <Square size={16} /> : <ArrowUp size={20} />}
          </button>
        </div>
      </div>
      <div className="composer-caption">
        <span>
          <kbd>Enter</kbd> nova linha <b>·</b> <kbd>Ctrl + Enter</kbd> enviar
        </span>
        <span>Modelo local · confira o estado de salvamento</span>
      </div>
    </div>
  );
});
