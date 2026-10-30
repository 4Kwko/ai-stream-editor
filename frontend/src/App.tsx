import { useCallback, useEffect, useRef, useState, type KeyboardEvent } from 'react'
import { ApiError, isAbort } from './api/client'
import type { Api, Automation, AutomationPatch, GalleryFilter, GalleryItem, ReviewStatus } from './api/types'
import { AutomationPanel } from './components/AutomationPanel'
import { GalleryCard, type ReviewState } from './components/GalleryCard'
import { Icon } from './components/Icon'
import { SegmentedControl, type SegmentOption } from './components/SegmentedControl'
import { useAutomationStatus } from './hooks/useAutomationStatus'
import { loadValue, saveValue } from './lib/storage'

/** O contrato aceita de 1 a 50. */
const PAGE_SIZE = 20
const SKELETONS = 6

const FILTERS: readonly SegmentOption<GalleryFilter>[] = [
  { value: 'pending', label: 'Para avaliar' },
  { value: 'approved', label: 'Gostei' },
  { value: 'rejected', label: 'Não gostei' },
  { value: 'all', label: 'Todos' },
]

interface GalleryState {
  items: GalleryItem[]
  nextCursor: number | null
  loading: boolean
  loadingMore: boolean
  error: string | null
}

const EMPTY_GALLERY: GalleryState = { items: [], nextCursor: null, loading: true, loadingMore: false, error: null }

function messageOf(error: unknown, fallback: string): string {
  return error instanceof Error && error.message ? error.message : fallback
}

function galleryError(error: unknown, fallback: string): string {
  if (error instanceof ApiError && error.status === 404) return 'O backend em execução ainda não oferece a galeria.'
  return messageOf(error, fallback)
}

function isFilter(value: unknown): value is GalleryFilter {
  return FILTERS.some((filter) => filter.value === value)
}

function emptyMessage(filter: GalleryFilter, automation: Automation | null): string {
  if (filter === 'approved') return 'Nenhum corte marcado como Gostei.'
  if (filter === 'rejected') return 'Nenhum corte marcado como Não gostei.'
  const prefix = filter === 'pending' ? 'Nada para avaliar agora.' : 'Nenhum corte pronto ainda.'
  switch (automation?.status) {
    case 'waiting':
      return `${prefix} Aguardando uma gravação disponível neste canal.`
    case 'checking':
    case 'downloading':
    case 'analyzing':
    case 'rendering':
      return `${prefix} Os cortes aparecem aqui assim que o processamento terminar.`
    case 'configuration_required':
      return `${prefix} A automação precisa de configuração no backend.`
    case 'disabled':
      return `${prefix} A busca automática está desligada.`
    case 'stopped':
      return `${prefix} A busca automática não está em execução.`
    default:
      return prefix
  }
}

/** Alvo de foco de um card: o botão "Assistir" ou o player já montado. */
function cardFocusTarget(card: Element | undefined): HTMLElement | null {
  return card?.querySelector<HTMLElement>('[data-card-focus]') ?? null
}

/** Card vizinho na grade, pela posição na tela (funciona com qualquer número de colunas). */
function neighbor(cards: HTMLElement[], from: HTMLElement, key: string): HTMLElement | undefined {
  const index = cards.indexOf(from)
  if (key === 'ArrowRight') return cards[index + 1]
  if (key === 'ArrowLeft') return cards[index - 1]
  const origin = from.getBoundingClientRect()
  const below = key === 'ArrowDown'
  const candidates = cards.filter((card) => {
    const rect = card.getBoundingClientRect()
    return below ? rect.top > origin.top + 1 : rect.top < origin.top - 1
  })
  if (candidates.length === 0) return undefined
  const rowTop = below
    ? Math.min(...candidates.map((card) => card.getBoundingClientRect().top))
    : Math.max(...candidates.map((card) => card.getBoundingClientRect().top))
  const row = candidates.filter((card) => Math.abs(card.getBoundingClientRect().top - rowTop) < 2)
  return row.reduce((best, card) =>
    Math.abs(card.getBoundingClientRect().left - origin.left) < Math.abs(best.getBoundingClientRect().left - origin.left) ? card : best,
  )
}

