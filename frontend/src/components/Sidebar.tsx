import { TerminalCompanion } from './TerminalCompanion';
import { useEffect, useRef } from 'react';
import {
  BookOpen,
  ChevronRight,
  Folder,
  MessageSquare,
  Plus,
  Search,
  Settings2,
  Shield,
  X,
} from 'lucide-react';
import { categories, type Category, type Chat, type Page } from '../types';

type Props = {
  chats: Chat[];
  activeId: string;
  category: Category | null;
  query: string;
  page: Page;
  open: boolean;
  onClose: () => void;
  onNew: () => void;
  onChat: (id: string) => void;
  onQuery: (value: string) => void;
  onCategory: (category: Category | null) => void;
  onPage: (page: Page) => void;
};

export function Sidebar(props: Props) {
  const panel = useRef<HTMLElement>(null);
  useEffect(() => {
    if (!props.open) return;
    const previousFocus = document.activeElement as HTMLElement | null;
    panel.current?.querySelector<HTMLButtonElement>('button')?.focus();
    function handleKeyboard(event: KeyboardEvent) {
      if (event.key === 'Escape') props.onClose();
      if (event.key !== 'Tab' || window.innerWidth > 900) return;
      const elements = panel.current?.querySelectorAll<HTMLElement>('button, input');
      if (!elements?.length) return;
      const first = elements[0];
      const last = elements[elements.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    }
    document.addEventListener('keydown', handleKeyboard);
    return () => {
      document.removeEventListener('keydown', handleKeyboard);
      previousFocus?.focus();
    };
  }, [props.open, props.onClose]);

  const filtered = props.chats.filter(
    (chat) =>
      (!props.category || chat.category === props.category) &&
      `${chat.title} ${chat.messages.map((message) => message.content).join(' ')}`
        .toLocaleLowerCase('pt-BR')
        .includes(props.query.toLocaleLowerCase('pt-BR')),
  );

  return (
    <>
      {props.open && (
        <button
          className="sidebar-backdrop"
          aria-label="Fechar navegação"
          onClick={props.onClose}
        />
      )}
      <aside
        ref={panel}
        className={`sidebar ${props.open ? 'is-open' : ''}`}
        aria-label="Navegação principal"
      >
        <div className="sidebar-content">
          <div className="brand">
            <div className="brand-mark">
              <Shield size={21} />
            </div>
            <div>
              Default<span>(ASI)</span>
              <small>LOCAL LEARNING SPACE</small>
            </div>
            <button
              className="icon-button mobile-only"
              aria-label="Fechar menu"
              onClick={props.onClose}
            >
              <X size={18} />
            </button>
          </div>
          <button className="new-chat" aria-label="Criar nova conversa" onClick={props.onNew}>
            <Plus size={18} /> Nova conversa <span aria-hidden="true">＋</span>
          </button>
          <label className="search">
            <Search size={16} />
            <input
              value={props.query}
              onChange={(event) => props.onQuery(event.target.value)}
              placeholder="Buscar conversas"
              aria-label="Buscar conversas"
            />
          </label>
          <nav className="topic-nav" aria-label="Assuntos">
            <div className="section-label">ESPAÇO DE ESTUDO</div>
            <button
              className={!props.category && props.page === 'chat' ? 'selected' : ''}
              onClick={() => props.onCategory(null)}
            >
              <MessageSquare size={17} /> Todas as conversas{' '}
              <span className="count">{props.chats.length}</span>
            </button>
            {categories.map((category) => (
              <button
                key={category}
                className={props.category === category && props.page === 'chat' ? 'selected' : ''}
                onClick={() => props.onCategory(category)}
              >
                <Folder size={16} />
                {category}
                <ChevronRight size={13} className="row-end" />
              </button>
            ))}
          </nav>
          <div className="recent-heading">
            <span className="section-label">CONVERSAS</span>
            <span className="tiny-dot" />
          </div>
          <div className="chat-list" aria-label="Histórico de conversas">
            {filtered.length ? (
              filtered.map((chat) => (
                <button
                  key={chat.id}
                  className={
                    props.activeId === chat.id && props.page === 'chat' ? 'active-chat' : ''
                  }
                  onClick={() => props.onChat(chat.id)}
                >
                  <MessageSquare size={15} />
                  <span>{chat.title}</span>
                </button>
              ))
            ) : (
              <p className="no-results">Nenhuma conversa encontrada.</p>
            )}
          </div>
          <div className="sidebar-bottom">
            <button
              className={props.page === 'courses' ? 'selected' : ''}
              onClick={() => props.onPage('courses')}
            >
              <BookOpen size={18} /> Cursos
            </button>
            <button
              className={props.page === 'labs' ? 'selected' : ''}
              onClick={() => props.onPage('labs')}
            >
              <Shield size={18} /> Laboratórios guiados
            </button>
            <button
              className={props.page === 'knowledge' ? 'selected' : ''}
              onClick={() => props.onPage('knowledge')}
            >
              <BookOpen size={18} /> Base de conhecimento
            </button>
            <button
              className={props.page === 'settings' ? 'selected' : ''}
              onClick={() => props.onPage('settings')}
            >
              <Settings2 size={18} /> Configurações
            </button>
          </div>
        </div>
        <TerminalCompanion />
      </aside>
    </>
  );
}
