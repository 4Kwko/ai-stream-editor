import { cleanup, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { App } from './App'
import { ApiError } from './api/client'
import { createMockApi, type MockScenario } from './api/mock'
import type { Api } from './api/types'

// Galeria sobre o mock (dados sintéticos, sem vídeo real nem Twitch).
type User = ReturnType<typeof userEvent.setup>

function mock(scenario: MockScenario = 'pronto', latencyMs = 0) {
  return createMockApi({ scenario, latencyMs })
}

function setup(api: Api = mock(), statusIntervalMs = 10_000) {
  const user = userEvent.setup()
  const view = render(<App api={api} statusIntervalMs={statusIntervalMs} />)
  return { user, api, view }
}

/** Registra as chamadas a cada método da API sem mudar o comportamento. */
function spyAll(api: Api) {
  const calls: string[] = []
  for (const key of ['health', 'automation', 'configureAutomation', 'gallery', 'reviewClip'] as const) {
    const original = api[key] as (...args: unknown[]) => unknown
    ;(api as unknown as Record<string, unknown>)[key] = (...args: unknown[]) => {
      calls.push(key)
      return original(...args)
    }
  }
  return calls
}

async function cards() {
  return within(await screen.findByRole('list')).findAllByRole('article')
}

function card(title: string) {
  return screen.getByRole('article', { name: title })
}

function likeButton(title: string) {
  return within(card(title)).getByRole('button', { name: 'Gostei' })
}

async function showFilter(user: User, label: string) {
  await user.click(within(screen.getByRole('radiogroup', { name: 'Filtrar cortes' })).getByRole('radio', { name: label }))
}

beforeEach(() => window.localStorage.clear())
afterEach(() => cleanup())

describe('Galeria: estados da automação', () => {
  it('canal sem VOD aparece como espera, não como falha', async () => {
    setup(mock('vazio'))
    expect(await screen.findByText('Aguardando uma gravação disponível neste canal.')).toBeInTheDocument()
    expect(await screen.findByText('Nada para avaliar agora. Aguardando uma gravação disponível neste canal.')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'joaomontagner' })).toHaveAttribute('href', 'https://www.twitch.tv/joaomontagner')
    expect(screen.queryByRole('alert')).not.toBeInTheDocument()
    expect(screen.queryByText(/falh/i)).not.toBeInTheDocument()
    expect(screen.getByText(/enquanto o AI Stream Editor estiver em execução/)).toBeInTheDocument()
  })

  it('configuração necessária é distinta de canal vazio e não pede segredos', async () => {
    setup(mock('config'))
    expect(await screen.findByText('Configuração necessária')).toBeInTheDocument()
    expect(screen.getByText(/não está instalado no backend/)).toBeInTheDocument()
    expect(screen.queryByText('Aguardando uma gravação disponível neste canal.')).not.toBeInTheDocument()
    expect(document.querySelector('input[type="password"]')).toBeNull()
    expect(screen.queryAllByRole('textbox').map((input) => input.getAttribute('id'))).toHaveLength(1)
    expect(screen.getByLabelText('Canal da Twitch (login)')).toBeInTheDocument()
  })

  it('serviço parado diz que a busca depende do app em execução', async () => {
    setup(mock('parado'))
    expect(await screen.findByText(/Busca automática parada: o serviço de automação não está em execução/)).toBeInTheDocument()
    expect(screen.queryByText(/Próxima:/)).not.toBeInTheDocument()
  })

  it('mostra o processamento por etapa e recebe os cortes quando ficam prontos', async () => {
    setup(mock('processando'), 20)
    expect(await screen.findByText('Transcrevendo e analisando · Live de 28/10')).toBeInTheDocument()
    expect(screen.getByText('Etapa: Transcrevendo · sem estimativa para esta etapa')).toBeInTheDocument()
    expect(await screen.findByText(/Os cortes aparecem aqui assim que o processamento terminar/)).toBeInTheDocument()
    expect(screen.queryByText(/restante/i)).not.toBeInTheDocument()
    expect(await screen.findAllByRole('article', {}, { timeout: 3000 })).toHaveLength(2)
    expect(await screen.findByText('Em dia. Aguardando a próxima gravação disponível neste canal.')).toBeInTheDocument()
  })

  it('falha parcial avisa sem impedir assistir aos cortes prontos', async () => {
    const { user } = setup(mock('falha'))
    expect(await screen.findByText(/não foi possível obter a live de 27\/10/)).toBeInTheDocument()
    expect(screen.getByText('Precisa de atenção')).toBeInTheDocument()
    await cards()
    await user.click(screen.getByRole('button', { name: 'Assistir Reação à notícia do patch' }))
    expect(within(card('Reação à notícia do patch')).getByText(/Modo demonstração: não há vídeo real/)).toBeInTheDocument()
  })

  it('backend indisponível mostra aviso e erro da galeria com nova tentativa', async () => {
    const api = mock()
    api.automation = async () => {
      throw new ApiError('network', 'Não foi possível falar com o backend local.')
    }
    let galleryUp = false
    const original = api.gallery
    api.gallery = async (query, signal) => {
      if (!galleryUp) throw new ApiError('network', 'Não foi possível falar com o backend local.')
      return original(query, signal)
    }
    const { user } = setup(api)
    expect(await screen.findByText(/Backend local indisponível/)).toBeInTheDocument()
    expect(await screen.findByText('Não foi possível falar com o backend local.')).toBeInTheDocument()
    galleryUp = true
    await user.click(screen.getByRole('button', { name: 'Tentar de novo' }))
    expect(await cards()).toHaveLength(3)
  })

  it('backend sem a rota de automação explica em vez de inventar estado', async () => {
    const api = mock()
    api.automation = async () => {
      throw new ApiError('http', 'Not Found', 404)
    }
    setup(api)
    expect(await screen.findByText('O backend em execução ainda não oferece a busca automática.')).toBeInTheDocument()
  })

  it('configura o canal com validação e mostra a recusa do backend', async () => {
    const api = mock('vazio')
    const calls = spyAll(api)
    const { user } = setup(api)
    await screen.findByText('Aguardando uma gravação disponível neste canal.')
    await user.click(screen.getByText('Configurar canal'))
    const input = screen.getByLabelText('Canal da Twitch (login)')

    await user.clear(input)
    await user.type(input, 'Nome Inválido!')
    await user.click(screen.getByRole('button', { name: 'Salvar' }))
    expect(screen.getByText(/Use o login do canal/)).toBeInTheDocument()
    expect(calls).not.toContain('configureAutomation')

    await user.clear(input)
    await user.type(input, 'https://www.twitch.tv/outro_canal')
    await user.click(screen.getByRole('button', { name: 'Salvar' }))
    expect(await screen.findByText('Configuração salva.')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'outro_canal' })).toBeInTheDocument()
    expect(screen.getByText('Procurando gravações novas no canal')).toBeInTheDocument()
  })

  it('trocar o canal durante um processamento mostra o 409 do backend', async () => {
    const { user } = setup(mock('processando'))
    await screen.findByText(/Transcrevendo e analisando/)
    await user.click(screen.getByText('Configurar canal'))
    const input = screen.getByLabelText('Canal da Twitch (login)')
    await user.clear(input)
    await user.type(input, 'outro_canal')
    await user.click(screen.getByRole('button', { name: 'Salvar' }))
    expect(await screen.findByText(/Há um vídeo em processamento/)).toBeInTheDocument()
  })
})

