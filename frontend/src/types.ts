export const categories = ['Cybersecurity', 'Linux', 'Networking', 'Programming', 'Labs'] as const;
export type Category = (typeof categories)[number];
export type Mode = 'EXPLAIN' | 'TUTOR' | 'LAB' | 'QUIZ' | 'DEBUG' | 'ANALYZE' | 'COURSE';
export type Page = 'chat' | 'knowledge' | 'settings' | 'courses' | 'labs';
export type Source = {
  label: string;
  material_id: string;
  name: string;
  page: number;
  text: string;
};
export type Message = {
  sources?: Source[];
  id: string;
  role: 'user' | 'assistant';
  content: string;
  mode: Mode;
  status?: 'generating' | 'complete' | 'cancelled' | 'error';
  error?: string;
  model?: string;
  note?: string;
  finishReason?: string;
  tokensPerSecond?: number | null;
};
export type Chat = {
  id: string;
  title: string;
  category: Category;
  messages: Message[];
  draft: string;
  mode: Mode;
};

export const modes: { id: Mode; label: string; description: string }[] = [
  { id: 'TUTOR', label: 'Tutor', description: 'Aprenda passo a passo, do conceito à prática.' },
  { id: 'EXPLAIN', label: 'Explicar', description: 'Entenda o que acontece, como e por quê.' },
  {
    id: 'LAB',
    label: 'Laboratório',
    description: 'Explore um roteiro prático em ambiente controlado.',
  },
  { id: 'QUIZ', label: 'Quiz', description: 'Teste seus conhecimentos, uma pergunta por vez.' },
  { id: 'DEBUG', label: 'Depurar', description: 'Investigue erros e entenda suas causas.' },
  { id: 'ANALYZE', label: 'Analisar', description: 'Examine código, logs e configurações.' },
  {
    id: 'COURSE',
    label: 'Curso',
    description: 'Organize um caminho de estudos para seu objetivo.',
  },
];
