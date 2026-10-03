import { useEffect, useState } from 'react';
import { isTauri } from '@tauri-apps/api/core';
import { request } from '../services/backend';
import { MarkdownMessage } from './chat/MarkdownMessage';

type Lesson = {
  id: string;
  title: string;
  body: string;
  quiz: { question: string; choices: string[] };
  progress: { complete: boolean; attempts: number; passed: boolean };
};
type Course = {
  title: string;
  status: string;
  modules: { id: string; title: string; lessons: Lesson[] }[];
};
export function Courses({ onStudy }: { onStudy: (draft: string) => void }) {
  const [course, setCourse] = useState<Course | null>(null);
  const [selected, setSelected] = useState('ip');
  const [choice, setChoice] = useState<number | null>(null);
  const [feedback, setFeedback] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  async function refresh() {
    setCourse(await request<Course>('/learning/course'));
  }
  async function run(action: () => Promise<void>) {
    setBusy(true);
    setError('');
    try {
      await action();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Falha no curso.');
    } finally {
      setBusy(false);
    }
  }
  useEffect(() => {
    if (isTauri()) void run(refresh);
  }, []);
  const lessons = course?.modules.flatMap((module) => module.lessons) ?? [];
  const lesson = lessons.find((item) => item.id === selected);
  return (
    <section className="content-page">
      <div className="page-eyebrow">ESTUDO E PRÁTICA</div>
      <h1>Cursos</h1>
      <p className="page-intro">
        Comece pelos fundamentos e acompanhe suas revisões. Concluir a leitura e acertar o quiz são
        registros separados.
      </p>
      {!isTauri() && <p>Abra o aplicativo desktop para salvar seu progresso.</p>}
      {error && (
        <p role="alert">
          {error} <button onClick={() => void run(refresh)}>Tentar novamente</button>
        </p>
      )}
      {course && (
        <>
          <h2>{course.title}</h2>
          <p>{course.status}</p>
          <p role="status">
            {lessons.filter((item) => item.progress.complete).length}/{lessons.length} leituras
            concluídas · {lessons.filter((item) => item.progress.passed).length}/{lessons.length}{' '}
            quizzes aprovados
          </p>
          <div className="learning-layout">
            <nav aria-label="Lições do curso">
              {course.modules.map((module) => (
                <div key={module.id}>
                  <h3>{module.title}</h3>
                  {module.lessons.map((item) => (
                    <button
                      key={item.id}
                      aria-current={item.id === selected ? 'step' : undefined}
                      disabled={busy}
                      onClick={() => {
                        setSelected(item.id);
                        setChoice(null);
                        setFeedback('');
                      }}
                    >
                      {item.progress.complete ? '✓ ' : ''}
                      {item.title}
                    </button>
                  ))}
                </div>
              ))}
            </nav>
            {lesson && (
              <article className="lesson">
                <h2>{lesson.title}</h2>
                <MarkdownMessage content={lesson.body} />
                <button
                  disabled={busy}
                  onClick={() =>
                    void run(async () => {
                      await request(`/learning/lessons/${lesson.id}`, 'PUT', {
                        complete: !lesson.progress.complete,
                      });
                      await refresh();
                    })
                  }
                >
                  {lesson.progress.complete ? 'Marcar como não lida' : 'Concluir leitura'}
                </button>
                <button
                  onClick={() =>
                    onStudy(
                      `Quero aprofundar a lição “${lesson.title}” do curso de fundamentos de redes. Explique com um exemplo e verifique minha compreensão.`,
                    )
                  }
                >
                  Aprofundar com o tutor
                </button>
                <fieldset disabled={busy}>
                  <legend>{lesson.quiz.question}</legend>
                  {lesson.quiz.choices.map((text, index) => (
                    <label className="quiz-option" key={text}>
                      <input
                        type="radio"
                        name="quiz"
                        checked={choice === index}
                        onChange={() => setChoice(index)}
                      />
                      {text}
                    </label>
                  ))}
                  <button
                    disabled={choice === null}
                    onClick={() =>
                      void run(async () => {
                        const result = await request<{ correct: boolean; explanation: string }>(
                          `/learning/lessons/${lesson.id}/quiz`,
                          'POST',
                          { choice },
                        );
                        setFeedback(
                          `${result.correct ? 'Correto.' : 'Vamos revisar.'} ${result.explanation}`,
                        );
                        await refresh();
                      })
                    }
                  >
                    Conferir resposta
                  </button>
                </fieldset>
                {feedback && <p role="status">{feedback}</p>}
                <small>
                  Tentativas: {lesson.progress.attempts}. O progresso é um registro de estudo, não
                  uma certificação.
                </small>
              </article>
            )}
          </div>
        </>
      )}
      <p className="privacy-note">
        Quer outra trilha? O modo Curso pode propor um plano no chat. Planos gerados pela IA
        precisam de revisão e não são incorporados automaticamente ao conteúdo deste curso.
      </p>
      <button
        onClick={() =>
          onStudy(
            'Proponha um curso progressivo de cibersegurança. Primeiro pergunte meu nível e objetivo. Identifique a proposta como conteúdo gerado que precisa de revisão.',
          )
        }
      >
        Planejar outra trilha com o tutor
      </button>
    </section>
  );
}
