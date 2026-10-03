import { useEffect, useRef, useState } from 'react';
import type { Category, Chat, Message, Mode } from '../../types';
import { streamChat } from '../../services/chat';
import { useHistory } from '../useHistory';

const CONTINUE_PROMPT =
  'Continue a resposta anterior exatamente do ponto em que parou, sem repetir a introdução. Conclua a explicação pendente.';

function createChat(category: Category = 'Cybersecurity', mode: Mode = 'TUTOR'): Chat {
  return {
    id: crypto.randomUUID(),
    title: 'Nova conversa',
    category,
    mode,
    messages: [],
    draft: '',
  };
}

export function useChatSession() {
  const [chats, setChats] = useState<Chat[]>(() => [createChat()]);
  const persistence = useHistory(chats, setChats);
  const [useMaterials, setUseMaterials] = useState(false);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [generatingChatId, setGeneratingChatId] = useState<string | null>(null);
  const running = useRef<AbortController | null>(null);
  const active = chats.find((chat) => chat.id === activeId) ?? chats[0];
  useEffect(() => () => running.current?.abort(), []);

  function updateActive(update: Partial<Chat>) {
    if (!persistence.ready || persistence.busy) return;
    setChats((items) =>
      items.map((chat) => (chat.id === active.id ? { ...chat, ...update } : chat)),
    );
  }
  function newChat(category?: Category, draft = '', mode?: Mode) {
    if (!persistence.ready || persistence.busy) return;
    const chat = createChat(category ?? active.category, mode ?? active.mode);
    chat.draft = draft;
    setChats((items) => [chat, ...items]);
    setActiveId(chat.id);
  }
  function cancel() {
    running.current?.abort();
  }

  async function generate(content: string, retry = false, continuation = false) {
    if (!content.trim() || running.current || !persistence.ready || persistence.busy) return;
    continuation = continuation || (retry && content === CONTINUE_PROMPT);
    const controller = new AbortController();
    running.current = controller;
    const chatId = active.id;
    setGeneratingChatId(chatId);
    const previous = retry ? active.messages.slice(0, -2) : active.messages;
    const mode = retry ? active.messages.at(-2)!.mode : active.mode;
    const user: Message = { id: crypto.randomUUID(), role: 'user', content, mode };
    const assistant: Message = {
      id: crypto.randomUUID(),
      role: 'assistant',
      content: '',
      mode,
      status: 'generating',
    };
    const pairs: { role: 'user' | 'assistant'; content: string }[] = [];
    for (let index = 0; index + 1 < previous.length; index += 2) {
      const reply = previous[index + 1];
      if (
        reply.status === 'complete' ||
        (continuation && index + 1 === previous.length - 1 && reply.content)
      )
        pairs.push(previous[index], reply);
    }
    // Limita o transporte; o backend aplica o orçamento final do contexto.
    const history = pairs.map(({ role, content }) => ({ role, content }));
    while (new TextEncoder().encode(JSON.stringify(history)).length > 7 * 1024 * 1024)
      history.splice(0, 2);
    const omittedLocally = previous.length - history.length;
    setChats((items) =>
      items.map((chat) =>
        chat.id === chatId
          ? {
              ...chat,
              title: previous.length ? chat.title : content.replace(/\s+/g, ' ').slice(0, 52),
              draft: retry || continuation ? chat.draft : '',
              messages: [...previous, user, assistant],
            }
          : chat,
      ),
    );
    function updateMessage(update: Partial<Message> | ((message: Message) => Partial<Message>)) {
      setChats((items) =>
        items.map((chat) =>
          chat.id === chatId
            ? {
                ...chat,
                messages: chat.messages.map((message) =>
                  message.id === assistant.id
                    ? {
                        ...message,
                        ...(typeof update === 'function' ? update(message) : update),
                      }
                    : message,
                ),
              }
            : chat,
        ),
      );
    }
    try {
      await streamChat(
        mode,
        [...history, { role: 'user', content }],
        controller.signal,
        (event) => {
          if (controller.signal.aborted) return;
          if (event.type === 'start')
            updateMessage({
              model: event.model,
              sources: event.sources,
              note:
                event.omitted_messages + omittedLocally
                  ? `${event.omitted_messages + omittedLocally} mensagens não entraram integralmente; trechos antigos relevantes podem ser recuperados nesta conversa.`
                  : undefined,
            });
          if (event.type === 'delta')
            updateMessage((message) => ({ content: message.content + event.content }));
          if (event.type === 'done')
            updateMessage({
              status: 'complete',
              finishReason: event.reason,
              tokensPerSecond: event.tokens_per_second,
              ...(event.reason === 'length'
                ? {
                    note: 'Limite desta parte atingido. Use Continuar resposta para retomar de onde parou.',
                  }
                : {}),
            });
        },
        useMaterials,
        continuation,
      );
      if (controller.signal.aborted) updateMessage({ status: 'cancelled' });
    } catch (error) {
      updateMessage({
        status: controller.signal.aborted ? 'cancelled' : 'error',
        error: controller.signal.aborted
          ? undefined
          : error instanceof Error
            ? error.message
            : 'Não foi possível gerar a resposta.',
      });
    } finally {
      if (running.current === controller) {
        running.current = null;
        setGeneratingChatId(null);
      }
    }
  }
  function send() {
    void generate(active.draft.trim());
  }
  function continueResponse() {
    const last = active.messages.at(-1);
    if (last?.role === 'assistant' && last.content && last.status !== 'generating')
      void generate(CONTINUE_PROMPT, false, true);
  }
  function retry() {
    const last = active.messages.at(-1);
    if (last && (last.status === 'error' || last.status === 'cancelled'))
      void generate(active.messages.at(-2)!.content, true);
  }
  return {
    persistence,
    useMaterials,
    setUseMaterials,
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
  };
}
