import { useEffect, useState } from 'react';
import { MemoryPanel } from './MemoryPanel';
import { Cpu, LockKeyhole } from 'lucide-react';
import type { LocalBackend } from './useLocalBackend';

export function Settings({ backend }: { backend: LocalBackend }) {
  const { health, hardware, models, settings, error, busy, probe } = backend;
  const [model, setModel] = useState(settings.model ?? '');
  const [context, setContext] = useState(settings.num_ctx);
  const [output, setOutput] = useState(settings.max_output ?? 8192);
  useEffect(() => {
    setModel(settings.model ?? '');
    setContext(settings.num_ctx);
    setOutput(settings.max_output ?? 8192);
  }, [settings]);
  const dirty =
    model !== (settings.model ?? '') ||
    context !== settings.num_ctx ||
    output !== (settings.max_output ?? 8192);
  return (
    <section className="content-page">
      <div className="page-eyebrow">SEU AMBIENTE</div>
      <h1>Configurações</h1>
      <p className="page-intro">Modelo, memória e diagnóstico no seu computador.</p>
      <div className="settings-section">
        <div className="settings-title">
          <Cpu size={20} />
          <div>
            <h2>Conexão local</h2>
            <p>{health?.message ?? 'Backend disponível no aplicativo desktop.'}</p>
          </div>
          <span className="status-pill muted">
            {health?.ollama === 'ready' ? `Ollama ${health.version}` : 'Não conectado'}
          </span>
        </div>
        <div className="diagnostic-actions">
          <button disabled={!!busy} onClick={() => void backend.refresh()}>
            Atualizar diagnóstico
          </button>
          <button
            disabled={!!busy || !health || health.ollama === 'ready'}
            onClick={() => void backend.start()}
          >
            Iniciar Ollama
          </button>
        </div>
        {error && (
          <p role="alert" className="diagnostic-error">
            {error}
          </p>
        )}
        <p role="status" className="setting-note">
          {busy ? `${busy}…` : 'Apenas conexões com 127.0.0.1. Nenhum download automático.'}
        </p>
        <label className="setting-field">
          Modelo de conversa
          <select
            aria-label="Modelo de conversa"
            disabled={!!busy || !models.installed.length}
            value={model}
            onChange={(e) => setModel(e.target.value)}
          >
            <option value="">Selecione um modelo instalado</option>
            {settings.model && !models.installed.some((m) => m.name === settings.model) && (
              <option value={settings.model}>{settings.model} (indisponível)</option>
            )}
            {models.installed.map((m) => (
              <option key={m.name} value={m.name}>
                {m.name} · {(m.size / 1e9).toFixed(1)} GB · {m.details?.quantization_level}
              </option>
            ))}
          </select>
        </label>
        {health?.ollama === 'ready' && !models.installed.length && (
          <p className="setting-note">
            Nenhum modelo local instalado. Consulte o guia da Fase 3 para instalar o Qwen3 8B.
          </p>
        )}
        <label className="setting-field">
          Janela de contexto
          <select
            aria-label="Janela de contexto"
            value={context}
            disabled={!!busy}
            onChange={(e) => setContext(Number(e.target.value))}
          >
            {[2048, 4096, 8192, 16384, 32768].map((n) => (
              <option key={n} value={n}>
                {n} tokens
              </option>
            ))}
          </select>
        </label>
        <p className="setting-note">
          Mais contexto mantém mais conversa e consome mais memória. Aumente gradualmente e teste a
          velocidade.
        </p>
        <label className="setting-field">
          Tamanho máximo de cada resposta
          <select
            aria-label="Tamanho máximo de cada resposta"
            value={output}
            disabled={!!busy}
            onChange={(e) => setOutput(Number(e.target.value))}
          >
            {[1024, 2048, 4096, 8192].map((n) => (
              <option key={n} value={n}>
                {n} tokens
              </option>
            ))}
          </select>
        </label>
        <p className="setting-note">
          A resposta reserva até metade do contexto. Respostas maiores podem demorar mais; use
          Continuar resposta quando necessário. Trechos antigos relevantes são buscados somente na
          conversa atual, sem memória ilimitada.
        </p>
        <div className="diagnostic-actions">
          <button
            disabled={!!busy || !health || !dirty}
            onClick={() =>
              void backend.save({ model: model || null, num_ctx: context, max_output: output })
            }
          >
            Salvar configuração
          </button>
          <button
            disabled={!!busy || dirty || !settings.model || health?.ollama !== 'ready'}
            onClick={() => void backend.test()}
          >
            Testar inferência local
          </button>
        </div>
        {probe && (
          <div className="probe-result">
            <strong>Teste concluído · {probe.model}</strong>
            <p>{probe.answer}</p>
            <p>
              {probe.tokens_per_second ?? '—'} tokens/s · {probe.total_seconds} s totais
            </p>
            <p>
              VRAM observada no teste:{' '}
              {(probe.loaded.reduce((sum, m) => sum + (m.size_vram ?? 0), 0) / 2 ** 30).toFixed(2)}{' '}
              GiB
            </p>
          </div>
        )}
        <p className="setting-note">
          Este diagnóstico usa uma frase fixa. Para estudar, abra uma conversa e envie sua pergunta.
        </p>
      </div>
      <div className="settings-section">
        <div className="settings-title">
          <Cpu size={20} />
          <div>
            <h2>Hardware detectado</h2>
            <p>{hardware?.cpu ?? 'Aguardando backend local'}</p>
          </div>
        </div>
        {hardware && (
          <>
            <div className="setting-row">
              <span>Sistema operacional</span>
              <span>{hardware.os}</span>
            </div>
            <div className="setting-row">
              <span>Memória RAM</span>
              <span>
                {hardware.ram_available_gib} GiB livres / {hardware.ram_total_gib} GiB
              </span>
            </div>
            {hardware.ram_available_gib < 6 && (
              <p className="setting-note">
                Há pouca RAM livre no momento. Fechar aplicativos pesados pode ajudar no
                carregamento do modelo; confirme o resultado no teste de inferência.
              </p>
            )}
            {hardware.gpus.map((g) => (
              <div className="setting-row" key={g.name}>
                <span>{g.name}</span>
                <span>
                  {(g.free_mib / 1024).toFixed(1)} / {(g.total_mib / 1024).toFixed(1)} GiB VRAM
                  livres
                </span>
              </div>
            ))}
            {!hardware.gpus.length && (
              <p className="setting-note">
                GPU NVIDIA não detectada; verifique o driver e o nvidia-smi.
              </p>
            )}
            <div className="setting-row">
              <span>Disco livre</span>
              <span>{hardware.disk_free_gib} GiB</span>
            </div>
            <p className="setting-note">
              {hardware.recommendation}. A velocidade depende da memória livre e será medida no
              teste.
            </p>
          </>
        )}
      </div>
      <div className="settings-section">
        <div className="settings-title">
          <LockKeyhole size={20} />
          <div>
            <h2>Privacidade e memória</h2>
            <p>Inferência local, sem serviços de nuvem.</p>
          </div>
        </div>
        <p className="setting-note">
          Conversas, respostas parciais e rascunhos são salvos no SQLite local. Aguarde a indicação
          de histórico salvo antes de fechar. Backups permanecem neste computador.
        </p>
      </div>
      <MemoryPanel />
    </section>
  );
}
