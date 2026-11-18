$ErrorActionPreference = 'Stop'
Set-Location (Split-Path -Parent $PSScriptRoot)
$base = (Get-Location).Path
Write-Host "`n=== INSTALADOR AGENTES LANGCHAIN + GEMMA ===" -ForegroundColor Cyan
Write-Host "Carpeta: $base"

# Verifica una version sin que PowerShell 5.1 detenga todo ante stderr nativo.
function Test-PyVersion([string]$ver) {
    $previous = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $null = & py "-$ver" -c 'import sys; print(sys.executable)' 2>$null
        return ($LASTEXITCODE -eq 0)
    }
    catch { return $false }
    finally { $ErrorActionPreference = $previous }
}
function Test-PathPython {
    $previous = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $value = & python -c 'import sys; print(str(sys.version_info.major) + "." + str(sys.version_info.minor))' 2>$null
        if ($LASTEXITCODE -eq 0 -and $value) { return $value }
        return $null
    }
    catch { return $null }
    finally { $ErrorActionPreference = $previous }
}
function Find-Python {
    if (Get-Command py -ErrorAction SilentlyContinue) {
        foreach ($ver in @('3.14','3.12','3.13','3.11')) {
            if (Test-PyVersion $ver) { return @{Kind='launcher';Version=$ver} }
        }
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        $version = Test-PathPython
        if ($version) { return @{Kind='path';Version=$version} }
    }
    # En instalaciones nuevas, winget puede instalar Python sin actualizar el PATH de esta terminal.
    foreach ($ver in @('Python314','Python312','Python313','Python311')) {
        $exe = Join-Path $env:LOCALAPPDATA "Programs\Python\$ver\python.exe"
        if (Test-Path $exe) { return @{Kind='exe';Version=$ver;Path=$exe} }
    }
    return $null
}
function Run-Python($spec, [string[]]$arguments) {
    if ($spec.Kind -eq 'launcher') { & py "-$($spec.Version)" @arguments }
    elseif ($spec.Kind -eq 'exe') { & $spec.Path @arguments }
    else { & python @arguments }
    if ($LASTEXITCODE -ne 0) { throw "Fallo Python: $($arguments -join ' ')" }
}

$python = Find-Python
if (-not $python) {
    Write-Host 'Python no encontrado. Intentando instalar Python 3.12 con winget...' -ForegroundColor Yellow
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        throw 'No existe winget. Instala Python 3.12 desde python.org, abre una terminal nueva y repite INSTALAR.bat.'
    }
    & winget install --id Python.Python.3.12 --exact --source winget --accept-package-agreements --accept-source-agreements --silent
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo instalar Python automaticamente. Instala Python 3.12 y vuelve a intentarlo.' }
    $env:Path += ";$env:LOCALAPPDATA\Programs\Python\Python312;$env:LOCALAPPDATA\Programs\Python\Python312\Scripts"
    $python = Find-Python
    if (-not $python) { throw 'Python se instalo, pero Windows aun no lo reconoce. Cierra y abre una terminal y ejecuta INSTALAR.bat otra vez.' }
}
Write-Host "Python detectado: $($python.Version)" -ForegroundColor Green
$venvPython = Join-Path $base '.venv\Scripts\python.exe'
if (-not (Test-Path $venvPython)) {
    Write-Host 'Creando entorno virtual...'
    Run-Python $python @('-m','venv','.venv')
}
Write-Host 'Instalando dependencias Python (puede demorar)...'
& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw 'No se pudo actualizar pip.' }
& $venvPython -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'No se pudieron instalar las dependencias. Revisa los errores de pip.' }

if (-not (Test-Path '.env')) {
    Copy-Item '.env.example' '.env'
    Write-Host 'Creado .env nuevo (sin credenciales privadas).' -ForegroundColor Green
} else {
    Write-Host 'Ya existe .env: no se modifica.'
}

$ollama = Get-Command ollama -ErrorAction SilentlyContinue
if (-not $ollama) {
    foreach ($candidate in @("$env:LOCALAPPDATA\Programs\Ollama\ollama.exe", "$env:ProgramFiles\Ollama\ollama.exe")) {
        if (Test-Path $candidate) { $ollama = @{Source=$candidate}; break }
    }
}
if (-not $ollama) {
    Write-Host 'Ollama no encontrado. Intentando instalarlo con winget...' -ForegroundColor Yellow
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        throw 'Instala Ollama desde ollama.com/download y repite INSTALAR.bat.'
    }
    & winget install --id Ollama.Ollama --exact --source winget --accept-package-agreements --accept-source-agreements --silent
    if ($LASTEXITCODE -ne 0) { throw 'No se pudo instalar Ollama. Instala Ollama desde ollama.com/download y reintenta.' }
    $ollama = Get-Command ollama -ErrorAction SilentlyContinue
    if (-not $ollama) {
        foreach ($candidate in @("$env:LOCALAPPDATA\Programs\Ollama\ollama.exe", "$env:ProgramFiles\Ollama\ollama.exe")) {
            if (Test-Path $candidate) { $ollama = @{Source=$candidate}; break }
        }
    }
    if (-not $ollama) { throw 'Ollama instalado, pero aun no se detecta. Reinicia la terminal y ejecuta INSTALAR.bat otra vez.' }
}
$ollamaExe = $ollama.Source
Write-Host "Ollama encontrado: $ollamaExe" -ForegroundColor Green
Write-Host 'Comprobando servidor Ollama...'
try { Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 3 | Out-Null }
catch {
    Write-Host 'Iniciando Ollama...'
    Start-Process -FilePath $ollamaExe -ArgumentList 'serve' -WindowStyle Hidden
    Start-Sleep -Seconds 4
}

Write-Host 'Verificando si Gemma 3:1b ya esta instalado...'

$modelos = & $ollamaExe list

if ($LASTEXITCODE -ne 0) {
    throw 'No se pudo consultar Ollama. Verifica que este en ejecucion.'
}

if ($modelos -match 'gemma3:1b') {
    Write-Host 'Gemma 3:1b ya esta instalado.' -ForegroundColor Green
    Write-Host 'No es necesario descargarlo nuevamente.'
}
else {
    Write-Host 'Gemma no esta instalado. Iniciando descarga...'

    & $ollamaExe pull gemma3:1b

    if ($LASTEXITCODE -ne 0) {
        throw 'No se pudo descargar Gemma. Comprueba tu conexion a Internet.'
    }

    Write-Host 'Gemma descargado correctamente.' -ForegroundColor Green
}

Write-Host "`nInstalacion completa." -ForegroundColor Green
Write-Host 'Para probar: haz doble clic en INICIAR.bat y elige la opcion 1.'
Write-Host 'Para LangSmith: INICIAR.bat, opcion 7, configura tu propia API key y activa tracing.'
