# ============================================================
# 🔵 FRENAR VS CODE - Botón de pánico para RAM
# ============================================================
# Mata TODOS los procesos de VS Code y node.exe zombis
# Libera 4-7 GB de RAM instantáneamente
# ============================================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Blue
Write-Host " 🔵 FRENAR VS CODE + NODE ZOMBIS" -ForegroundColor Blue
Write-Host "========================================" -ForegroundColor Blue
Write-Host ""

# RAM antes
$ramAntes = [math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB, 1)
Write-Host "RAM libre antes: $ramAntes GB" -ForegroundColor Yellow
Write-Host ""

# Contar procesos
$codeProcs = Get-Process "Code - Insiders" -ErrorAction SilentlyContinue
$nodeProcs = Get-Process "node" -ErrorAction SilentlyContinue
$codeCount = if ($codeProcs) { $codeProcs.Count } else { 0 }
$nodeCount = if ($nodeProcs) { $nodeProcs.Count } else { 0 }

Write-Host "Procesos encontrados:" -ForegroundColor Cyan
Write-Host "  VS Code Insiders: $codeCount procesos" -ForegroundColor White
Write-Host "  Node.js:          $nodeCount procesos" -ForegroundColor White
Write-Host ""

if ($codeCount -eq 0 -and $nodeCount -eq 0) {
    Write-Host "✅ No hay procesos que matar. Todo limpio." -ForegroundColor Green
} else {
    Write-Host "Matando procesos..." -ForegroundColor Red
    
    # Matar VS Code
    if ($codeCount -gt 0) {
        $codeProcs | Stop-Process -Force -ErrorAction SilentlyContinue
        Write-Host "  ✓ $codeCount procesos de VS Code terminados" -ForegroundColor Green
    }
    
    # Matar node.exe (cuidado: esto también mata el servidor MCP si está corriendo)
    if ($nodeCount -gt 0) {
        Start-Sleep -Milliseconds 500
        $nodeProcs = Get-Process "node" -ErrorAction SilentlyContinue
        if ($nodeProcs) {
            $nodeProcs | Stop-Process -Force -ErrorAction SilentlyContinue
            Write-Host "  ✓ $($nodeProcs.Count) procesos Node.js terminados" -ForegroundColor Green
        }
    }
    
    # Matar bun.exe si existe
    $bunProcs = Get-Process "bun" -ErrorAction SilentlyContinue
    if ($bunProcs) {
        $bunProcs | Stop-Process -Force -ErrorAction SilentlyContinue
        Write-Host "  ✓ $($bunProcs.Count) procesos Bun terminados" -ForegroundColor Green
    }
    
    Start-Sleep -Seconds 2
    
    # RAM después
    $ramDespues = [math]::Round((Get-CimInstance Win32_OperatingSystem).FreePhysicalMemory / 1MB, 1)
    $liberada = [math]::Round($ramDespues - $ramAntes, 1)
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host " ✅ PROCESOS TERMINADOS" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "RAM libre antes:  $ramAntes GB" -ForegroundColor White
    Write-Host "RAM libre ahora:  $ramDespues GB" -ForegroundColor Green
    Write-Host "RAM LIBERADA:     $liberada GB" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
}

Write-Host ""
Write-Host "Presiona cualquier tecla para cerrar..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")