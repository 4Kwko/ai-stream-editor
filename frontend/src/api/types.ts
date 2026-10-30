// Tipos da API local (http://127.0.0.1:8765/api) para a automação e a galeria,
// conforme docs/coordination/integration-contract.md (extensão de 2026-10-30,
// mantida pelo GPT). Tempos em segundos, snake_case, datas UTC ISO 8601.
// Campos opcionais: a interface funciona sem eles.

/** Gostei = approved; Não gostei = rejected; Para avaliar = pending. */
export type ReviewStatus = 'pending' | 'approved' | 'rejected'

export type GalleryFilter = ReviewStatus | 'all'

export type AutomationStatusName =
  | 'stopped'
  | 'disabled'
  | 'checking'
  | 'waiting'
  | 'downloading'
  | 'analyzing'
  | 'rendering'
  | 'attention'
  | 'configuration_required'

export interface AutomationCounts {
  queued: number
  processing: number
  completed: number
  failed: number
  skipped: number
}

export interface ActiveVod {
  id: string
  title?: string | null
  url?: string | null
  stage?: string | null
  project_id?: string | null
  job_id?: string | null
  /** 0 a 1 da etapa atual, ou null sem estimativa real. Nunca total. */
  progress?: number | null
  progress_scope?: 'stage'
}

/** Formato de saída dos cortes. 16:9 preserva a imagem; 9:16 tenta câmera em cima e conteúdo embaixo. */
export type OutputFormat = '16:9' | '9:16'

export type ClipLayout = 'source_preserved' | 'camera_top_content_bottom' | 'full_frame'

/** Estado da automação persistente do backend (GET /automation). */
export interface Automation {
  enabled: boolean
  channel_login: string | null
  /** Formato dos próximos VODs; não reconverte o acervo. Ausente em backends antigos. */
  output_format?: OutputFormat
  /** Muda quando a galeria ganha artefatos; base para avisar cortes novos. */
  gallery_updated_at?: string | null
  channel_url?: string | null
  poll_interval_seconds?: number
  /** Supervisor iniciado no backend; não depende da página aberta. */
  runtime_active?: boolean
  status: AutomationStatusName
  /** PT-BR, sem caminhos privados. */
  message?: string | null
  last_checked_at?: string | null
  next_check_at?: string | null
  active_vod?: ActiveVod | null
  counts?: AutomationCounts | null
}

export interface AutomationPatch {
  enabled?: boolean
  channel_login?: string
  output_format?: OutputFormat
}

export interface GalleryItem {
  id: string
  project_id?: string
  title: string
  reason?: string | null
  score?: number | null
  review_status: ReviewStatus
  revision?: number
  duration_seconds: number
  /** Ausente em cortes antigos, que são 9:16 / full_frame. */
  output_format?: OutputFormat
  layout?: ClipLayout
  /** PT-BR, quando a câmera não pôde ser adaptada com segurança. */
  layout_warning?: string | null
  created_at?: string | null
  /** URL local absoluta do MP4 para assistir (com revisão). */
  preview_url: string
  /** URL local absoluta do mesmo MP4 como download (GET /clips/{id}/file). */
  download_url?: string | null
  source?: {
    type: 'local' | 'twitch' | string
    vod_id?: string | null
    channel_login?: string | null
    url?: string | null
    title?: string | null
  } | null
}

export interface GalleryPage {
  items: GalleryItem[]
  next_cursor: number | null
}

export interface GalleryQuery {
  review_status: GalleryFilter
  cursor?: number | null
  limit?: number
}

/** Resposta do PATCH /clips/{id}; só os campos usados aqui. */
export interface ClipReviewResult {
  id: string
  review_status: ReviewStatus
  revision?: number
}

export interface Health {
  status?: string
  [key: string]: unknown
}

/** Interface única que a UI usa. A implementação real e o mock seguem esta forma. */
export interface Api {
  readonly mode: 'real' | 'mock'
  health(signal?: AbortSignal): Promise<Health>
  automation(signal?: AbortSignal): Promise<Automation>
  configureAutomation(patch: AutomationPatch): Promise<Automation>
  gallery(query: GalleryQuery, signal?: AbortSignal): Promise<GalleryPage>
  /** Só registra a escolha; não altera nem regenera a mídia. */
  reviewClip(clipId: string, status: ReviewStatus): Promise<ClipReviewResult>
  /** URL que o elemento <video> ou um link conseguem abrir. */
  resolveUrl(url: string | null | undefined): string | null
}