export function App({ api, statusIntervalMs }: { api: Api; statusIntervalMs?: number }) {
  const [filter, setFilter] = useState<GalleryFilter>(() => {
    const saved = loadValue<unknown>('gallery-filter', 'pending')
    return isFilter(saved) ? saved : 'pending'
  })
  const [gallery, setGallery] = useState<GalleryState>(EMPTY_GALLERY)
  const [reloadKey, setReloadKey] = useState(0)
  const [hasNew, setHasNew] = useState(false)
  const [playingId, setPlayingId] = useState<string | null>(null)
  const [reviews, setReviews] = useState<Record<string, ReviewState>>({})
  const galleryRef = useRef(gallery)
  const gridRef = useRef<HTMLUListElement>(null)
  const loadMoreController = useRef<AbortController | null>(null)
  /**
   * Marca da galeria quando ela foi carregada pela última vez; base para detectar cortes novos.
   * Usa `gallery_updated_at` (muda a cada render bem-sucedido, inclusive parcial);
   * em backends sem o campo, o número de VODs concluídos.
   */
  const markerAtLoad = useRef<string | null>(null)
  const latestMarker = useRef<string | null>(null)

  useEffect(() => {
    galleryRef.current = gallery
  }, [gallery])

  const reload = useCallback(() => {
    markerAtLoad.current = latestMarker.current
    setHasNew(false)
    setGallery((current) => ({ ...current, loading: true, error: null }))
    setReloadKey((n) => n + 1)
  }, [])

  // Galeria mudou: lista vazia carrega sozinha; com cortes na tela, só avisa (sem reordenar).
  const handleAutomation = useCallback(
    (next: Automation) => {
      const marker =
        'gallery_updated_at' in next
          ? (next.gallery_updated_at ?? 'vazia')
          : next.counts
            ? `vods:${next.counts.completed}`
            : null
      latestMarker.current = marker
      if (marker === null) return
      if (markerAtLoad.current === null) {
        markerAtLoad.current = marker
        return
      }
      if (marker === markerAtLoad.current) return
      const current = galleryRef.current
      if (current.items.length === 0 && !current.loading && !current.error) reload()
      else setHasNew(true)
    },
    [reload],
  )
  const watch = useAutomationStatus(api, statusIntervalMs, handleAutomation)

  // Primeira página do filtro atual. Troca de filtro cancela a consulta anterior.
  useEffect(() => {
    const controller = new AbortController()
    loadMoreController.current?.abort()
    api.gallery({ review_status: filter, limit: PAGE_SIZE }, controller.signal).then(
      (page) => setGallery({ items: page.items, nextCursor: page.next_cursor, loading: false, loadingMore: false, error: null }),
      (error: unknown) => {
        if (isAbort(error)) return
        setGallery((current) => ({ ...current, loading: false, error: galleryError(error, 'Não foi possível carregar a galeria.') }))
      },
    )
    return () => controller.abort()
  }, [api, filter, reloadKey])

  useEffect(() => () => loadMoreController.current?.abort(), [])

  function changeFilter(next: GalleryFilter) {
    if (next === filter) return
    saveValue('gallery-filter', next)
    setPlayingId(null)
    setGallery(EMPTY_GALLERY)
    setFilter(next)
  }

  async function loadMore() {
    if (gallery.nextCursor === null || gallery.loadingMore) return
    const controller = new AbortController()
    loadMoreController.current = controller
    setGallery((current) => ({ ...current, loadingMore: true, error: null }))
    try {
      const page = await api.gallery({ review_status: filter, cursor: gallery.nextCursor, limit: PAGE_SIZE }, controller.signal)
      setGallery((current) => {
        const known = new Set(current.items.map((item) => item.id))
        return {
          ...current,
          items: [...current.items, ...page.items.filter((item) => !known.has(item.id))],
          nextCursor: page.next_cursor,
          loadingMore: false,
        }
      })
    } catch (error) {
      if (isAbort(error)) return
      setGallery((current) => ({ ...current, loadingMore: false, error: messageOf(error, 'Não foi possível carregar mais cortes.') }))
    }
  }

  async function review(item: GalleryItem, status: Exclude<ReviewStatus, 'pending'>): Promise<boolean> {
    if (reviews[item.id]?.saving) return false
    setReviews((all) => ({ ...all, [item.id]: { saving: true, saved: null, error: null } }))
    try {
      const result = await api.reviewClip(item.id, status)
      const confirmed = result.review_status ?? status
      setGallery((current) => ({
        ...current,
        items: current.items.map((candidate) => (candidate.id === item.id ? { ...candidate, review_status: confirmed } : candidate)),
      }))
      setReviews((all) => ({
        ...all,
        [item.id]: { saving: false, saved: confirmed === 'pending' ? null : confirmed, error: null },
      }))
      return true
    } catch (error) {
      setReviews((all) => ({ ...all, [item.id]: { saving: false, saved: null, error: messageOf(error, 'Erro desconhecido.') } }))
      return false
    }
  }

  /**
   * Atalhos de triagem (inspirados no P/X do Lightroom e no [ ] do Frame.io):
   * setas percorrem a grade, G = Gostei, N = Não gostei. Em "Para avaliar",
   * avaliar pelo teclado leva o foco ao próximo corte depois de salvo.
   */
  function handleGridKeyDown(event: KeyboardEvent<HTMLUListElement>) {
    if (event.altKey || event.ctrlKey || event.metaKey) return
    const target = event.target as HTMLElement
    if (target.closest('input, textarea, select')) return
    // Dentro do player, as setas pertencem aos controles de vídeo.
    if (target.tagName === 'VIDEO' && event.key.startsWith('Arrow')) return
    const card = target.closest<HTMLElement>('[data-clip-id]')
    if (!card || !gridRef.current) return
    const cards = Array.from(gridRef.current.querySelectorAll<HTMLElement>('[data-clip-id]'))

    if (event.key.startsWith('Arrow')) {
      const next = neighbor(cards, card, event.key)
      if (!next) return
      event.preventDefault()
      cardFocusTarget(next)?.focus()
      return
    }

    const key = event.key.toLowerCase()
    if (key !== 'g' && key !== 'n') return
    const item = gallery.items.find((candidate) => candidate.id === card.dataset.clipId)
    if (!item) return
    event.preventDefault()
    const status = key === 'g' ? 'approved' : 'rejected'
    if (item.review_status === status) return
    const next = cards[cards.indexOf(card) + 1]
    void review(item, status).then((saved) => {
      if (saved && filter === 'pending' && next) cardFocusTarget(next)?.focus()
    })
  }

  async function configure(patch: AutomationPatch) {
    watch.replace(await api.configureAutomation(patch))
  }

  const backendDown = watch.error?.kind === 'network'
  const showSkeleton = gallery.loading && gallery.items.length === 0

  return (
    <div className="app">
      <header className="topbar">
        <h1 className="wordmark">
          AI Stream Editor
        </h1>
        <p className="topbar__tagline">Cortes prontos para assistir e avaliar</p>
      </header>

      {api.mode === 'mock' && (
        <p className="banner" data-tone="demo" role="note">
          <span className="banner__tag">Demo</span>
          <span>
            <b>Modo demonstração.</b> Dados simulados no navegador; não há vídeos reais nem ligação com a Twitch.
          </span>
        </p>
      )}
      {backendDown && (
        <div className="banner" data-tone="error" role="alert">
          <Icon name="alert" />
          <span>
            <b>Backend local indisponível.</b> Abra o AI Stream Editor pelo atalho ou confira se ele está rodando em
            127.0.0.1:8765. Os cortes já carregados continuam na tela, mas os vídeos só tocam com o backend no ar.
          </span>
        </div>
      )}

      <main className="main">
        <AutomationPanel
          automation={watch.automation}
          error={backendDown ? null : watch.error}
          offline={backendDown}
          onRetry={watch.refresh}
          onConfigure={configure}
        />

        <section className="gallery" aria-labelledby="gallery-title">
          <div className="gallery__head">
            <div className="gallery__title">
              <h2 id="gallery-title">Galeria</h2>
              {gallery.items.length > 0 && (
                <p className="gallery__count">
                  {gallery.items.length} {gallery.items.length === 1 ? 'corte' : 'cortes'}
                  {gallery.nextCursor !== null ? ' carregados; há mais' : ''}
                </p>
              )}
            </div>
            <SegmentedControl label="Filtrar cortes" value={filter} options={FILTERS} onChange={changeFilter} />
          </div>

          <p className="shortcuts" aria-hidden="true">
            <kbd>←</kbd>
            <kbd>→</kbd> navegar · <kbd>G</kbd> Gostei · <kbd>N</kbd> Não gostei · <kbd>Enter</kbd> assistir
          </p>

          {hasNew && (
            <div className="notice" role="status">
              <span className="notice__marker" aria-hidden="true" />
              <span>Há cortes novos prontos.</span>
              <button type="button" className="btn btn--secondary btn--sm" onClick={reload}>
                Mostrar
              </button>
            </div>
          )}

          {gallery.error && (
            <div className="notice" data-tone="error" role="alert">
              <Icon name="alert" />
              <span>{gallery.error}</span>
              <button
                type="button"
                className="btn btn--secondary btn--sm"
                onClick={gallery.items.length ? () => void loadMore() : reload}
              >
                <Icon name="refresh" size={14} />
                Tentar de novo
              </button>
            </div>
          )}

          {showSkeleton && (
            <ul className="grid" aria-hidden="true">
              {Array.from({ length: SKELETONS }, (_, index) => (
                <li key={index} className="skeleton">
                  <span className="skeleton__frame" />
                  <span className="skeleton__line" />
                  <span className="skeleton__line skeleton__line--short" />
                </li>
              ))}
            </ul>
          )}
          {showSkeleton && <p className="visually-hidden" role="status">Carregando cortes…</p>}

          {!gallery.loading && !gallery.error && gallery.items.length === 0 && (
            <div className="empty">
              <Icon name="film" size={28} />
              <p>{emptyMessage(filter, watch.automation)}</p>
            </div>
          )}

          {gallery.items.length > 0 && (
            <ul className="grid" ref={gridRef} onKeyDown={handleGridKeyDown}>
              {gallery.items.map((item) => (
                <li key={item.id}>
                  <GalleryCard
                    item={item}
                    videoSrc={api.resolveUrl(item.preview_url)}
                    downloadSrc={api.resolveUrl(item.download_url)}
                    mockMode={api.mode === 'mock'}
                    playing={playingId === item.id}
                    onPlay={() => setPlayingId(item.id)}
                    review={reviews[item.id]}
                    onReview={(status) => void review(item, status)}
                  />
                </li>
              ))}
            </ul>
          )}

          {gallery.nextCursor !== null && (
            <div className="gallery__more">
              <button type="button" className="btn btn--secondary" onClick={() => void loadMore()} disabled={gallery.loadingMore}>
                {gallery.loadingMore ? 'Carregando…' : 'Carregar mais'}
              </button>
            </div>
          )}
        </section>
      </main>
    </div>
  )
}
