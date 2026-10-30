import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
// Fontes empacotadas localmente (OFL 1.1): o app roda offline. Só latim e os pesos usados.
import '@fontsource/ibm-plex-sans/latin-400.css'
import '@fontsource/ibm-plex-sans/latin-500.css'
import '@fontsource/ibm-plex-sans/latin-600.css'
import '@fontsource/ibm-plex-mono/latin-400.css'
import '@fontsource/ibm-plex-mono/latin-500.css'
import './index.css'
import { App } from './App'
import { createApiClient } from './api/client'
import { createMockApi, MOCK_SCENARIOS, type MockScenario } from './api/mock'

// O mock só entra quando pedido explicitamente: ?mock=1 (cenário com ?cenario=) ou VITE_API_MODE=mock.
const params = new URLSearchParams(window.location.search)
const useMock = params.get('mock') === '1' || import.meta.env.VITE_API_MODE === 'mock'
const requested = params.get('cenario') as MockScenario | null
const scenario = requested && MOCK_SCENARIOS.includes(requested) ? requested : undefined
const api = useMock ? createMockApi({ scenario }) : createApiClient()

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App api={api} />
  </StrictMode>,
)
