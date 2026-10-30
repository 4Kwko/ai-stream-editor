import type { GalleryItem, ReviewStatus } from '../api/types'
import { formatDateTime, formatTimecode } from '../lib/time'
import { Icon } from './Icon'

type Choice = Exclude<ReviewStatus, 'pending'>

const LABELS: Record<ReviewStatus, string> = { pending: 'Para avaliar', approved: 'Gostei', rejected: 'Não gostei' }

export interface ReviewState {
  saving: boolean
  /** Escolha que acabou de ser confirmada pelo backend nesta sessão. */
  saved: Choice | null
  error: string | null
}

interface Props {
  item: GalleryItem
  /** URLs já resolvidas; null quando não há vídeo servível (ex.: modo demonstração). */
  videoSrc: string | null
  downloadSrc: string | null
  mockMode: boolean
  /** Só um card monta o player por vez. */
  playing: boolean
  onPlay: () => void
  review: ReviewState | undefined
  onReview: (status: Choice) => void
}

export function GalleryCard({ item, videoSrc, downloadSrc, mockMode, playing, onPlay, review, onReview }: Props) {
  const saving = review?.saving ?? false
  const titleId = `clip-title-${item.id}`
  const sourceLabel = item.source?.title ?? (item.source?.type === 'local' ? 'Arquivo local' : null)
  // Cortes antigos não trazem formato: pelo contrato, são 9:16 com o quadro inteiro.
  const format = item.output_format ?? '9:16'

  return (
    <article
      className="clip"
      aria-labelledby={titleId}
      data-clip-id={item.id}
      data-review={item.review_status}
      data-playing={playing || undefined}
    >
      <div className="clip__frame" data-format={format}>
        {playing && videoSrc ? (
          // Começa só depois do clique do usuário; nada toca sozinho ao abrir a galeria.
          <video className="clip__video" src={videoSrc} controls autoPlay preload="metadata" data-card-focus />
        ) : playing ? (
          <p className="clip__placeholder">
            {mockMode ? 'Modo demonstração: não há vídeo real.' : 'O backend não informou o endereço do vídeo.'}
          </p>
        ) : (
          <button type="button" className="clip__play" onClick={onPlay} aria-label={`Assistir ${item.title}`} data-card-focus>
            <span className="clip__play-icon">
              <Icon name="play" size={20} />
            </span>
          </button>
        )}

        {/* Marca de avaliação no canto do quadro, legível ao percorrer a grade. */}
        {item.review_status !== 'pending' && (
          <span className={`clip__flag clip__flag--${item.review_status}`} aria-hidden="true">
            <Icon name={item.review_status === 'approved' ? 'like' : 'dislike'} size={12} />
          </span>
        )}
        {!playing && (
          <>
            <span className="clip__format" aria-hidden="true">
              {format}
            </span>
            <span className="clip__timecode">{formatTimecode(item.duration_seconds)}</span>
          </>
        )}
      </div>

      <div className="clip__body">
        <h3 id={titleId} className="clip__title">
          {item.title || 'Corte sem título'}
        </h3>
        <p className="clip__meta">
          <span className="visually-hidden">
            Formato {format}. Duração {formatTimecode(item.duration_seconds)}. Estado:{' '}
          </span>
          <span className="visually-hidden">{LABELS[item.review_status]}</span>
          {sourceLabel && <span>{sourceLabel}</span>}
          {item.created_at && <span className="mono">{formatDateTime(item.created_at)}</span>}
          {item.layout === 'camera_top_content_bottom' && <span>Câmera em cima</span>}
        </p>
        {item.layout_warning && (
          <p className="clip__warning">
            <Icon name="alert" size={14} />
            <span>{item.layout_warning}</span>
          </p>
        )}

        <div className="rating" role="group" aria-label={`Avaliar ${item.title}`}>
          {(['approved', 'rejected'] as const).map((value) => (
            <button
              key={value}
              type="button"
              className={`rating__option rating__option--${value}`}
              aria-pressed={item.review_status === value}
              aria-keyshortcuts={value === 'approved' ? 'G' : 'N'}
              disabled={saving}
              onClick={() => item.review_status !== value && onReview(value)}
            >
              <Icon name={value === 'approved' ? 'like' : 'dislike'} />
              {LABELS[value]}
            </button>
          ))}
        </div>

        <div className="clip__footer">
          <p className={`clip__feedback ${review?.saved && !saving ? 'is-saved' : ''}`} role="status" aria-live="polite">
            {saving && 'Salvando…'}
            {!saving && review?.saved && (
              <>
                <Icon name="check" size={14} />
                {`Salvo: ${LABELS[review.saved]}`}
              </>
            )}
          </p>
          {downloadSrc && (
            <a className="btn btn--quiet btn--sm" href={downloadSrc} download>
              <Icon name="download" size={14} />
              Baixar MP4
            </a>
          )}
        </div>

        {review?.error && (
          <p className="clip__error" role="alert">
            <Icon name="alert" size={14} />
            <span>
              Não foi possível salvar. {review.error}{' '}
              {item.review_status === 'pending'
                ? 'O corte continua sem avaliação.'
                : `A escolha registrada continua: ${LABELS[item.review_status]}.`}
            </span>
          </p>
        )}
      </div>
    </article>
  )
}
