# ============================================================
# 🟡 MANTENIMIENTO SEMANAL - Dev Machine Cleanup
# ============================================================
# Ejecutar cada domingo o cuando termines la semana
# Mantiene el sistema sano, libera 1-5 GB
# ============================================================

$ErrorActionPreference = "SilentlyContinue"

function Get-FolderSize($path) {
    if (Test-Path $path) {
        return [math]::Round((Get-ChildItem $path -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB, 0)
    }
    return 0
}

function Clean-Folder($name, $path) {
    if (Test-Path $path) {
        $sizeBefore = Get-FolderSize $path
        if ($sizeBefore -gt 1) {
            Remove-Item "$path\*" -Recurse -Force -ErrorAction SilentlyContinue
            Write-Host "  ✓ $name : $sizeBefore MB liberados" -ForegroundColor Green
            return $sizeBefore
        }
    }
    return 0
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Yellow
Write-Host " 🟡 MANTENIMIENTO SEMANAL" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Yellow
Write-Host ""

# Estado inicial
$ramTotal = [math]::Round((Get-CimInstance Win32_OperatingSystem).TotalVisibleMemorySize / 1MB, 1)
$ramLibre = [math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB, 1)
$discoLibre = [math]::Round((Get-PSDrive C).Free / 1GB, 2)

Write-Host "📊 ESTADO DEL SISTEMA" -ForegroundColor Cyan
Write-Host "  RAM Total: $ramTotal GB | Libre: $ramLibre GB ($([math]::Round($ramLibre/$ramTotal*100,0))%)" -ForegroundColor White
Write-Host "  Disco C: Libre: $discoLibre GB" -ForegroundColor $(if($discoLibre -lt 15){"Red"}else{"Green"})
Write-Host ""

$liberadoTotal = 0

# 1. Temp
Write-Host "[1/6] Limpiando archivos temporales..." -ForegroundColor Cyan
$liberadoTotal += Clean-Folder "Temp Usuario" "$env:TEMP"
$liberadoTotal += Clean-Folder "Temp Windows" "C:\Windows\Temp"

# 2. Cachés de desarrollo
Write-Host "`n[2/6] Limpiando cachés de desarrollo..." -ForegroundColor Cyan
$liberadoTotal += Clean-Folder "npm-cache" "$env:LOCALAPPDATA\npm-cache"
try { pip cache purge 2>$null } catch {}

# 3. Logs de VS Code (mantener solo última semana)
Write-Host "`n[3/6] Limpiando logs antiguos de VS Code..." -ForegroundColor Cyan
$vscodeLogs = "$env:APPDATA\Code - Insiders\logs"
if (Test-Path $vscodeLogs) {
    Get-ChildItem $vscodeLogs -Directory -ErrorAction SilentlyContinue | Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-7) } | ForEach-Object {
        $sz = Get-FolderSize $_.FullName
        Remove-Item $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "  ✓ Log $($_.Name) : $sz MB" -ForegroundColor Green
        $liberadoTotal += $sz
    }
}

# 4. Compactar .git en repositorios
Write-Host "`n[4/6] Compactando repositorios Git..." -ForegroundColor Cyan
$proyectosPath = "C:\Users\julio\Documents\Proyectos"
if (Test-Path $proyectosPath) {
    Get-ChildItem $proyectosPath -Directory -ErrorAction SilentlyContinue | ForEach-Object {
        $gitDir = Join-Path $_.FullName ".git"
        if (Test-Path $gitDir) {
            Write-Host "  Git GC: $($_.Name)..." -ForegroundColor Gray
            $result = git -C $_.FullName gc --auto --quiet 2>&1
            if ($LASTEXITCODE -eq 0) { Write-Host "    ✓ OK" -ForegroundColor DarkGreen }
        }
    }
}

# 5. Thumbnails
Write-Host "`n[5/6] Limpiando Thumbnails..." -ForegroundColor Cyan
$liberadoTotal += Clean-Folder "Explorer Thumb" "$env:LOCALAPPDATA\Microsoft\Windows\Explorer"

# 6. Papelera
Write-Host "`n[6/6] Vaciando Papelera..." -ForegroundColor Cyan
Clear-RecycleBin -Force -ErrorAction SilentlyContinue
Write-Host "  ✓ Papelera vaciada" -ForegroundColor Green

# Resumen final
$discoLibreDespues = [math]::Round((Get-PSDrive C).Free / 1GB, 2)
$diferencia = [math]::Round($discoLibreDespues - $discoLibre, 2)

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host " ✅ MANTENIMIENTO COMPLETADO" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Disco libre antes:  $discoLibre GB" -ForegroundColor White
Write-Host "Disco libre ahora:  $discoLibreDespues GB" -ForegroundColor Green
Write-Host "Librado esta sesión: $diferencia GB ($liberadoTotal MB)" -ForegroundColor Green
Write-Host ""

# Recomendaciones automáticas
Write-Host "💡 RECOMENDACIONES:" -ForegroundColor Yellow
if ($discoLibreDespues -lt 15) {
    Write-Host "  ⚠ Disco crítico (<15GB). Ejecuta 'EMERGENCIA - Liberar Disco'" -ForegroundColor Red
}
$codeProcs = (Get-Process "Code - Insiders" -ErrorAction SilentlyContinue).Count
if ($codeProcs -gt 6) {
    Write-Host "  ⚠ Tienes $codeProcs procesos de VS Code. Considera cerrar proyectos que no uses." -ForegroundColor Yellow
    Write-Host "    Usa el acceso directo 'FRENAR VS CODE' si necesitas un reinicio limpio." -ForegroundColor Gray
}
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Presiona cualquier tecla para cerrar..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")