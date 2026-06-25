# ============================================================
# EMERGENCIA - Liberar Disco (Freno de mano)
# ============================================================

$ErrorActionPreference = "SilentlyContinue"
$totalLiberado = 0

function Get-FolderSize($path) {
    if (Test-Path $path) {
        return [math]::Round((Get-ChildItem $path -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB, 0)
    }
    return 0
}

function Clean-Folder($name, $path) {
    if (Test-Path $path) {
        $sizeBefore = Get-FolderSize $path
        Remove-Item "$path\*" -Recurse -Force -ErrorAction SilentlyContinue
        $sizeAfter = Get-FolderSize $path
        $liberado = $sizeBefore - $sizeAfter
        Write-Host "  [$name] Liberados $liberado MB" -ForegroundColor Green
        return $liberado
    }
    return 0
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Red
Write-Host " EMERGENCIA - LIBERAR DISCO C:" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Red
Write-Host ""

# Estado inicial
$discoAntes = (Get-PSDrive C)
$libreAntes = [math]::Round($discoAntes.Free / 1GB, 2)
Write-Host "Estado inicial: $libreAntes GB libres" -ForegroundColor Yellow
Write-Host ""

# 1. Temp de usuario
Write-Host "[1/9] Limpiando Temp de usuario..." -ForegroundColor Cyan
$totalLiberado += Clean-Folder "Temp Usuario" "$env:TEMP"
$totalLiberado += Clean-Folder "Temp Windows" "C:\Windows\Temp"
$totalLiberado += Clean-Folder "Prefetch" "C:\Windows\Prefetch"

# 2. Cache npm
Write-Host "`n[2/9] Limpiando cache npm..." -ForegroundColor Cyan
$npmCache = "$env:LOCALAPPDATA\npm-cache"
$totalLiberado += Clean-Folder "npm-cache" $npmCache

# 3. Cache pip
Write-Host "`n[3/9] Limpiando cache pip..." -ForegroundColor Cyan
$totalLiberado += Clean-Folder "pip cache" "$env:LOCALAPPDATA\pip\cache"

# 4. Cache de yarn y pnpm
Write-Host "`n[4/9] Limpiando cache yarn/pnpm..." -ForegroundColor Cyan
$totalLiberado += Clean-Folder "yarn cache" "$env:LOCALAPPDATA\Yarn\Cache"
$totalLiberado += Clean-Folder "pnpm store" "$env:LOCALAPPDATA\pnpm\store"

# 5. Logs y crash dumps de VS Code
Write-Host "`n[5/9] Limpiando logs VS Code y crash dumps..." -ForegroundColor Cyan
$totalLiberado += Clean-Folder "VS Code logs" "$env:APPDATA\Code - Insiders\logs"
$totalLiberado += Clean-Folder "VS Code Cache" "$env:APPDATA\Code - Insiders\Cache"
$totalLiberado += Clean-Folder "VS Code CachedData" "$env:APPDATA\Code - Insiders\CachedData"
$totalLiberado += Clean-Folder "Crash Dumps" "$env:LOCALAPPDATA\CrashDumps"

# 6. Thumbnails y cache de Explorer
Write-Host "`n[6/9] Limpiando Thumbnails..." -ForegroundColor Cyan
$totalLiberado += Clean-Folder "Thumbnails" "$env:LOCALAPPDATA\Microsoft\Windows\Explorer"
$totalLiberado += Clean-Folder "INetCache" "$env:LOCALAPPDATA\Microsoft\Windows\INetCache"

# 7. Windows Update Cache
Write-Host "`n[7/9] Limpiando Windows Update Cache..." -ForegroundColor Cyan
$softwareDist = "C:\Windows\SoftwareDistribution\Download"
$totalLiberado += Clean-Folder "Windows Update" $softwareDist

# 8. Papelera de reciclaje
Write-Host "`n[8/9] Vaciando Papelera de reciclaje..." -ForegroundColor Cyan
Clear-RecycleBin -Force -ErrorAction SilentlyContinue
Write-Host "  [Papelera] Vaciada" -ForegroundColor Green

# 9. .next y node_modules/.cache en proyectos
Write-Host "`n[9/9] Limpiando caches de proyectos..." -ForegroundColor Cyan
$proyectosPath = "C:\Users\julio\Documents\Proyectos"
if (Test-Path $proyectosPath) {
    # Buscar y limpiar .next
    Get-ChildItem $proyectosPath -Recurse -Directory -Filter ".next" -Depth 3 -ErrorAction SilentlyContinue | ForEach-Object {
        $sizeNext = Get-FolderSize $_.FullName
        if ($sizeNext -gt 10) {
            Remove-Item $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
            Write-Host "  [.next] $($_.Parent.Name) - $sizeNext MB" -ForegroundColor Green
            $totalLiberado += $sizeNext
        }
    }
    # Buscar y limpiar node_modules/.cache
    Get-ChildItem $proyectosPath -Recurse -Directory -Filter ".cache" -Depth 4 -ErrorAction SilentlyContinue | ForEach-Object {
        if ($_.FullName -like "*node_modules*") {
            $sizeCache = Get-FolderSize $_.FullName
            if ($sizeCache -gt 5) {
                Remove-Item $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
                Write-Host "  [.cache] $($_.Parent.Parent.Parent.Name) - $sizeCache MB" -ForegroundColor Green
                $totalLiberado += $sizeCache
            }
        }
    }
}

# DISM (WinSxS) - requiere admin
Write-Host "`n[EXTRA] Compactando WinSxS..." -ForegroundColor Cyan
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if ($isAdmin) {
    Write-Host "  Ejecutando DISM..." -ForegroundColor Yellow
    $result = DISM /Online /Cleanup-Image /StartComponentCleanup /ResetBase 2>&1
    Write-Host "  DISM completado" -ForegroundColor Green
} else {
    Write-Host "  Saltando DISM - requiere Admin. Ejecuta como Admin para liberar 3-8GB extra." -ForegroundColor Yellow
}

# Estado final
$discoDespues = (Get-PSDrive C)
$libreDespues = [math]::Round($discoDespues.Free / 1GB, 2)
$diferencia = [math]::Round($libreDespues - $libreAntes, 2)

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host " LIMPIEZA COMPLETADA" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Espacio libre antes:  $libreAntes GB" -ForegroundColor White
Write-Host "Espacio libre ahora:  $libreDespues GB" -ForegroundColor Green
Write-Host "TOTAL LIBERADO:       $diferencia GB" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""