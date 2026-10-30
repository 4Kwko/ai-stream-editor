import { useLayoutEffect, useRef, type KeyboardEvent } from 'react'

export interface SegmentOption<T extends string> {
  value: T
  label: string
}

interface Props<T extends string> {
  label: string
  value: T
  options: readonly SegmentOption<T>[]
  onChange: (value: T) => void
}

/**
 * Controle segmentado com indicador deslizante.
 * Semântica do padrão Radio Group (WAI-ARIA APG): um único item na ordem de
 * tabulação, setas movem e selecionam, Home/End vão às pontas.
 * O indicador é um elemento só, movido com transform: a seleção "viaja"
 * entre as opções em vez de piscar (ideia do Animated Background do Motion
 * Primitives, refeita em CSS sem dependência).
 */
export function SegmentedControl<T extends string>({ label, value, options, onChange }: Props<T>) {
  const rootRef = useRef<HTMLDivElement>(null)
  const indicatorRef = useRef<HTMLSpanElement>(null)

  // Posiciona o indicador direto no DOM: não é estado de React, é geometria.
  useLayoutEffect(() => {
    const root = rootRef.current
    const indicator = indicatorRef.current
    if (!root || !indicator) return
    function place() {
      const selected = root!.querySelector<HTMLElement>('[aria-checked="true"]')
      if (!selected) return
      indicator!.style.width = `${selected.offsetWidth}px`
      indicator!.style.transform = `translateX(${selected.offsetLeft}px)`
    }
    place()
    // Primeira posição sem transição: o indicador não "desliza" ao abrir a página com um filtro lembrado.
    const frame = requestAnimationFrame(() => indicator.setAttribute('data-ready', ''))
    const observer = typeof ResizeObserver === 'undefined' ? null : new ResizeObserver(place)
    observer?.observe(root)
    return () => {
      cancelAnimationFrame(frame)
      observer?.disconnect()
    }
  }, [value, options])

  function handleKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    const index = options.findIndex((option) => option.value === value)
    let next = index
    if (event.key === 'ArrowRight' || event.key === 'ArrowDown') next = (index + 1) % options.length
    else if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') next = (index - 1 + options.length) % options.length
    else if (event.key === 'Home') next = 0
    else if (event.key === 'End') next = options.length - 1
    else return
    event.preventDefault()
    onChange(options[next].value)
    rootRef.current?.querySelectorAll<HTMLButtonElement>('[role="radio"]')[next]?.focus()
  }

  return (
    <div ref={rootRef} className="segmented" role="radiogroup" aria-label={label} onKeyDown={handleKeyDown}>
      <span ref={indicatorRef} className="segmented__indicator" aria-hidden="true" />
      {options.map((option) => {
        const checked = option.value === value
        return (
          <button
            key={option.value}
            type="button"
            role="radio"
            aria-checked={checked}
            tabIndex={checked ? 0 : -1}
            className="segmented__option"
            onClick={() => onChange(option.value)}
          >
            {option.label}
          </button>
        )
      })}
    </div>
  )
}
