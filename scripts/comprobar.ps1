<#
.SYNOPSIS
    Comprobacion declarada de Warezone. Solo lee. Sale 0 si todo va bien.

.DESCRIPTION
    Este proyecto no tiene servidor propio: raspa wzstats.gg desde un cron de
    GitHub Actions y publica en GitHub Pages. Por eso su modo de fallo tipico
    NO se ve desde este PC: la web sigue en pie, con datos de hace dias, y
    nadie se entera. Lo que se comprueba aqui es justo eso.

    Tres pasos, de menos a mas:

      1. python -B scripts\pruebas.py     parser y validador. Sin red, 1 s.
      2. python -B scripts\validar_meta.py invariantes del JSON de esta copia.
      3. El JSON YA PUBLICADO en GitHub Pages: que el cron siga vivo
         (generated_at reciente), que no traiga warnings y que esten los
         5 modos.

    El paso 3 es el unico que mira el producto de verdad. Los otros dos miran
    esta copia local, que puede ir por detras del repo sin que nada este roto:
    por eso la ANTIGUEDAD solo se juzga sobre el JSON publicado, nunca sobre
    el de disco.

    LIMITE, escrito a proposito: si no hay internet, el paso 3 no se puede
    hacer y se dice por pantalla, pero NO se cuenta como fallo. Un aviso
    diario cada vez que el PC esta sin red gastaria la confianza en el repaso
    entero. A cambio, el job "avisar" del workflow sigue mandando correo.

.PARAMETER Detalle
    Enseña tambien la salida de los pasos que van bien.
#>
[CmdletBinding()]
param([switch]$Detalle)

$ErrorActionPreference = 'Continue'
$raiz = Split-Path -Parent $PSScriptRoot
$fallos = @()

function Paso {
    # OJO: el parametro NO puede llamarse $Args, que es variable automatica de
    # PowerShell. Si se llama asi, el splatting manda 'python -B' sin fichero y
    # el REPL se queda esperando entrada para siempre.
    param([string]$Nombre, [string]$Script)
    $salida = & python -B $Script 2>&1
    $codigo = $LASTEXITCODE
    if ($codigo -ne 0) {
        Write-Host "  FALLA  $Nombre" -ForegroundColor Red
        $salida | Select-Object -Last 12 | ForEach-Object { Write-Host "     $_" }
        return $false
    }
    Write-Host "  bien   $Nombre" -ForegroundColor Green
    if ($Detalle) { $salida | ForEach-Object { Write-Host "     $_" -ForegroundColor DarkGray } }
    return $true
}

Write-Host 'Warezone - comprobacion'

# --- 1 y 2: esta copia local, sin red -------------------------------------
if (-not (Paso 'pruebas del parser y del validador' "$raiz\scripts\pruebas.py"))      { $fallos += 'pruebas.py' }
if (-not (Paso 'invariantes del meta.json local'    "$raiz\scripts\validar_meta.py")) { $fallos += 'validar_meta.py' }

# --- 3: el JSON publicado, que es lo que consume el movil ------------------
$sonda = @'
import json, sys, urllib.error, urllib.request
from datetime import datetime, timezone

URL = "https://zeusente.github.io/warzone-armeria/data/meta.json"
DIAS_MAX = 3          # el cron es diario; 3 dias tolera un par de fallos sueltos

try:
    with urllib.request.urlopen(URL, timeout=30) as r:
        datos = json.load(r)
except urllib.error.URLError as e:          # sin red, DNS, TLS...
    print(f"no concluyente: no se pudo consultar la web publicada ({e.reason})")
    sys.exit(0)
except Exception as e:
    print(f"la web publicada contesta pero no da un JSON valido: {e}")
    sys.exit(1)

problemas = []

marca = datos.get("generated_at")
try:
    edad = (datetime.now(timezone.utc) - datetime.fromisoformat(marca)).total_seconds() / 86400
    print(f"publicado hace {edad:.1f} dias ({marca})")
    if edad > DIAS_MAX:
        problemas.append(f"el cron lleva {edad:.1f} dias sin actualizar (limite {DIAS_MAX})")
except Exception:
    problemas.append(f"generated_at ilegible: {marca!r}")

avisos = datos.get("warnings") or []
for a in avisos:
    problemas.append(f"warning en los datos publicados: {a}")

modos = datos.get("modes") or {}
if len(modos) < 5:
    problemas.append(f"solo {len(modos)} modos publicados, deberian ser 5")

for nombre, modo in modos.items():
    if modo.get("stale"):
        problemas.append(f"modo '{nombre}' sirviendo dato guardado desde {modo.get('stale_since')}")

for p in problemas:
    print(p)
sys.exit(1 if problemas else 0)
'@

$tmp = Join-Path ([System.IO.Path]::GetTempPath()) 'warezone-sonda.py'
Set-Content -LiteralPath $tmp -Value $sonda -Encoding UTF8
if (-not (Paso 'el meta.json publicado en GitHub Pages' $tmp)) { $fallos += 'web publicada' }
Remove-Item -LiteralPath $tmp -ErrorAction SilentlyContinue

if ($fallos.Count -gt 0) {
    Write-Host "Warezone: falla $($fallos -join ', ')" -ForegroundColor Red
    exit 1
}
Write-Host 'Warezone: bien' -ForegroundColor Green
exit 0
