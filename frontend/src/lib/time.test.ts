import { describe, expect, it } from 'vitest'
import { formatDateTime, formatTimecode } from './time'

describe('formatTimecode', () => {
  it('formata minutos e horas', () => {
    expect(formatTimecode(0)).toBe('0:00')
    expect(formatTimecode(22)).toBe('0:22')
    expect(formatTimecode(24.2)).toBe('0:24')
    expect(formatTimecode(725)).toBe('12:05')
    expect(formatTimecode(3725)).toBe('1:02:05')
  })

  it('arredonda sem gerar 60 segundos', () => {
    expect(formatTimecode(59.6)).toBe('1:00')
  })

  it('devolve traço para valores inválidos', () => {
    expect(formatTimecode(Number.NaN)).toBe('—')
    expect(formatTimecode(-1)).toBe('—')
  })
})

describe('formatDateTime', () => {
  it('devolve traço quando ausente ou inválida', () => {
    expect(formatDateTime(null)).toBe('—')
    expect(formatDateTime('não é data')).toBe('—')
  })

  it('formata data válida em pt-BR', () => {
    expect(formatDateTime('2026-10-01T22:00:00Z')).toMatch(/\d{2}\/10\/2026/)
  })
})
