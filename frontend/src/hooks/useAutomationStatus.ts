import { useCallback, useEffect, useRef, useState } from 'react'
import { ApiError, isAbort } from '../api/client'
import type { Api, Automation } from '../api/types'

export const STATUS_INTERVAL_MS = 10_000
const MAX_INTERVAL_MS = 60_000

export interface AutomationWatch {
  automation: Automation | null
  error: ApiError | null
  /** Consulta agora, fora do intervalo. */
  refresh: () => void
  /** Substitui o estado com a resposta de um PATCH. */
  replace: (next: Automation) => void
}

/**
 * Consulta GET /automation em intervalo fixo enquanto a aba está visível.
 * Só lê o estado: quem busca VODs e processa é o backend, com ou sem a página
 * aberta. Em erro, o intervalo dobra até 60 s. A consulta em andamento é
 * cancelada ao desmontar.
 */
export function useAutomationStatus(
  api: Api,
  intervalMs = STATUS_INTERVAL_MS,
  onUpdate?: (automation: Automation) => void,
): AutomationWatch {
  const [automation, setAutomation] = useState<Automation | null>(null)
  const [error, setError] = useState<ApiError | null>(null)
  const [tick, setTick] = useState(0)
  const delayRef = useRef(intervalMs)
  const onUpdateRef = useRef(onUpdate)
  useEffect(() => {
    onUpdateRef.current = onUpdate
  }, [onUpdate])

  const refresh = useCallback(() => setTick((n) => n + 1), [])
  const replace = useCallback((next: Automation) => {
    setAutomation(next)
    setError(null)
  }, [])

  useEffect(() => {
    const controller = new AbortController()
    let timer: ReturnType<typeof setTimeout> | undefined
    // Uma consulta por vez: voltar à aba durante uma consulta não abre um segundo ciclo.
    let inFlight = false

    function schedule() {
      timer = setTimeout(() => {
        if (document.visibilityState === 'visible') void poll()
        else schedule()
      }, delayRef.current)
    }

    async function poll() {
      if (inFlight) return
      inFlight = true
      try {
        const next = await api.automation(controller.signal)
        setAutomation(next)
        setError(null)
        onUpdateRef.current?.(next)
        delayRef.current = intervalMs
      } catch (err) {
        if (isAbort(err)) return
        setError(err instanceof ApiError ? err : new ApiError('network', 'Falha ao consultar a automação.'))
        delayRef.current = Math.min(delayRef.current * 2, MAX_INTERVAL_MS)
      } finally {
        inFlight = false
      }
      if (!controller.signal.aborted) schedule()
    }

    // Ao voltar para a aba, consulta logo em vez de esperar o intervalo.
    function onVisible() {
      if (document.visibilityState !== 'visible') return
      if (timer) clearTimeout(timer)
      void poll()
    }

    void poll()
    document.addEventListener('visibilitychange', onVisible)
    return () => {
      controller.abort()
      if (timer) clearTimeout(timer)
      document.removeEventListener('visibilitychange', onVisible)
    }
  }, [api, intervalMs, tick])

  return { automation, error, refresh, replace }
}
