import { useEffect, useState } from 'react';
import { isTauri } from '@tauri-apps/api/core';
import { request } from '../services/backend';
import { MarkdownMessage } from './chat/MarkdownMessage';
type Lab = {
  id: string;
  title: string;
  level: string;
  objective: string;
  requirements: string[];
  isolation: string;
  steps: { title: string; command: string | null; explanation: string; expected: string }[];
  errors: string[];
  defense: string;
  cleanup: string;
  reflection: string;
  completed: number[];
};
export function Labs({ onStudy }: { onStudy: (draft: string) => void }) {
  const [labs, setLabs] = useState<Lab[]>([]);
  const [selected, setSelected] = useState('loopback');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  async function refresh() {
    setLabs(await request<Lab[]>('/learning/labs'));
  }
  async function run(action: () => Promise<void>) {
    setBusy(true);
    setError('');
    try {
      await action();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Falha ao salvar checklist.');
    } finally {
      setBusy(false);
    }
  }
  useEffect(() => {
    if (isTauri()) void run(refresh);
  }, []);
  const lab = labs.find((item) => item.id === selected);
  return (
    <section className="content-page">
      <div className="page-eyebrow">APRENDER FAZENDO</div>
      <h1>Laboratórios guiados</h1>
      <p className="page-intro">
        Leia, copie e execute manualmente no ambiente indicado. O tutor não executa comandos. O
        checklist registra sua declaração de conclusão.
      </p>
      {!isTauri() && <p>Abra o aplicativo desktop para acompanhar os laboratórios.</p>}
      {error && (
        <p role="alert">
          {error} <button onClick={() => void run(refresh)}>Tentar novamente</button>
        </p>
      )}
      <nav className="lab-tabs" aria-label="Laboratórios">
        {labs.map((item) => (
          <button
            key={item.id}
            aria-pressed={selected === item.id}
            onClick={() => setSelected(item.id)}
          >
            {item.title}
          </button>
        ))}
      </nav>
      {lab && (
        <article className="lesson">
          <h2>{lab.title}</h2>
          <p>{lab.level}</p>
          <p>{lab.objective}</p>
          <h3>Pré-requisitos</h3>
          <ul>
            {lab.requirements.map((text) => (
              <li key={text}>{text}</li>
            ))}
          </ul>
          <h3>Ambiente</h3>
          <p>{lab.isolation}</p>
          <p>
            {lab.completed.length}/{lab.steps.length} etapas marcadas
          </p>
          {lab.steps.map((step, index) => (
            <section className="lab-step" key={step.title}>
              <h3>
                {index + 1}. {step.title}
              </h3>
              <p>{step.explanation}</p>
              {step.command && (
                <MarkdownMessage content={'```powershell\n' + step.command + '\n```'} />
              )}
              <p>
                <strong>Resultado esperado:</strong> {step.expected}
              </p>
              <label>
                <input
                  type="checkbox"
                  disabled={busy}
                  checked={lab.completed.includes(index)}
                  onChange={(event) => {
                    const complete = event.target.checked;
                    void run(async () => {
                      await request(`/learning/labs/${lab.id}/steps/${index}`, 'PUT', { complete });
                      await refresh();
                    });
                  }}
                />{' '}
                Concluí esta etapa
              </label>
            </section>
          ))}
          <h3>Erros comuns</h3>
          <ul>
            {lab.errors.map((text) => (
              <li key={text}>{text}</li>
            ))}
          </ul>
          <h3>Detecção e defesa</h3>
          <p>{lab.defense}</p>
          <h3>Limpeza</h3>
          <p>{lab.cleanup}</p>
          <h3>Verifique sua compreensão</h3>
          <p>{lab.reflection}</p>
          <button
            onClick={() =>
              onStudy(
                `Estou estudando o laboratório “${lab.title}”. Ajude-me a responder: ${lab.reflection}`,
              )
            }
          >
            Discutir com o tutor
          </button>
        </article>
      )}
    </section>
  );
}
