<#
.SYNOPSIS
    Levanta el servidor local para ver la web ANTES de publicarla.

.DESCRIPTION
    Esto NO es la forma de mirar el panel: para eso esta la web publicada
    (https://zeusente.github.io/warzone-armeria/), que no necesita nada
    instalado. Esto es para ver un cambio antes de subirlo.

    Abrir docs\index.html con doble clic no vale: en file:// el navegador
    bloquea el fetch del JSON y la pagina sale en blanco. Hay que servirla.

    La logica vive aqui y no dentro del acceso directo a proposito: asi esta
    versionada, se puede arreglar, y el .lnk es solo un lanzador.

.PARAMETER Puerto
    Por defecto 8765.

.PARAMETER NoAbrir
    No abre el navegador solo.
#>
[CmdletBinding()]
param(
    [int]$Puerto = 8765,
    [switch]$NoAbrir
)

$docs = Join-Path (Split-Path -Parent $PSScriptRoot) 'docs'
if (-not (Test-Path $docs)) { Write-Host "No encuentro $docs" -ForegroundColor Red; exit 1 }

# OJO: no basta con que "python" exista. En un Windows sin Python el PATH trae
# igualmente %LOCALAPPDATA%\Microsoft\WindowsApps\python.exe, un fichero de CERO
# BYTES que solo abre la Microsoft Store. Si se lanza tal cual, la ventana
# escribe su mensaje y muere en la linea siguiente con un error que no explica
# nada. Paso el 2026-09-10 en DESPACHO_GAMER: mejor decirlo a la cara.
function Buscar-Python {
    $c = (Get-Command python -ErrorAction SilentlyContinue).Source
    if ($c -and (Get-Item $c -ErrorAction SilentlyContinue).Length -gt 0) { return $c }
    # Puede estar instalado y no haberse recargado el PATH de esta sesion.
    foreach ($p in @(
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe"
    )) { if (Test-Path $p) { return $p } }
    return $null
}

$python = Buscar-Python
if (-not $python) {
    Write-Host ''
    Write-Host '  No hay Python en esta maquina.' -ForegroundColor Red
    Write-Host ''
    Write-Host '  Esto solo hace falta para PROBAR cambios antes de publicarlos.'
    Write-Host '  Para ver el panel normal no necesitas nada: abre'
    Write-Host '    https://zeusente.github.io/warzone-armeria/' -ForegroundColor Cyan
    Write-Host ''
    Write-Host '  Si quieres el servidor de pruebas aqui:'
    Write-Host '    winget install --id Python.Python.3.12 --scope user' -ForegroundColor DarkGray
    Write-Host '  y despues abre una ventana NUEVA (el PATH no se recarga sola).'
    Write-Host ''
    Read-Host 'Pulsa Intro para cerrar'
    exit 1
}

Set-Location $docs

if (-not $NoAbrir) {
    Start-Job { Start-Sleep -Seconds 2; Start-Process "http://localhost:$using:Puerto/" } | Out-Null
}

Write-Host ''
Write-Host "  Warezone - SERVIDOR DE PRUEBAS" -ForegroundColor Cyan
Write-Host "  http://localhost:$Puerto/" -ForegroundColor Cyan
Write-Host ''
Write-Host "  Sirve docs\ de tu copia local, con los cambios que tengas sin publicar."
Write-Host "  El panel de verdad es https://zeusente.github.io/warzone-armeria/" -ForegroundColor DarkGray
Write-Host ''
Write-Host "  Cierra esta ventana para parar el servidor." -ForegroundColor DarkYellow
Write-Host ''
Write-Host "  Python: $python" -ForegroundColor DarkGray
Write-Host ''

& $python -m http.server $Puerto
