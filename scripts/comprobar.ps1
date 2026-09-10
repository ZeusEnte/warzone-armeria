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

    DOS LIMITES, los dos escritos a proposito y ninguno cuenta como fallo:

      - Sin internet, el paso 3 no se puede hacer. Un aviso diario cada vez
        que el PC esta sin red gastaria la confianza en el repaso entero. A
        cambio, el job "avisar" del workflow sigue mandando correo.

      - Sin Python, los pasos 1 y 2 no se pueden hacer. Esta casa tiene dos
        Windows y solo uno lo tiene: en Worker esta Python 3.12, en
        DESPACHO_GAMER no hay ninguno (lo que responde a "python" es el
        señuelo de 0 bytes de la Microsoft Store). Hasta el 2026-09-10 los
        tres pasos llamaban a python y en Gamer salian los tres en ROJO con
        el proyecto perfectamente sano: una falsa alarma diaria, que es peor
        que no avisar. Los pasos 1 y 2 se omiten diciendolo, y el paso 3
        -el que de verdad importa- se hace ahora con PowerShell, asi que se
        comprueba igual en las dos maquinas.

.PARAMETER Detalle
    Enseña tambien la salida de los pasos que van bien.
#>
[CmdletBinding()]
param([switch]$Detalle)

$ErrorActionPreference = 'Continue'
$raiz = Split-Path -Parent $PSScriptRoot
$fallos = @()
$omitidos = @()

function Hay-Python {
    # NO basta con Get-Command python: en un Windows sin Python, el PATH trae
    # igualmente %LOCALAPPDATA%\Microsoft\WindowsApps\python.exe, un fichero de
    # CERO BYTES que solo abre la Microsoft Store. Get-Command lo encuentra y
    # dice que si. Hay que ejecutarlo y ver si contesta una version.
    $ruta = (Get-Command python -ErrorAction SilentlyContinue).Source
    if (-not $ruta) { return $false }
    if ((Get-Item $ruta -ErrorAction SilentlyContinue).Length -eq 0) { return $false }
    $v = & python --version 2>&1
    return ($LASTEXITCODE -eq 0 -and "$v" -match 'Python \d')
}

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
if (Hay-Python) {
    if (-not (Paso 'pruebas del parser y del validador' "$raiz\scripts\pruebas.py"))      { $fallos += 'pruebas.py' }
    if (-not (Paso 'invariantes del meta.json local'    "$raiz\scripts\validar_meta.py")) { $fallos += 'validar_meta.py' }
} else {
    Write-Host '  omitido  pruebas del parser y del validador' -ForegroundColor DarkYellow
    Write-Host '  omitido  invariantes del meta.json local'    -ForegroundColor DarkYellow
    Write-Host '           no hay Python en esta maquina; se comprueban desde Worker' -ForegroundColor DarkGray
    $omitidos += 'los dos pasos locales (sin Python aqui)'
}

# --- 3: el JSON publicado, que es lo que consume el movil ------------------
# En PowerShell y no en Python a proposito: es el unico paso que mira el
# producto de verdad, y tiene que poder correr tambien en la maquina que no
# tiene Python. Antes era una sonda de Python en un heredoc + un fichero
# temporal; esto hace lo mismo con una pieza menos.

$URL      = 'https://zeusente.github.io/warzone-armeria/data/meta.json'
$DIAS_MAX = 3     # el cron es diario; 3 dias tolera un par de fallos sueltos

$problemas = @()
$datos = $null
try {
    $datos = Invoke-RestMethod -Uri $URL -TimeoutSec 30
} catch {
    # Sin red, DNS, TLS: no concluyente, y NO cuenta como fallo (ver .DESCRIPTION)
    Write-Host '  omitido  el meta.json publicado en GitHub Pages' -ForegroundColor DarkYellow
    Write-Host "           no se pudo consultar: $($_.Exception.Message)" -ForegroundColor DarkGray
    $omitidos += 'la web publicada (sin conexion)'
}

if ($datos) {
    $marca = $datos.generated_at
    try {
        # OJO, esto tiene trampa y costo una prueba descubrirlo. ConvertFrom-Json
        # NO deja "generated_at" como texto: reconoce el ISO-8601 y lo convierte
        # a [datetime]. Si luego se llama a [datetimeoffset]::Parse($marca), el
        # DateTime se vuelve a texto con la cultura de la maquina (es-ES,
        # dd/MM/yyyy) y se re-parsea con la invariante (MM/dd/yyyy): "02/09" se
        # lee como 9 de febrero en vez de 2 de septiembre. El 2026-09-10 un JSON
        # de hace 8 dias daba "213 dias" por eso, y no se veia a simple vista
        # porque la fecha de ese dia, 09/09, es simetrica. Peor que la falsa
        # alarma es el caso contrario: una fecha vieja leida como reciente y el
        # cron parado sin que nadie avise.
        $fecha = if ($marca -is [datetime]) {
            [datetimeoffset]::new($marca)          # ya viene con su Kind: no lo toques
        } else {
            [datetimeoffset]::Parse(
                $marca,
                [cultureinfo]::InvariantCulture,
                [System.Globalization.DateTimeStyles]::RoundtripKind)
        }
        $edad = ([datetimeoffset]::UtcNow - $fecha).TotalDays
        if ($edad -gt $DIAS_MAX) {
            $problemas += "el cron lleva {0:N1} dias sin actualizar (limite $DIAS_MAX)" -f $edad
        }
    } catch {
        $problemas += "generated_at ilegible: '$marca'"
    }

    foreach ($a in @($datos.warnings)) {
        if ($a) { $problemas += "warning en los datos publicados: $a" }
    }

    # OJO: .Count sobre PSObject.Properties enumera los miembros de cada
    # elemento en vez de contarlos. Hay que envolverlo en @(...).
    $modos = @($datos.modes.PSObject.Properties)
    if ($modos.Count -lt 5) { $problemas += "solo $($modos.Count) modos publicados, deberian ser 5" }
    foreach ($m in $modos) {
        if ($m.Value.stale) { $problemas += "modo '$($m.Name)' sirviendo dato guardado desde $($m.Value.stale_since)" }
    }

    if ($problemas.Count -gt 0) {
        Write-Host '  FALLA  el meta.json publicado en GitHub Pages' -ForegroundColor Red
        $problemas | ForEach-Object { Write-Host "     $_" }
        $fallos += 'web publicada'
    } else {
        Write-Host '  bien   el meta.json publicado en GitHub Pages' -ForegroundColor Green
        if ($Detalle) {
            Write-Host ("     publicado hace {0:N1} dias ({1})" -f $edad, $marca) -ForegroundColor DarkGray
            Write-Host "     $($modos.Count) modos, ninguno sirviendo dato guardado" -ForegroundColor DarkGray
        }
    }
}

if ($fallos.Count -gt 0) {
    Write-Host "Warezone: falla $($fallos -join ', ')" -ForegroundColor Red
    exit 1
}
if ($omitidos.Count -gt 0) {
    Write-Host "Warezone: bien, pero sin comprobar $($omitidos -join ' ni ')" -ForegroundColor Yellow
    exit 0
}
Write-Host 'Warezone: bien' -ForegroundColor Green
exit 0
