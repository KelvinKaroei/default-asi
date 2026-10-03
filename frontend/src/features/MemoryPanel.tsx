import { useEffect, useState } from 'react';
import { isTauri } from '@tauri-apps/api/core';
import { request } from '../services/backend';
type State = { enabled: boolean; items: { id: string; text: string }[] };
export function MemoryPanel() {
  const [state, setState] = useState<State | null>(null);
  const [text, setText] = useState('');
  const [editing, setEditing] = useState<string | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [confirm, setConfirm] = useState(false);
  async function run(action: () => Promise<State>) {
    setBusy(true);
    setError('');
    try {
      setState(await action());
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Memória indisponível.');
    } finally {
      setBusy(false);
    }
  }
  useEffect(() => {
    if (isTauri()) void run(() => request<State>('/memory'));
  }, []);
  return (
    <section className="settings-section">
      <h2>Memória de aprendizado</h2>
      <p>
        Guarde somente preferências e conhecimentos que você confirmar. Desativada por padrão.
        Nenhuma conversa é resumida ou analisada automaticamente.
      </p>
      {!isTauri() && <p>Disponível no aplicativo desktop.</p>}
      {error && (
        <p role="alert">
          {error}{' '}
          {!state && (
            <button onClick={() => void run(() => request<State>('/memory'))}>
              Tentar novamente
            </button>
          )}
        </p>
      )}
      {state && (
        <>
          <label>
            <input
              type="checkbox"
              checked={state.enabled}
              disabled={busy}
              onChange={(event) => {
                const enabled = event.target.checked;
                void run(() => request<State>('/memory/enabled', 'PUT', { enabled }));
              }}
            />{' '}
            Usar memórias nas próximas respostas
          </label>
          <p>
            {state.enabled
              ? 'Ativa: memórias confirmadas podem entrar no contexto.'
              : 'Desativada: o tutor não consulta estas memórias. Você ainda pode inspecionar ou apagar.'}
          </p>
          <ul>
            {state.items.map((item) => (
              <li key={item.id}>
                <p>{item.text}</p>
                <button
                  disabled={busy || !state.enabled}
                  onClick={() => {
                    setEditing(item.id);
                    setText(item.text);
                  }}
                >
                  Editar memória
                </button>
                <button
                  disabled={busy}
                  onClick={() => void run(() => request<State>(`/memory/${item.id}`, 'DELETE'))}
                >
                  Apagar memória
                </button>
              </li>
            ))}
          </ul>
          <label className="setting-field">
            {editing ? 'Editar preferência' : 'Nova preferência confirmada'}
            <textarea
              maxLength={160}
              value={text}
              disabled={busy || !state.enabled}
              onChange={(event) => setText(event.target.value)}
            />
          </label>
          <button
            disabled={busy || !state.enabled || !text.trim()}
            onClick={() =>
              void run(async () => {
                const value = await request<State>(
                  editing ? `/memory/${editing}` : '/memory',
                  editing ? 'PUT' : 'POST',
                  { text },
                );
                setText('');
                setEditing(null);
                return value;
              })
            }
          >
            Confirmar e salvar memória
          </button>
          {editing && (
            <button
              onClick={() => {
                setEditing(null);
                setText('');
              }}
            >
              Cancelar edição
            </button>
          )}
          <details>
            <summary>Sugestões para preencher</summary>
            <p>Edite o texto e salve somente se representar você.</p>
            {[
              'Prefiro explicações passo a passo com exemplos curtos.',
              'Estou estudando fundamentos de redes.',
              'Já entendo endereços IPv4 e quero praticar sub-redes.',
            ].map((value) => (
              <button
                key={value}
                disabled={!state.enabled || busy}
                onClick={() => {
                  setText(value);
                  setEditing(null);
                }}
              >
                {value}
              </button>
            ))}
          </details>
          <p>
            Até três memórias; limite total de 500 bytes. O contexto é limitado e pode deixar
            memórias de fora. Desativar afeta as próximas respostas, não uma geração já iniciada. O
            histórico e suas cópias de segurança são independentes.
          </p>
          <button disabled={busy || !state.items.length} onClick={() => setConfirm(true)}>
            Limpar todas as memórias
          </button>
          {confirm && (
            <div>
              Apagar todas as preferências salvas?{' '}
              <button
                disabled={busy}
                onClick={() =>
                  void run(async () => {
                    const value = await request<State>('/memory', 'DELETE');
                    setConfirm(false);
                    setText('');
                    setEditing(null);
                    return value;
                  })
                }
              >
                Confirmar limpeza
              </button>
              <button onClick={() => setConfirm(false)}>Cancelar</button>
            </div>
          )}
        </>
      )}
    </section>
  );
}
