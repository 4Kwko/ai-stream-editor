import { useId, useState, type FormEvent } from 'react'
import type { ApiError } from '../api/client'
import type { Automation, AutomationPatch, AutomationStatusName, OutputFormat } from '../api/types'
import { formatDateTime } from '../lib/time'
import { Icon } from './Icon'
import { SegmentedControl, type SegmentOption } from './SegmentedControl'

const FORMAT_OPTIONS: readonly SegmentOption<OutputFormat>[] = [
  { value: '16:9', label: '16:9 horizontal' },
  { value: '9:16', label: '9:16 vertical' },
]

type Tone = 'ok' | 'busy' | 'warn' | 'error'

function describe(automation: Automation): { label: string; tone: Tone } {
  const labels: Record<AutomationStatusName, { label: string; tone: Tone }> = {
    stopped: { label: 'Busca automática parada: o serviço de automação não está em execução.', tone: 'warn' },
    disabled: { label: 'Busca automática desligada.', tone: 'warn' },
    checking: { label: 'Procurando gravações novas no canal', tone: 'busy' },
    waiting: {
      label: automation.counts?.completed
        ? 'Em dia. Aguardando a próxima gravação disponível neste canal.'
        : 'Aguardando uma gravação disponível neste canal.',
      tone: 'ok',
    },
    downloading: { label: 'Obtendo o vídeo', tone: 'busy' },
    analyzing: { label: 'Transcrevendo e analisando', tone: 'busy' },
    rendering: { label: 'Gerando cortes', tone: 'busy' },
    attention: { label: 'Precisa de atenção', tone: 'warn' },
    configuration_required: { label: 'Configuração necessária', tone: 'error' },
  }
  return labels[automation.status] ?? { label: `Estado não reconhecido: ${automation.status}`, tone: 'warn' }
}

const CHANNEL_PATTERN = /^[a-z0-9_]{3,25}$/

interface Props {
  automation: Automation | null
  error: ApiError | null
  /** Backend fora do ar (o aviso detalhado fica na faixa do topo). */
  offline?: boolean
  onRetry: () => void
  onConfigure: (patch: AutomationPatch) => Promise<void>
}

/**
 * Faixa de estado da automação. Como a barra de status de uma ferramenta de
 * edição: uma linha legível de relance, detalhes e configuração sob demanda.
 */
export function AutomationPanel({ automation, error, offline = false, onRetry, onConfigure }: Props) {
  const [settingsOpen, setSettingsOpen] = useState(false)
  const settingsId = useId()
  const { label, tone } = automation ? describe(automation) : { label: '', tone: 'ok' as Tone }
  const busy = tone === 'busy'
  const vod = automation?.active_vod
  const percent = vod?.progress != null ? Math.round(Math.min(Math.max(vod.progress, 0), 1) * 100) : null
  const counts = automation?.counts

  return (
    <section className="status" aria-labelledby="automation-title" data-tone={automation ? tone : undefined}>
      <h2 id="automation-title" className="visually-hidden">
        Automação
      </h2>

      {!automation && !error && !offline && (
        <div className="status__row">
          <span className="tally" aria-hidden="true" />
          <span className="status__label status__label--muted">Consultando a automação…</span>
        </div>
      )}

      {offline && (
        <div className="status__row">
          <span className="tally" data-tone="error" aria-hidden="true" />
          <span className="status__label">
            Sem conexão com o backend local. {automation ? 'Mostrando o último estado conhecido; ' : ''}nova tentativa
            automática.
          </span>
          <button type="button" className="btn btn--secondary btn--sm" onClick={onRetry}>
            <Icon name="refresh" size={14} />
            Tentar agora
          </button>
        </div>
      )}

      {error && (
        <div className="status__row" role="alert">
          <span className="tally" data-tone="error" aria-hidden="true" />
          <span className="status__label">
            {error.status === 404
              ? 'O backend em execução ainda não oferece a busca automática.'
              : `Não foi possível consultar a automação. ${error.message}`}
          </span>
          <button type="button" className="btn btn--secondary btn--sm" onClick={onRetry}>
            <Icon name="refresh" size={14} />
            Tentar de novo
          </button>
        </div>
      )}

      {automation && (
        <>
          <div className="status__row">
            <span className="tally" data-tone={tone} aria-hidden="true" />
            <span className="status__label" role="status" aria-live="polite">
              {label}
              {busy && vod?.title ? ` · ${vod.title}` : ''}
            </span>

            <dl className="status__meta">
              <div>
                <dt>Canal</dt>
                <dd>
                  {automation.channel_login ? (
                    automation.channel_url ? (
                      <a href={automation.channel_url} target="_blank" rel="noreferrer">
                        {automation.channel_login}
                      </a>
                    ) : (
                      automation.channel_login
                    )
                  ) : (
                    'nenhum'
                  )}
                </dd>
              </div>
              {counts && (
                <div>
                  <dt>Vídeos</dt>
                  <dd className="mono">
                    {counts.completed} {counts.completed === 1 ? 'processado' : 'processados'}
                    {counts.processing ? ` · ${counts.processing} em processamento` : ''}
                    {counts.queued ? ` · ${counts.queued} na fila` : ''}
                    {counts.failed ? ` · ${counts.failed} com falha` : ''}
                  </dd>
                </div>
              )}
              {automation.last_checked_at && (
                <div>
                  <dt>Última verificação</dt>
                  <dd className="mono">{formatDateTime(automation.last_checked_at)}</dd>
                </div>
              )}
              {automation.enabled && automation.runtime_active !== false && automation.next_check_at && (
                <div>
                  <dt>Próxima:</dt>
                  <dd className="mono">{formatDateTime(automation.next_check_at)}</dd>
                </div>
              )}
            </dl>

            <button
              type="button"
              className="btn btn--quiet btn--sm status__toggle"
              aria-expanded={settingsOpen}
              aria-controls={settingsId}
              onClick={() => setSettingsOpen((open) => !open)}
            >
              <Icon name="sliders" size={14} />
              Configurar canal
              <Icon name="chevron" size={14} className="status__chevron" />
            </button>
          </div>

          {busy && vod && (
            <div className="status__stage">
              <span>
                {vod.stage ? `Etapa: ${vod.stage} · ` : ''}
                {percent !== null ? `${percent}% desta etapa` : 'sem estimativa para esta etapa'}
              </span>
              <span
                className="progress"
                role="progressbar"
                aria-label="Progresso da etapa atual"
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={percent ?? undefined}
                aria-valuetext={percent === null ? 'Sem estimativa' : `${percent}% desta etapa`}
                data-indeterminate={percent === null || undefined}
              >
                <span className="progress__bar" style={percent === null ? undefined : { transform: `scaleX(${percent / 100})` }} />
              </span>
            </div>
          )}

          {/* Em estado normal a mensagem repete o rótulo; destaque só para problemas. */}
          {automation.message && (tone === 'warn' || tone === 'error') && (
            <p className="callout" data-tone={tone}>
              <Icon name="alert" size={14} />
              <span>{automation.message}</span>
            </p>
          )}
          {automation.message && busy && <p className="status__stage status__stage--note">{automation.message}</p>}

          {/* Sempre montado: abre e fecha com a mesma transição; fechado fica inerte (fora do foco e da leitura). */}
          <div className="collapse" data-open={settingsOpen} id={settingsId} inert={!settingsOpen}>
            <div className="collapse__inner">
              <AutomationSettings automation={automation} onConfigure={onConfigure} />
            </div>
          </div>
        </>
      )}

      <p className="status__note">
        A busca e o processamento acontecem no backend enquanto o AI Stream Editor estiver em execução neste computador,
        mesmo com esta página fechada. Com o app encerrado ou o PC desligado, nada é buscado.
      </p>
    </section>
  )
}

