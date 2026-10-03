import { isTauri } from '@tauri-apps/api/core';
import { useEffect, useRef, useState } from 'react';
import { RetrievalPanel } from './RetrievalPanel';
import { request } from '../services/backend';

type Material = {
  id: string;
  name: string;
  extension: string;
  size: number;
  created: string;
  encoding: string;
  warning: string;
};
type Detail = Material & { pages: { page: number; text: string }[] };
const formats =
  '.pdf,.txt,.md,.markdown,.py,.js,.ts,.tsx,.jsx,.json,.yaml,.yml,.toml,.ini,.cfg,.log,.csv,.sql,.sh,.ps1,.c,.h,.cpp,.rs,.go,.java,.css,.html,.xml';

function encode(file: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).split(',')[1]);
    reader.onerror = () => reject(new Error('Não foi possível ler o arquivo selecionado.'));
    reader.readAsDataURL(file);
  });
}

export function Knowledge() {
  const desktop = isTauri();
  const input = useRef<HTMLInputElement>(null);
  const [items, setItems] = useState<Material[]>([]);
  const [detail, setDetail] = useState<Detail | null>(null);
  const [page, setPage] = useState(0);
  const [offset, setOffset] = useState(0);
  const [busy, setBusy] = useState(false);
  const [revision, setRevision] = useState(0);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');
  const [encoding, setEncoding] = useState('utf-8');
  const [query, setQuery] = useState('');
  const [title, setTitle] = useState('');
  const [note, setNote] = useState('');
  const [removeId, setRemoveId] = useState<string | null>(null);

  async function refresh() {
    const result = await request<Material[]>('/materials');
    setItems(result);
    setLoaded(true);
    setRevision((value) => value + 1);
  }
  async function run(action: () => Promise<void>) {
    setBusy(true);
    setError('');
    setNotice('');
    try {
      await action();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Falha ao acessar materiais.');
    } finally {
      setBusy(false);
    }
  }
  useEffect(() => {
    if (desktop) void run(refresh);
  }, [desktop]);
  function select(value: Detail) {
    setDetail(value);
    setPage(0);
    setOffset(0);
    setRemoveId(null);
  }

  async function importMaterial(file: Blob, name: string, selectedEncoding = encoding) {
    if (!file.size || file.size > 5 * 1024 * 1024)
      throw new Error('Selecione um arquivo entre 1 byte e 5 MiB.');
    const result = await request<{ material: Detail; duplicate: boolean }>('/materials', 'POST', {
      name,
      content: await encode(file),
      encoding: selectedEncoding,
    });
    select(result.material);
    await refresh();
    setNotice(
      result.duplicate
        ? 'Este conteúdo já estava no acervo. Nenhuma cópia foi criada.'
        : 'Material importado e salvo neste computador.',
    );
  }
  const text = detail?.pages[page]?.text ?? '';
  return (
    <section className="content-page knowledge-page">
      <div className="page-eyebrow">SEU ACERVO PESSOAL</div>
      <h1>Base de conhecimento</h1>
      <p className="page-intro">
        Importe materiais, confira o texto extraído e prepare a consulta local pela IA.
      </p>
      {!desktop && <p>Abra o aplicativo desktop para importar materiais locais.</p>}
      <RetrievalPanel desktop={desktop} revision={revision} />
      <div className="material-toolbar">
        <input
          hidden
          type="file"
          ref={input}
          accept={formats}
          onChange={(event) => {
            const file = event.target.files?.[0];
            event.target.value = '';
            if (file) void run(() => importMaterial(file, file.name));
          }}
        />
        <button
          className="primary-button"
          disabled={!desktop || busy}
          onClick={() => input.current?.click()}
        >
          Adicionar documento
        </button>
        <label>
          Codificação de texto
          <select
            value={encoding}
            disabled={busy}
            onChange={(event) => setEncoding(event.target.value)}
          >
            <option value="utf-8">UTF-8 (padrão)</option>
            <option value="cp1252">Windows-1252</option>
          </select>
        </label>
        <button disabled={!desktop || busy} onClick={() => void run(refresh)}>
          Atualizar acervo
        </button>
      </div>
      <p className="setting-note">
        PDF textual, TXT, Markdown e código · até 5 MiB por arquivo e 200 páginas por PDF. UTF-16
        com BOM é detectado automaticamente. Sem OCR.
      </p>
      {busy && <p role="status">Processando material local…</p>}
      {error && (
        <p role="alert" className="diagnostic-error">
          {error}
        </p>
      )}
      {notice && <p role="status">{notice}</p>}
      <details className="material-note">
        <summary>Criar anotação</summary>
        <label>
          Título da anotação
          <input
            value={title}
            maxLength={150}
            disabled={busy}
            onChange={(event) => setTitle(event.target.value)}
          />
        </label>
        <label>
          Texto da anotação
          <textarea
            value={note}
            maxLength={100000}
            rows={5}
            disabled={busy}
            onChange={(event) => setNote(event.target.value)}
          />
        </label>
        <button
          disabled={!desktop || busy || !title.trim() || !note.trim()}
          onClick={() =>
            void run(async () => {
              await importMaterial(
                new Blob([note], { type: 'text/plain;charset=utf-8' }),
                title.trim() + '.md',
                'utf-8',
              );
              setNote('');
              setTitle('');
            })
          }
        >
          Salvar anotação
        </button>
      </details>
      <label className="material-search">
        Buscar material pelo nome
        <input value={query} onChange={(event) => setQuery(event.target.value)} />
      </label>
      {loaded && !items.length && (
        <p>Seu acervo está vazio. Adicione um documento ou uma anotação.</p>
      )}
      <ul className="material-list">
        {items
          .filter((item) => item.name.toLocaleLowerCase().includes(query.toLocaleLowerCase()))
          .map((item) => (
            <li key={item.id}>
              <button
                disabled={busy}
                onClick={() =>
                  void run(async () => select(await request<Detail>(`/materials/${item.id}`)))
                }
              >
                {item.name}
              </button>
              <small>
                {(item.size / 1024).toFixed(1)} KiB ·{' '}
                {new Date(item.created).toLocaleDateString('pt-BR')}
              </small>
              <button
                disabled={busy}
                aria-label={`Remover ${item.name}`}
                onClick={() => setRemoveId(item.id)}
              >
                Remover
              </button>
              {removeId === item.id && (
                <div>
                  Remover a cópia local e o texto extraído de {item.name}? O arquivo de origem
                  permanece intacto.{' '}
                  <button
                    disabled={busy}
                    onClick={() =>
                      void run(async () => {
                        await request(`/materials/${item.id}`, 'DELETE');
                        if (detail?.id === item.id) setDetail(null);
                        setRemoveId(null);
                        await refresh();
                        setNotice('Material removido do acervo.');
                      })
                    }
                  >
                    Confirmar remoção
                  </button>
                  <button onClick={() => setRemoveId(null)}>Cancelar</button>
                </div>
              )}
            </li>
          ))}
      </ul>
      {detail && (
        <section className="material-preview">
          <h2>{detail.name}</h2>
          {detail.warning && <p role="status">{detail.warning}</p>}
          <label>
            Página do material
            <select
              value={page}
              onChange={(event) => {
                setPage(Number(event.target.value));
                setOffset(0);
              }}
            >
              {detail.pages.map((item, index) => (
                <option key={item.page} value={index}>
                  Página {item.page}
                </option>
              ))}
            </select>
          </label>
          <pre>{text.slice(offset, offset + 30000) || 'Página sem texto extraível.'}</pre>
          {text.length > 30000 && (
            <div>
              <button
                disabled={offset === 0}
                onClick={() => setOffset(Math.max(0, offset - 30000))}
              >
                Trecho anterior
              </button>
              <span>
                {' '}
                Caracteres {offset + 1}–{Math.min(offset + 30000, text.length)} de{' '}
                {text.length}{' '}
              </span>
              <button
                disabled={offset + 30000 >= text.length}
                onClick={() => setOffset(offset + 30000)}
              >
                Próximo trecho
              </button>
            </div>
          )}
        </section>
      )}
      <p className="privacy-note">
        Originais e texto extraído ficam no banco local de materiais. Nenhum arquivo é executado ou
        enviado à nuvem. O backup de conversas não inclui o acervo.
      </p>
    </section>
  );
}
