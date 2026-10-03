import { useCallback, useRef, useState } from 'react';
import { ChevronDown, Menu, ShieldCheck } from 'lucide-react';
import { Sidebar } from './components/Sidebar';
import { Composer } from './features/chat/Composer';
import { MessageList } from './features/chat/MessageList';
import { Welcome } from './features/chat/Welcome';
import { useChatSession } from './features/chat/useChatSession';
import { Courses } from './features/Courses';
import { Labs } from './features/Labs';
import { Knowledge } from './features/Knowledge';
import { Settings } from './features/Settings';
import { useLocalBackend } from './features/useLocalBackend';
import { categories, type Category, type Page } from './types';

export default function App() {
  const backend = useLocalBackend();
  const {
    chats,
    active,
    setActiveId,
    updateActive,
    newChat,
    send,
    cancel,
    retry,
    continueResponse,
    generatingChatId,
    persistence,
    useMaterials,
    setUseMaterials,
  } = useChatSession();
  const [page, setPage] = useState<Page>('chat');
  const [category, setCategory] = useState<Category | null>(null);
  const [query, setQuery] = useState('');
  const [menuOpen, setMenuOpen] = useState(false);
  const [confirmRestore, setConfirmRestore] = useState(false);
  const composer = useRef<HTMLTextAreaElement>(null);
  const closeMenu = useCallback(() => setMenuOpen(false), []);

  function navigate(next: Page) {
    setPage(next);
    setMenuOpen(false);
  }
  function startChat() {
    newChat(category ?? undefined);
    setQuery('');
    navigate('chat');
  }

  if (!persistence.ready)
    return (
      <main className="page-scroll">
        <h1>Histórico local</h1>
        <p role="status">{persistence.error || 'Carregando conversas salvas…'}</p>
        {persistence.error && (
          <button onClick={() => void persistence.retrySave()}>Tentar carregar novamente</button>
        )}
      </main>
    );

  return (
    <div className="app-shell">
      <div className="bios-masthead">
        <span>Default (ASI) / LOCAL</span>
        <span>LEARNING SYSTEM / 2026</span>
        <span>VER 0.14.1</span>
        <span>SESSÃO LOCAL</span>
      </div>
      <nav className="bios-tabs" aria-label="Módulos do tutor">
        {(
          [
            ['chat', 'CHAT'],
            ['courses', 'CURSOS'],
            ['labs', 'LABS'],
            ['knowledge', 'ARQUIVOS'],
            ['settings', 'SISTEMA'],
          ] as const
        ).map(([target, label]) => (
          <button
            key={target}
            aria-current={page === target ? 'page' : undefined}
            onClick={() => navigate(target)}
          >
            {label}
          </button>
        ))}
      </nav>
      <Sidebar
        chats={chats}
        activeId={active.id}
        category={category}
        query={query}
        page={page}
        open={menuOpen}
        onClose={closeMenu}
        onNew={startChat}
        onChat={(id) => {
          setActiveId(id);
          navigate('chat');
        }}
        onQuery={setQuery}
        onCategory={(value) => {
          setCategory(value);
          navigate('chat');
        }}
        onPage={navigate}
      />
      <main className="main-panel">
        <header className="topbar">
          <div className="breadcrumb">
            <button
              className="icon-button mobile-only"
              aria-label="Abrir menu"
              onClick={() => setMenuOpen(true)}
            >
              <Menu size={20} />
            </button>
            <span>Meu espaço</span>
            <span className="breadcrumb-slash">/</span>
            <strong>
              {page === 'chat'
                ? active.title
                : page === 'knowledge'
                  ? 'Base de conhecimento'
                  : page === 'courses'
                    ? 'Cursos'
                    : page === 'labs'
                      ? 'Laboratórios'
                      : 'Configurações'}
            </strong>
          </div>
          <div className="privacy-badge">
            {generatingChatId && page !== 'chat' && (
              <button className="icon-button" aria-label="Parar geração" onClick={cancel}>
                Parar geração
              </button>
            )}
            <ShieldCheck size={14} />
            <span>Local por design</span>
          </div>
        </header>
        <div className="history-status" aria-live="polite">
          <span>{persistence.error || persistence.storageStatus}</span>
          {persistence.error && (
            <button onClick={() => void persistence.retrySave()}>Tentar salvar novamente</button>
          )}
          <button
            disabled={!persistence.desktop || !!generatingChatId || persistence.busy}
            onClick={() => void persistence.maintenance(false)}
          >
            Criar backup
          </button>
          <button
            disabled={!persistence.desktop || !!generatingChatId || persistence.busy}
            onClick={() => setConfirmRestore(!confirmRestore)}
          >
            Restaurar backup
          </button>
          {confirmRestore && (
            <span>
              Substituir o histórico pelo último backup? Uma cópia do estado atual será preservada.{' '}
              <button
                disabled={!persistence.desktop || !!generatingChatId || persistence.busy}
                onClick={() => {
                  setConfirmRestore(false);
                  void persistence.maintenance(true);
                }}
              >
                Confirmar restauração
              </button>
            </span>
          )}
          {persistence.notice && <span>{persistence.notice}</span>}
        </div>
        {page === 'chat' ? (
          <>
            <div className="chat-toolbar">
              <label className="category-select">
                <span className="small-square" />
                <span className="sr-only">Assunto da conversa</span>
                <select
                  aria-label="Assunto da conversa"
                  value={active.category}
                  onChange={(event) => {
                    updateActive({ category: event.target.value as Category });
                    setCategory(null);
                  }}
                >
                  {categories.map((item) => (
                    <option key={item}>{item}</option>
                  ))}
                </select>
                <ChevronDown size={13} />
              </label>
              <label className="category-select">
                <input
                  type="checkbox"
                  checked={useMaterials}
                  disabled={!!generatingChatId}
                  onChange={(event) => setUseMaterials(event.target.checked)}
                />
                Consultar materiais
              </label>
            </div>
            <div className="chat-scroll">
              {active.messages.length ? (
                <MessageList
                  messages={active.messages}
                  onRetry={retry}
                  onContinue={continueResponse}
                  busy={!!generatingChatId}
                />
              ) : (
                <Welcome
                  onSuggestion={(draft, category, mode) => {
                    updateActive({ draft, category, mode });
                    setCategory(null);
                    composer.current?.focus();
                  }}
                />
              )}
            </div>
            <div className="chat-bottom">
              <div className="demo-notice">
                <ShieldCheck size={14} />
                <span>
                  {generatingChatId && generatingChatId !== active.id
                    ? 'Há uma geração em outra conversa. O botão Parar cancela essa geração.'
                    : 'Inferência local · confira comandos e respostas antes de usar.'}
                </span>
              </div>
              <Composer
                ref={composer}
                draft={active.draft}
                mode={active.mode}
                onDraft={(draft) => updateActive({ draft })}
                onMode={(mode) => updateActive({ mode })}
                onSend={send}
                generating={!!generatingChatId}
                onCancel={cancel}
              />
            </div>
          </>
        ) : (
          <div className="page-scroll">
            {page === 'knowledge' ? (
              <Knowledge />
            ) : page === 'courses' ? (
              <Courses
                onStudy={(draft) => {
                  newChat('Networking', draft, 'COURSE');
                  setUseMaterials(false);
                  navigate('chat');
                }}
              />
            ) : page === 'labs' ? (
              <Labs
                onStudy={(draft) => {
                  newChat('Labs', draft, 'LAB');
                  setUseMaterials(false);
                  navigate('chat');
                }}
              />
            ) : (
              <Settings backend={backend} />
            )}
          </div>
        )}
        <footer className="statusbar">
          <span>
            <i /> PROTÓTIPO 0.14.1 <b>/</b> HISTÓRICO LOCAL
          </span>
          <span>
            {backend.health?.ollama === 'ready' ? 'Ollama conectado' : 'Ollama não conectado'}{' '}
            <b>·</b>{' '}
            {backend.settings.model
              ? `Selecionado: ${backend.settings.model}`
              : 'Nenhum modelo selecionado'}
          </span>
        </footer>
      </main>
    </div>
  );
}
