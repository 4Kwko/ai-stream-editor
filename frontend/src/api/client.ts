import type { Api, Automation, ClipReviewResult, GalleryItem, GalleryPage, Health } from './types'

/**
 * Em desenvolvimento o Vite encaminha /api para http://127.0.0.1:8765/api
 * (vite.config.ts), então o navegador não precisa de CORS.
 * VITE_API_BASE_URL permite apontar direto para outro endereço.
 */
export const DEFAULT_API_BASE_URL: string = import.meta.env.VITE_API_BASE_URL ?? '/api'

export type ApiErrorKind = 'network' | 'http' | 'invalid_response' | 'aborted'

export class ApiError extends Error {
  readonly kind: ApiErrorKind
  readonly status: number | null

  constructor(kind: ApiErrorKind, message: string, status: number | null = null) {
    super(message)
    this.name = 'ApiError'
    this.kind = kind
    this.status = status
  }
}

export function isAbort(error: unknown): boolean {
  return error instanceof ApiError && error.kind === 'aborted'
}

type FetchLike = (input: string, init?: RequestInit) => Promise<Response>

/** Extrai uma mensagem legível dos formatos de erro mais comuns (FastAPI usa "detail"). */
function errorMessageFromBody(body: unknown): string | null {
  if (typeof body === 'string' && body.trim()) return body.trim()
  if (body && typeof body === 'object') {
    const record = body as Record<string, unknown>
    for (const key of ['detail', 'error', 'message']) {
      const value = record[key]
      if (typeof value === 'string' && value.trim()) return value.trim()
      if (Array.isArray(value) && value.length > 0) {
        const first = value[0] as Record<string, unknown> | string
        if (typeof first === 'string') return first
        if (first && typeof first.msg === 'string') return first.msg
      }
    }
  }
  return null
}

function joinUrl(base: string, path: string): string {
  return base.replace(/\/+$/, '') + path
}

export function createApiClient(baseUrl: string = DEFAULT_API_BASE_URL, fetchImpl: FetchLike = fetch): Api {
  async function request<T>(method: string, path: string, options: { body?: unknown; signal?: AbortSignal } = {}): Promise<T> {
    const init: RequestInit = { method, headers: { Accept: 'application/json' }, signal: options.signal }
    if (options.body !== undefined) {
      init.headers = { ...init.headers, 'Content-Type': 'application/json' }
      init.body = JSON.stringify(options.body)
    }

    let response: Response
    try {
      response = await fetchImpl(joinUrl(baseUrl, path), init)
    } catch (error) {
      if (options.signal?.aborted || (error instanceof DOMException && error.name === 'AbortError')) {
        throw new ApiError('aborted', 'Consulta cancelada.')
      }
      throw new ApiError('network', 'Não foi possível falar com o backend local.')
    }

    // 502/504 vêm do proxy do Vite quando o backend não responde: é indisponibilidade, não erro da API.
    if (response.status === 502 || response.status === 504) {
      throw new ApiError('network', 'Não foi possível falar com o backend local.', response.status)
    }

    const text = await response.text()
    let parsed: unknown = null
    if (text) {
      try {
        parsed = JSON.parse(text)
      } catch {
        parsed = text
      }
    }

    if (!response.ok) {
      const detail = errorMessageFromBody(parsed)
      throw new ApiError('http', detail ?? `O backend respondeu com erro ${response.status}.`, response.status)
    }
    if (parsed === null || typeof parsed !== 'object') {
      throw new ApiError('invalid_response', 'Resposta inesperada do backend.', response.status)
    }
    return parsed as T
  }

  /** URL absoluta ou relativa à mesma origem; caminhos /api/... respeitam a base configurada. */
  function resolve(url: string | null | undefined): string | null {
    if (!url) return null
    if (/^https?:\/\//i.test(url)) return url
    if (url.startsWith('/api/') && /^https?:\/\//i.test(baseUrl) && baseUrl.endsWith('/api')) {
      return baseUrl.slice(0, -'/api'.length) + url
    }
    return url
  }

  return {
    mode: 'real',
    health: (signal) => request<Health>('GET', '/health', { signal }),
    automation: (signal) => request<Automation>('GET', '/automation', { signal }),
    configureAutomation: (patch) => request<Automation>('PATCH', '/automation', { body: patch }),
    gallery: async (query, signal) => {
      const params = new URLSearchParams({ review_status: query.review_status, limit: String(query.limit ?? 20) })
      // Cursor opaco: repassado como veio do backend.
      if (query.cursor != null) params.set('cursor', String(query.cursor))
      const page = await request<GalleryPage | GalleryItem[]>('GET', `/gallery?${params}`, { signal })
      if (Array.isArray(page)) return { items: page, next_cursor: null }
      if (!Array.isArray(page.items)) throw new ApiError('invalid_response', 'A galeria veio em formato inesperado.')
      return page
    },
    // Avaliar usa o PATCH de revisão existente; não altera revisão nem mídia.
    reviewClip: (clipId, status) =>
      request<ClipReviewResult>('PATCH', `/clips/${encodeURIComponent(clipId)}`, { body: { review_status: status } }),
    resolveUrl: resolve,
  }
}
