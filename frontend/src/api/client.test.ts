import { describe, expect, it, vi } from 'vitest'
import { ApiError, createApiClient, isAbort } from './client'
import type { GalleryItem } from './types'

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
}

const ITEM = {
  id: 'c1',
  title: 'T',
  duration_seconds: 30,
  review_status: 'pending',
  preview_url: '/api/clips/c1/preview?revision=1',
  download_url: '/api/clips/c1/file?revision=1',
} as GalleryItem

describe('createApiClient', () => {
  it('lê a automação com GET /automation', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ status: 'waiting', enabled: true, channel_login: 'x' }))
    await createApiClient('/api', fetchMock).automation()
    expect(fetchMock.mock.calls[0][0]).toBe('/api/automation')
    expect(fetchMock.mock.calls[0][1].method).toBe('GET')
  })

  it('configura a automação com PATCH e só os campos enviados', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ status: 'checking', enabled: true, channel_login: 'canal_novo' }))
    await createApiClient('/api', fetchMock).configureAutomation({ channel_login: 'canal_novo' })
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/automation')
    expect(init.method).toBe('PATCH')
    expect(JSON.parse(init.body)).toEqual({ channel_login: 'canal_novo' })
  })

  it('monta a consulta da galeria com review_status, limite e cursor opaco', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ items: [ITEM], next_cursor: 7 }))
    const api = createApiClient('http://127.0.0.1:8765/api/', fetchMock)
    const page = await api.gallery({ review_status: 'pending', limit: 20, cursor: 3 })
    expect(fetchMock.mock.calls[0][0]).toBe('http://127.0.0.1:8765/api/gallery?review_status=pending&limit=20&cursor=3')
    expect(page.next_cursor).toBe(7)
  })

  it('aceita galeria como lista pura e recusa formato inesperado', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse([ITEM]))
      .mockResolvedValueOnce(jsonResponse({ cortes: [] }))
    const api = createApiClient('/api', fetchMock)
    expect(await api.gallery({ review_status: 'all' })).toEqual({ items: [ITEM], next_cursor: null })
    await expect(api.gallery({ review_status: 'all' })).rejects.toMatchObject({ kind: 'invalid_response' })
  })

  it('avalia com PATCH /clips/{id} e só review_status', async () => {
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ id: 'c 1', review_status: 'approved', revision: 2 }))
    const result = await createApiClient('/api', fetchMock).reviewClip('c 1', 'approved')
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/clips/c%201')
    expect(init.method).toBe('PATCH')
    expect(JSON.parse(init.body)).toEqual({ review_status: 'approved' })
    expect(result.review_status).toBe('approved')
  })

  it('transforma detail do FastAPI em mensagem de erro com status', async () => {
    const api = createApiClient('/api', vi.fn().mockResolvedValue(jsonResponse({ detail: 'Corte não encontrado' }, 404)))
    const error = await api.reviewClip('x', 'approved').catch((e: unknown) => e)
    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({ kind: 'http', status: 404, message: 'Corte não encontrado' })
  })

  it('lê erros de validação em lista e erro sem corpo', async () => {
    const body = { detail: [{ loc: ['body', 'channel_login'], msg: 'login inválido' }] }
    const api422 = createApiClient('/api', vi.fn().mockResolvedValue(jsonResponse(body, 422)))
    await expect(api422.configureAutomation({ channel_login: 'A' })).rejects.toMatchObject({ status: 422, message: 'login inválido' })
    const api500 = createApiClient('/api', vi.fn().mockResolvedValue(new Response('', { status: 500 })))
    await expect(api500.automation()).rejects.toMatchObject({ status: 500, message: expect.stringContaining('500') })
  })

  it('trata 502/504 do proxy como backend indisponível', async () => {
    const api = createApiClient('/api', vi.fn().mockResolvedValue(new Response('', { status: 502 })))
    await expect(api.automation()).rejects.toMatchObject({ kind: 'network', status: 502 })
  })

  it('distingue falha de rede de consulta cancelada', async () => {
    const offline = createApiClient('/api', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))
    await expect(offline.health()).rejects.toMatchObject({ kind: 'network' })

    const controller = new AbortController()
    const aborting = createApiClient('/api', (_url, init) => {
      return new Promise((_resolve, reject) => {
        init?.signal?.addEventListener('abort', () => reject(new DOMException('aborted', 'AbortError')))
      })
    })
    const pending = aborting.gallery({ review_status: 'all' }, controller.signal).catch((e: unknown) => e)
    controller.abort()
    expect(isAbort(await pending)).toBe(true)
  })

  it('resolve URLs de vídeo e download', () => {
    const relative = createApiClient('/api', vi.fn())
    const absolute = createApiClient('http://127.0.0.1:8765/api', vi.fn())
    expect(relative.resolveUrl(ITEM.preview_url)).toBe('/api/clips/c1/preview?revision=1')
    expect(absolute.resolveUrl(ITEM.download_url)).toBe('http://127.0.0.1:8765/api/clips/c1/file?revision=1')
    expect(relative.resolveUrl('http://127.0.0.1:8765/api/clips/c1/file')).toBe('http://127.0.0.1:8765/api/clips/c1/file')
    expect(relative.resolveUrl(null)).toBeNull()
  })
})
