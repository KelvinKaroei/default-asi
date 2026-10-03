import { useEffect, useState } from 'react';
import { request } from '../services/backend';

type State = {
  running: boolean;
  ready: boolean;
  completed: number;
  total: number;
  chunks: number;
  error: string;
};
export function RetrievalPanel({ desktop, revision }: { desktop: boolean; revision: number }) {
  const [state, setState] = useState<State | null>(null);
  const [error, setError] = useState('');
  const [pending, setPending] = useState(false);
  useEffect(() => {
    if (!desktop) return;
    let alive = true;
    async function refresh() {
      try {
        const value = await request<State>('/retrieval');
        if (alive) {
          setState(value);
          setError('');
        }
      } catch (cause) {
        if (alive) setError(cause instanceof Error ? cause.message : 'Busca indisponível.');
      }
    }
    void refresh();
    const timer = setInterval(() => void refresh(), 2000);
    return () => {
      alive = false;
      clearInterval(timer);
    };
  }, [desktop, revision]);
  return (
    <section className="material-preview">
      <h2>Consulta pela IA</h2>
      <p>
        Prepare o índice após alterar o acervo. Depois, marque “Consultar materiais” no chat. Os
        trechos usados aparecem junto da resposta.
      </p>
      <button
        disabled={!desktop || pending || state?.running}
        onClick={async () => {
          setPending(true);
          setError('');
          try {
            setState(await request<State>('/retrieval/index', 'POST'));
          } catch (cause) {
            setError(cause instanceof Error ? cause.message : 'Não foi possível indexar.');
          } finally {
            setPending(false);
          }
        }}
      >
        Preparar índice local
      </button>
      <p role="status">
        {state?.running
          ? `Indexando ${state.completed} de ${state.total} trechos…`
          : state?.ready
            ? `Índice pronto · ${state.chunks} trechos`
            : 'Acervo ainda não preparado ou alterado. Prepare o índice para consultar.'}
      </p>
      {(error || state?.error) && <p role="alert">{error || state?.error}</p>}
    </section>
  );
}
