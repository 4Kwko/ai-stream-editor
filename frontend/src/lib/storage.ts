// Preferências locais do navegador (último projeto, pasta de exportação,
// versões de preview já geradas). Tudo opcional: a interface funciona sem.

const PREFIX = 'ai-stream-editor:'

export function loadValue<T>(key: string, fallback: T): T {
  try {
    const raw = window.localStorage.getItem(PREFIX + key)
    return raw === null ? fallback : (JSON.parse(raw) as T)
  } catch {
    return fallback
  }
}

export function saveValue(key: string, value: unknown): void {
  try {
    if (value === null || value === undefined) window.localStorage.removeItem(PREFIX + key)
    else window.localStorage.setItem(PREFIX + key, JSON.stringify(value))
  } catch {
    // Sem armazenamento local: segue sem lembrar.
  }
}
