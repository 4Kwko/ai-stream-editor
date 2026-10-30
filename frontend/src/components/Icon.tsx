// Ícones próprios do produto: grade de 16px, traço 1,5, pontas arredondadas,
// herdando a cor do texto. Só os ícones que a interface usa.

const PATHS = {
  play: <path d="M5.5 3.5v9l7-4.5z" fill="currentColor" stroke="none" />,
  like: (
    <>
      <path d="M5 7v6.5" />
      <path d="M5 7l2.4-4.4c.95 0 1.6.75 1.38 1.66L8.4 6.5h3.4c.92 0 1.58.86 1.36 1.75l-1 4.2a1.3 1.3 0 0 1-1.27 1.05H5" />
      <path d="M2.5 7H5v6.5H2.5z" />
    </>
  ),
  download: (
    <>
      <path d="M8 2.5v8" />
      <path d="M4.5 7.5 8 11l3.5-3.5" />
      <path d="M3 13.5h10" />
    </>
  ),
  chevron: <path d="M4 6l4 4 4-4" />,
  check: <path d="M3.5 8.5l3 3 6-7" />,
  alert: (
    <>
      <circle cx="8" cy="8" r="5.75" />
      <path d="M8 5v3.5" />
      <path d="M8 11h.01" />
    </>
  ),
  refresh: (
    <>
      <path d="M13 8a5 5 0 1 1-1.46-3.54" />
      <path d="M13 2.5v3h-3" />
    </>
  ),
  sliders: (
    <>
      <path d="M2.5 5h6M11.5 5h2M2.5 11h2M7.5 11h6" />
      <circle cx="10" cy="5" r="1.5" />
      <circle cx="6" cy="11" r="1.5" />
    </>
  ),
  external: (
    <>
      <path d="M6.5 3.5h-3v9h9v-3" />
      <path d="M9.5 2.5h4v4" />
      <path d="M13.5 2.5 7.5 8.5" />
    </>
  ),
  film: (
    <>
      <rect x="3" y="1.5" width="10" height="13" rx="1.5" />
      <path d="M3 5h2M3 8h2M3 11h2M11 5h2M11 8h2M11 11h2" />
    </>
  ),
} as const

export type IconName = keyof typeof PATHS | 'dislike'

export function Icon({ name, size = 16, className }: { name: IconName; size?: number; className?: string }) {
  // "Não gostei" é o mesmo desenho girado: os dois ficam idênticos em peso e proporção.
  const flipped = name === 'dislike'
  return (
    <svg
      className={className ? `icon ${className}` : 'icon'}
      width={size}
      height={size}
      viewBox="0 0 16 16"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      focusable="false"
      style={flipped ? { transform: 'rotate(180deg)' } : undefined}
    >
      {PATHS[flipped ? 'like' : name]}
    </svg>
  )
}