/** Configuração inicial: canal público e liga/desliga. Sem credenciais. */
function AutomationSettings({ automation, onConfigure }: { automation: Automation; onConfigure: (patch: AutomationPatch) => Promise<void> }) {
  const baseId = useId()
  const [channel, setChannel] = useState(automation.channel_login ?? '')
  const [enabled, setEnabled] = useState(automation.enabled)
  // Backends anteriores à extensão não têm formato: o seletor não aparece.
  const supportsFormat = automation.output_format !== undefined
  const [format, setFormat] = useState<OutputFormat>(automation.output_format ?? '16:9')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    const login = channel.trim().toLowerCase().replace(/^https?:\/\/(www\.)?twitch\.tv\//, '').replace(/\/.*$/, '')
    if (!CHANNEL_PATTERN.test(login)) {
      setError('Use o login do canal: 3 a 25 letras minúsculas, números ou _. Exemplo: joaomontagner')
      return
    }
    const patch: AutomationPatch = {}
    if (login !== automation.channel_login) patch.channel_login = login
    if (enabled !== automation.enabled) patch.enabled = enabled
    if (supportsFormat && format !== automation.output_format) patch.output_format = format
    if (Object.keys(patch).length === 0) {
      setError(null)
      setSaved(true)
      return
    }
    setSaving(true)
    setError(null)
    setSaved(false)
    try {
      await onConfigure(patch)
      setChannel(login)
      setSaved(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Não foi possível salvar a configuração.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={submit} noValidate className="settings">
      <div className="field">
        <label htmlFor={`${baseId}-channel`} className="field__label">
          Canal da Twitch (login)
        </label>
        <input
          id={`${baseId}-channel`}
          className="input"
          value={channel}
          onChange={(event) => setChannel(event.target.value)}
          spellCheck={false}
          autoComplete="off"
          aria-describedby={`${baseId}-help`}
          aria-invalid={error ? true : undefined}
        />
      </div>
      {supportsFormat && (
        <div className="field field--auto">
          <span className="field__label" aria-hidden="true">
            Formato dos próximos cortes
          </span>
          <SegmentedControl label="Formato dos próximos cortes" value={format} options={FORMAT_OPTIONS} onChange={setFormat} />
        </div>
      )}
      <label className="switch">
        <input type="checkbox" checked={enabled} onChange={(event) => setEnabled(event.target.checked)} />
        <span className="switch__track" aria-hidden="true">
          <span className="switch__thumb" />
        </span>
        Busca automática ligada
      </label>
      <button type="submit" className="btn btn--primary btn--sm" disabled={saving}>
        {saving ? 'Salvando…' : 'Salvar'}
      </button>
      <p id={`${baseId}-help`} className="settings__help">
        Só o canal público; não há senha nem chave. Trocar de canal não é possível enquanto um vídeo está sendo processado.
        {supportsFormat &&
          ' O formato vale para os próximos vídeos: cortes prontos não mudam. No 9:16 a câmera vai para cima quando é detectada com segurança; senão, a imagem inteira é preservada.'}
      </p>
      {saved && !error && (
        <p className="settings__result" role="status">
          <Icon name="check" size={14} />
          Configuração salva.
        </p>
      )}
      {error && (
        <p className="field-error" role="alert">
          {error}
        </p>
      )}
    </form>
  )
}
