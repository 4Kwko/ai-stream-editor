// MOCK — API simulada em memória, só para desenvolvimento da interface sem backend.
// Ativada com ?mock=1 (cenário com ?cenario=...) ou VITE_API_MODE=mock. A interface
// mostra a faixa "Modo demonstração". Não há vídeo: resolveUrl devolve null para as
// URLs simuladas, para que nada seja exibido como corte real. Segue o formato do
// contrato (extensão de automação e galeria); não comprova integração com o backend
// nem com a Twitch. O andamento simulado avança a cada consulta de GET /automation,
// imitando o estado que o backend persistente informaria.

import { ApiError } from './client'
import type { Api, Automation, GalleryItem, GalleryPage, ReviewStatus } from './types'

export type MockScenario = 'pronto' | 'vazio' | 'config' | 'parado' | 'processando' | 'falha' | 'muitos'

export const MOCK_SCENARIOS: readonly MockScenario[] = ['pronto', 'vazio', 'config', 'parado', 'processando', 'falha', 'muitos']

export interface MockApiOptions {
  /** Atraso artificial por chamada, em ms. */
  latencyMs?: number
  scenario?: MockScenario
}

const MOCK_URL_PREFIX = 'mock://'

const TITLES = [
  'Reação à notícia do patch',
  'História da viagem',
  'Jogada no final da partida',
  'Explicação sobre a configuração',
  'Momento engraçado com o chat',
  'Conclusão da live',
]

function makeItem(index: number, review: ReviewStatus = 'pending'): GalleryItem {
  const day = String(1 + (index % 28)).padStart(2, '0')
  // Mistura formatos: maioria 16:9 (padrão), um vertical com câmera e um vertical com aviso.
  const vertical = index % 4 === 1 || index % 4 === 3
  const layout = !vertical ? 'source_preserved' : index % 4 === 1 ? 'camera_top_content_bottom' : 'full_frame'
  return {
    output_format: vertical ? '9:16' : '16:9',
    layout,
    layout_warning:
      layout === 'full_frame' ? 'Simulação: câmera não detectada com segurança; a imagem inteira foi preservada.' : null,
    id: `clip-mock-${index + 1}`,
    project_id: `proj-mock-${Math.floor(index / 3) + 1}`,
    title: TITLES[index % TITLES.length] + (index >= TITLES.length ? ` (${index + 1})` : ''),
    reason: 'Simulação: trecho com reação e frase completa.',
    score: 0.7,
    review_status: review,
    revision: 1,
    duration_seconds: 22 + ((index * 7) % 40),
    created_at: `2026-10-${day}T22:00:00Z`,
    preview_url: `${MOCK_URL_PREFIX}preview/${index + 1}`,
    download_url: `${MOCK_URL_PREFIX}file/${index + 1}`,
    source: { type: 'twitch', vod_id: `v${index}`, channel_login: 'joaomontagner', url: null, title: `Live de ${day}/10` },
  }
}

function baseAutomation(overrides: Partial<Automation>): Automation {
  return {
    enabled: true,
    channel_login: 'joaomontagner',
    output_format: '16:9',
    gallery_updated_at: '2026-10-30T02:00:00Z',
    channel_url: 'https://www.twitch.tv/joaomontagner',
    poll_interval_seconds: 300,
    runtime_active: true,
    status: 'waiting',
    message: null,
    last_checked_at: '2026-10-30T03:00:00Z',
    next_check_at: '2026-10-30T03:05:00Z',
    active_vod: null,
    counts: { queued: 0, processing: 0, completed: 0, failed: 0, skipped: 0 },
    ...overrides,
  }
}

function clone<T>(value: T): T {
  return structuredClone(value)
}

