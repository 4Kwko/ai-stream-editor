// Compila o lançador com o compilador C# que já vem no Windows (.NET Framework 4.x).
// Nada é instalado. Saída: frontend/launcher/dist/AI Stream Editor.exe (ignorado pelo Git).
import { execFileSync } from 'node:child_process'
import { existsSync, mkdirSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const here = dirname(fileURLToPath(import.meta.url))
const windir = process.env.WINDIR ?? 'C:\\Windows'
const csc = [
  join(windir, 'Microsoft.NET', 'Framework64', 'v4.0.30319', 'csc.exe'),
  join(windir, 'Microsoft.NET', 'Framework', 'v4.0.30319', 'csc.exe'),
].find((candidate) => existsSync(candidate))

if (!csc) {
  console.error('Compilador C# do .NET Framework 4 não encontrado em %WINDIR%\\Microsoft.NET. Nada foi instalado.')
  process.exit(1)
}

const outDir = join(here, 'dist')
mkdirSync(outDir, { recursive: true })
const output = join(outDir, 'AI Stream Editor.exe')

execFileSync(
  csc,
  ['/nologo', '/target:exe', '/optimize+', '/codepage:65001', `/out:${output}`, join(here, 'Launcher.cs')],
  { stdio: 'inherit' },
)
console.log(`Gerado: ${output}`)