describe('Galeria: cortes e avaliação', () => {
  it('abre em "Para avaliar" com cortes prontos e sem controles de edição', async () => {
    setup()
    expect(await cards()).toHaveLength(3)
    expect(screen.getByRole('radio', { name: 'Para avaliar' })).toHaveAttribute('aria-checked', 'true')
    for (const name of [/Aprovar/, /Exportar/, /Gerar preview/, /Salvar ajustes/, /Analisar/, /Renderizar/]) {
      expect(screen.queryByRole('button', { name })).not.toBeInTheDocument()
    }
    expect(screen.queryByLabelText('Início')).not.toBeInTheDocument()
    expect(screen.queryByLabelText('Fim')).not.toBeInTheDocument()
    expect(document.querySelector('textarea')).toBeNull()
    expect(document.querySelector('video')).toBeNull()
  })

  it('cada card mostra duração, origem, data e estado', async () => {
    setup()
    await cards()
    const first = card('Reação à notícia do patch')
    expect(within(first).getByText('0:22')).toBeInTheDocument()
    expect(within(first).getByText('Live de 01/10')).toBeInTheDocument()
    expect(within(first).getByText(/01\/10\/2026/)).toBeInTheDocument()
    expect(within(first).getByText('Para avaliar')).toBeInTheDocument()
  })

  it('monta só um player por vez', async () => {
    const { user } = setup()
    await cards()
    await user.click(screen.getByRole('button', { name: 'Assistir Reação à notícia do patch' }))
    await user.click(screen.getByRole('button', { name: 'Assistir História da viagem' }))
    expect(screen.getAllByText(/Modo demonstração: não há vídeo real/)).toHaveLength(1)
    expect(screen.getByRole('button', { name: 'Assistir Reação à notícia do patch' })).toBeInTheDocument()
  })

  it('com backend real, o player só monta após o clique e o download usa a URL do contrato', async () => {
    const api = mock()
    api.resolveUrl = (url) => (url ? url.replace('mock://', 'http://127.0.0.1:8765/api/') : null)
    const { user } = setup(api)
    await cards()
    expect(document.querySelector('video')).toBeNull()
    const target = card('Reação à notícia do patch')
    expect(within(target).getByRole('link', { name: 'Baixar MP4' })).toHaveAttribute('href', 'http://127.0.0.1:8765/api/file/1')
    await user.click(within(target).getByRole('button', { name: /Assistir/ }))
    const video = target.querySelector('video')
    expect(video).not.toBeNull()
    expect(video).toHaveAttribute('src', 'http://127.0.0.1:8765/api/preview/1')
    expect(document.querySelectorAll('video')).toHaveLength(1)
  })

  it('Gostei confirma, troca para Não gostei e só chama a rota de avaliação', async () => {
    const api = mock()
    const calls = spyAll(api)
    const { user } = setup(api)
    await cards()
    const before = calls.length
    const target = card('Reação à notícia do patch')

    await user.click(likeButton('Reação à notícia do patch'))
    expect(await within(target).findByText('Salvo: Gostei')).toBeInTheDocument()
    expect(likeButton('Reação à notícia do patch')).toHaveAttribute('aria-pressed', 'true')
    expect(within(target).getAllByText('Gostei').length).toBeGreaterThan(0)

    await user.click(within(target).getByRole('button', { name: 'Não gostei' }))
    expect(await within(target).findByText('Salvo: Não gostei')).toBeInTheDocument()
    expect(within(target).getByRole('button', { name: 'Não gostei' })).toHaveAttribute('aria-pressed', 'true')
    expect(likeButton('Reação à notícia do patch')).toHaveAttribute('aria-pressed', 'false')

    expect(calls.slice(before)).toEqual(['reviewClip', 'reviewClip'])
  })

  it('cliques repetidos não duplicam a gravação', async () => {
    const api = mock('pronto', 60)
    const calls = spyAll(api)
    const { user } = setup(api)
    await cards()
    const target = card('Reação à notícia do patch')
    await user.click(likeButton('Reação à notícia do patch'))
    expect(within(target).getByText('Salvando…')).toBeInTheDocument()
    expect(likeButton('Reação à notícia do patch')).toBeDisabled()
    await user.click(likeButton('Reação à notícia do patch'))
    await within(target).findByText('Salvo: Gostei')
    expect(calls.filter((call) => call === 'reviewClip')).toHaveLength(1)
  })

  it('falha ao salvar não finge que a escolha ficou registrada', async () => {
    const { user } = setup(mock('falha'))
    await cards()
    const title = 'Corte cuja avaliação falha (simulação)'
    await user.click(likeButton(title))
    expect(await within(card(title)).findByText(/Não foi possível salvar/)).toBeInTheDocument()
    expect(within(card(title)).getByText(/O corte continua sem avaliação/)).toBeInTheDocument()
    expect(likeButton(title)).toHaveAttribute('aria-pressed', 'false')
    expect(within(card(title)).getByText('Para avaliar')).toBeInTheDocument()
    expect(within(card(title)).queryByText(/Salvo:/)).not.toBeInTheDocument()
  })

  it('filtra por estado', async () => {
    const { user } = setup()
    expect(await cards()).toHaveLength(3)
    await showFilter(user, 'Gostei')
    await waitFor(() => expect(screen.getByRole('article')).toHaveAccessibleName('Jogada no final da partida'))
    await showFilter(user, 'Não gostei')
    await waitFor(() => expect(screen.getByRole('article')).toHaveAccessibleName('Explicação sobre a configuração'))
    await showFilter(user, 'Todos')
    await waitFor(async () => expect(await cards()).toHaveLength(5))
  })

  it('filtro vazio explica o motivo', async () => {
    const { user } = setup(mock('falha'))
    await cards()
    await showFilter(user, 'Não gostei')
    expect(await screen.findByText('Nenhum corte marcado como Não gostei.')).toBeInTheDocument()
  })

  it('recarregar preserva escolhas e o filtro selecionado', async () => {
    const api = mock()
    const first = setup(api)
    await cards()
    await first.user.click(likeButton('Reação à notícia do patch'))
    await within(card('Reação à notícia do patch')).findByText('Salvo: Gostei')
    await showFilter(first.user, 'Gostei')
    await waitFor(async () => expect(await cards()).toHaveLength(2))
    first.view.unmount()

    setup(api)
    expect(await cards()).toHaveLength(2)
    expect(within(screen.getByRole('radiogroup', { name: 'Filtrar cortes' })).getByRole('radio', { name: 'Gostei' })).toHaveAttribute(
      'aria-checked',
      'true',
    )
    expect(likeButton('Reação à notícia do patch')).toHaveAttribute('aria-pressed', 'true')
  })

  it('carrega por páginas com "Carregar mais", repassando o cursor', async () => {
    const { user } = setup(mock('muitos'))
    await cards()
    await showFilter(user, 'Todos')
    await waitFor(async () => expect(await cards()).toHaveLength(20))
    expect(screen.getByText('20 cortes carregados; há mais')).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Carregar mais' }))
    await waitFor(async () => expect(await cards()).toHaveLength(40))
    await user.click(screen.getByRole('button', { name: 'Carregar mais' }))
    await waitFor(async () => expect(await cards()).toHaveLength(60))
    expect(screen.queryByRole('button', { name: 'Carregar mais' })).not.toBeInTheDocument()
    expect(screen.getByText('60 cortes')).toBeInTheDocument()
  })

  it('render novo (gallery_updated_at) com a lista cheia gera aviso, sem reordenar', async () => {
    const api = mock()
    const calls = spyAll(api)
    let extra = 0
    const original = api.automation
    api.automation = async (signal) => {
      const state = await original(signal)
      return { ...state, gallery_updated_at: extra ? '2026-10-30T09:00:00Z' : state.gallery_updated_at }
    }
    const { user } = setup(api, 20)
    expect(await cards()).toHaveLength(3)
    await waitFor(() => expect(calls.filter((call) => call === 'automation').length).toBeGreaterThan(1))
    extra = 1
    expect(await screen.findByText('Há cortes novos prontos.')).toBeInTheDocument()
    expect(await cards()).toHaveLength(3)
    const galleryCalls = calls.filter((call) => call === 'gallery').length
    await user.click(screen.getByRole('button', { name: 'Mostrar' }))
    await waitFor(() => expect(calls.filter((call) => call === 'gallery').length).toBe(galleryCalls + 1))
    expect(screen.queryByText('Há cortes novos prontos.')).not.toBeInTheDocument()
  })

  it('sem gallery_updated_at (backend antigo), usa o aumento de VODs concluídos', async () => {
    const api = mock()
    let extra = 0
    const original = api.automation
    api.automation = async (signal) => {
      const { gallery_updated_at: _ignored, ...state } = await original(signal)
      return { ...state, counts: { ...state.counts!, completed: state.counts!.completed + extra } }
    }
    setup(api, 20)
    expect(await cards()).toHaveLength(3)
    await new Promise((resolve) => setTimeout(resolve, 60))
    extra = 1
    expect(await screen.findByText('Há cortes novos prontos.')).toBeInTheDocument()
  })

  it('cada card segue o formato do corte e mostra o aviso de enquadramento', async () => {
    const { user } = setup()
    await cards()
    await showFilter(user, 'Todos')
    await waitFor(async () => expect(await cards()).toHaveLength(5))
    const horizontal = card('Reação à notícia do patch')
    expect(horizontal.querySelector('.clip__frame')).toHaveAttribute('data-format', '16:9')
    expect(within(horizontal).getByText('16:9')).toBeInTheDocument()
    const camera = card('História da viagem')
    expect(camera.querySelector('.clip__frame')).toHaveAttribute('data-format', '9:16')
    expect(within(camera).getByText('Câmera em cima')).toBeInTheDocument()
    const warned = card('Explicação sobre a configuração')
    expect(within(warned).getByText(/câmera não detectada com segurança/)).toBeInTheDocument()
  })

  it('corte antigo sem formato é tratado como 9:16', async () => {
    const api = mock()
    const original = api.gallery
    api.gallery = async (query, signal) => {
      const page = await original(query, signal)
      return {
        ...page,
        items: page.items.map(({ output_format: _f, layout: _l, layout_warning: _w, ...item }) => item),
      }
    }
    setup(api)
    await cards()
    expect(card('Reação à notícia do patch').querySelector('.clip__frame')).toHaveAttribute('data-format', '9:16')
  })

  it('a configuração troca o formato dos próximos cortes sem tocar nos prontos', async () => {
    const api = mock()
    const calls: unknown[] = []
    const original = api.configureAutomation
    api.configureAutomation = (patch) => {
      calls.push(patch)
      return original(patch)
    }
    const { user } = setup(api)
    await cards()
    await user.click(screen.getByRole('button', { name: /Configurar canal/ }))
    const formats = screen.getByRole('radiogroup', { name: 'Formato dos próximos cortes' })
    expect(within(formats).getByRole('radio', { name: '16:9 horizontal' })).toHaveAttribute('aria-checked', 'true')
    await user.click(within(formats).getByRole('radio', { name: '9:16 vertical' }))
    await user.click(screen.getByRole('button', { name: 'Salvar' }))
    expect(await screen.findByText('Configuração salva.')).toBeInTheDocument()
    expect(calls).toEqual([{ output_format: '9:16' }])
    expect(card('Reação à notícia do patch').querySelector('.clip__frame')).toHaveAttribute('data-format', '16:9')
  })

  it('funciona pelo teclado: filtros e avaliação', async () => {
    const { user } = setup()
    await cards()
    within(screen.getByRole('radiogroup', { name: 'Filtrar cortes' })).getByRole('radio', { name: 'Todos' }).focus()
    await user.keyboard('{Enter}')
    await waitFor(async () => expect(await cards()).toHaveLength(5))
    likeButton('Reação à notícia do patch').focus()
    await user.keyboard(' ')
    expect(await within(card('Reação à notícia do patch')).findByText('Salvo: Gostei')).toBeInTheDocument()
  })

  it('filtros seguem o padrão radio: setas mudam a seleção e só um item é tabulável', async () => {
    const { user } = setup()
    await cards()
    const pending = screen.getByRole('radio', { name: 'Para avaliar' })
    expect(pending).toHaveAttribute('tabindex', '0')
    expect(screen.getByRole('radio', { name: 'Gostei' })).toHaveAttribute('tabindex', '-1')
    pending.focus()
    await user.keyboard('{ArrowRight}')
    const liked = screen.getByRole('radio', { name: 'Gostei' })
    expect(liked).toHaveAttribute('aria-checked', 'true')
    expect(liked).toHaveFocus()
    await waitFor(() => expect(screen.getByRole('article')).toHaveAccessibleName('Jogada no final da partida'))
    await user.keyboard('{End}')
    expect(screen.getByRole('radio', { name: 'Todos' })).toHaveAttribute('aria-checked', 'true')
  })

  it('setas percorrem os cards e G avalia e avança para o próximo em "Para avaliar"', async () => {
    const api = mock()
    const calls = spyAll(api)
    const { user } = setup(api)
    await cards()
    const firstPlay = screen.getByRole('button', { name: 'Assistir Reação à notícia do patch' })
    firstPlay.focus()
    await user.keyboard('{ArrowRight}')
    expect(screen.getByRole('button', { name: 'Assistir História da viagem' })).toHaveFocus()
    await user.keyboard('{ArrowLeft}')
    expect(firstPlay).toHaveFocus()

    await user.keyboard('g')
    expect(await within(card('Reação à notícia do patch')).findByText('Salvo: Gostei')).toBeInTheDocument()
    await waitFor(() => expect(screen.getByRole('button', { name: 'Assistir História da viagem' })).toHaveFocus())
    await user.keyboard('n')
    expect(await within(card('História da viagem')).findByText('Salvo: Não gostei')).toBeInTheDocument()
    expect(calls.filter((call) => call === 'reviewClip')).toHaveLength(2)
  })

  it('atalhos não disparam dentro de campos de texto', async () => {
    const api = mock('vazio')
    const calls = spyAll(api)
    const { user } = setup(api)
    await screen.findByText('Aguardando uma gravação disponível neste canal.')
    await user.click(screen.getByRole('button', { name: /Configurar canal/ }))
    await user.type(screen.getByLabelText('Canal da Twitch (login)'), 'gn')
    expect(calls).not.toContain('reviewClip')
  })
})
