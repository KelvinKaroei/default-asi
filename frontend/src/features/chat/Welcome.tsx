import { ArrowUpRight, Code2, Globe2, Network, ShieldCheck, Terminal } from 'lucide-react';
import type { Category, Mode } from '../../types';

const suggestions: {
  title: string;
  detail: string;
  prompt: string;
  category: Category;
  mode: Mode;
  icon: typeof Network;
  color: string;
}[] = [
  {
    title: 'Entender a rede',
    detail: 'TCP/IP, DNS e o caminho dos pacotes',
    prompt:
      'Explique como uma consulta DNS funciona, passo a passo, incluindo o que acontece na rede.',
    category: 'Networking',
    mode: 'EXPLAIN',
    icon: Network,
    color: 'teal',
  },
  {
    title: 'Explorar o Linux',
    detail: 'Permissões, processos e terminal',
    prompt:
      'Ensine permissões de arquivos no Linux com exemplos e explique cada parte dos comandos.',
    category: 'Linux',
    mode: 'TUTOR',
    icon: Terminal,
    color: 'blue',
  },
  {
    title: 'Construir um laboratório',
    detail: 'Da teoria a um ambiente controlado',
    prompt:
      'Monte um laboratório local para estudar segurança web, com pré-requisitos, passos e formas de defesa.',
    category: 'Labs',
    mode: 'LAB',
    icon: ShieldCheck,
    color: 'amber',
  },
  {
    title: 'Aprender com código',
    detail: 'Python, lógica e análise de erros',
    prompt:
      'Ensine como analisar um arquivo de log sintético com Python, explicando o código linha por linha.',
    category: 'Programming',
    mode: 'TUTOR',
    icon: Code2,
    color: 'purple',
  },
];

export function Welcome({
  onSuggestion,
}: {
  onSuggestion: (prompt: string, category: Category, mode: Mode) => void;
}) {
  return (
    <div className="welcome">
      <div className="welcome-eyebrow">
        <span /> CONHECIMENTO QUE FICA COM VOCÊ
      </div>
      <div className="hero-icon">
        <Globe2 size={31} strokeWidth={1.25} />
        <span className="orbit-dot" />
      </div>
      <h1>
        Entenda o sistema.
        <br />
        <span>Aprenda a protegê-lo.</span>
      </h1>
      <p className="hero-description">
        Seu tutor particular de cibersegurança.
        <br />
        Do primeiro conceito à prática, no seu ritmo.
      </p>
      <div className="suggestion-grid">
        {suggestions.map((item) => (
          <button
            className="suggestion-card"
            key={item.title}
            onClick={() => onSuggestion(item.prompt, item.category, item.mode)}
          >
            <div className="card-top">
              <item.icon className={item.color} size={21} strokeWidth={1.6} />
              <ArrowUpRight size={16} />
            </div>
            <strong>{item.title}</strong>
            <span>{item.detail}</span>
          </button>
        ))}
      </div>
      <div className="method">
        <span>CONCEITO</span>
        <i />
        <span>EXEMPLO</span>
        <i />
        <span>PRÁTICA</span>
        <i />
        <span>DEFESA</span>
      </div>
    </div>
  );
}