export function createMockApi(options: MockApiOptions = {}): Api {
  const latency = options.latencyMs ?? 150
  const scenario = options.scenario ?? 'pronto'
  const wait = () => new Promise((resolve) => setTimeout(resolve, latency))

  let items: GalleryItem[] = []
  let calls = 0
  let automation: Automation

  switch (scenario) {
    case 'vazio':
      automation = baseAutomation({ status: 'waiting' })
      break
    case 'config':
      automation = baseAutomation({
        status: 'configuration_required',
        message: 'Simulação: o componente que obtém vídeos da Twitch não está instalado no backend.',
      })
      break
    case 'parado':
      automation = baseAutomation({ status: 'stopped', runtime_active: false, message: null })
      break
    case 'processando':
      automation = baseAutomation({
        status: 'analyzing',
        active_vod: { id: 'v1', title: 'Live de 28/10', stage: 'Transcrevendo', progress: null, progress_scope: 'stage' },
        counts: { queued: 0, processing: 1, completed: 0, failed: 0, skipped: 3 },
      })
      break
    case 'falha':
      items = [makeItem(0), makeItem(1, 'approved'), makeItem(2)]
      items[2].title = 'Corte cuja avaliação falha (simulação)'
      automation = baseAutomation({
        status: 'attention',
        message: 'Simulação: não foi possível obter a live de 27/10. Nova tentativa mais tarde; os cortes prontos continuam disponíveis.',
        counts: { queued: 0, processing: 0, completed: 1, failed: 1, skipped: 0 },
      })
      break
    case 'muitos':
      items = Array.from({ length: 60 }, (_, index) => makeItem(index, index % 5 === 0 ? 'approved' : 'pending'))
      automation = baseAutomation({ counts: { queued: 0, processing: 0, completed: 20, failed: 0, skipped: 0 } })
      break
    default:
      items = [makeItem(0), makeItem(1), makeItem(2, 'approved'), makeItem(3, 'rejected'), makeItem(4)]
      automation = baseAutomation({ counts: { queued: 0, processing: 0, completed: 2, failed: 0, skipped: 5 } })
  }

  // Cenário "processando": cada consulta avança o backend simulado.
  function advance() {
    calls += 1
    if (scenario !== 'processando') return
    if (calls === 2) automation.active_vod = { ...automation.active_vod!, stage: 'Procurando momentos', progress: 0.4 }
    if (calls === 3) {
      automation.status = 'rendering'
      automation.active_vod = { ...automation.active_vod!, stage: 'Gerando cortes verticais', progress: 0.5 }
    }
    if (calls >= 4 && items.length === 0) {
      items = [makeItem(0), makeItem(1)]
      automation.status = 'waiting'
      automation.active_vod = null
      automation.counts = { queued: 0, processing: 0, completed: 1, failed: 0, skipped: 3 }
      automation.gallery_updated_at = '2026-10-30T03:10:00Z'
    }
  }

  return {
    mode: 'mock',
    async health() {
      await wait()
      return { status: 'ok' }
    },
    async automation() {
      await wait()
      advance()
      return clone(automation)
    },
    async configureAutomation(patch) {
      await wait()
      if (patch.channel_login !== undefined && !/^[a-z0-9_]{3,25}$/.test(patch.channel_login)) {
        throw new ApiError('http', 'Login do canal inválido.', 422)
      }
      if (patch.channel_login !== undefined && automation.active_vod) {
        throw new ApiError('http', 'Há um vídeo em processamento; troque o canal quando ele terminar.', 409)
      }
      if (patch.output_format !== undefined) automation.output_format = patch.output_format
      if (patch.enabled !== undefined) {
        automation.enabled = patch.enabled
        automation.status = patch.enabled ? 'checking' : 'disabled'
      }
      if (patch.channel_login !== undefined) {
        automation.channel_login = patch.channel_login
        automation.channel_url = `https://www.twitch.tv/${patch.channel_login}`
        automation.status = automation.enabled ? 'checking' : 'disabled'
      }
      return clone(automation)
    },
    async gallery(query): Promise<GalleryPage> {
      await wait()
      const filtered = items.filter((item) => query.review_status === 'all' || item.review_status === query.review_status)
      const limit = query.limit ?? 20
      const start = query.cursor ?? 0
      const page = filtered.slice(start, start + limit)
      return { items: page.map(clone), next_cursor: start + limit < filtered.length ? start + limit : null }
    },
    async reviewClip(clipId, status) {
      await wait()
      const item = items.find((candidate) => candidate.id === clipId)
      if (!item) throw new ApiError('http', 'Corte não encontrado.', 404)
      if (/falha/i.test(item.title)) throw new ApiError('http', 'Simulação: não foi possível gravar a avaliação.', 500)
      item.review_status = status
      return { id: item.id, review_status: status, revision: item.revision }
    },
    resolveUrl: (url) => (!url || url.startsWith(MOCK_URL_PREFIX) ? null : url),
  }
}
