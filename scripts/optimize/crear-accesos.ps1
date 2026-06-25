# ============================================================
# Crear accesos directos en el Escritorio
# ============================================================

$scriptsDir = "C:\Users\julio\Documents\Proyectos\IA-HUB-MADRID1\scripts\optimize"
$desktop = [Environment]::GetFolderPath("Desktop")
$shell = New-Object -ComObject WScript.Shell

Write-Host "Creando accesos directos en el Escritorio..." -ForegroundColor Cyan

# 1. EMERGENCIA
$lnk1 = $shell.CreateShortcut("$desktop\EMERGENCIA - Liberar Disco.lnk")
$lnk1.TargetPath = "powershell.exe"
$lnk1.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$scriptsDir\emergencia-disco.ps1`""
$lnk1.WorkingDirectory = $scriptsDir
$lnk1.IconLocation = "shell32.dll,131"
$lnk1.Description = "Limpieza agresiva de disco - Freno de mano"
$lnk1.WindowStyle = 1
$lnk1.Save()
Write-Host "  [OK] EMERGENCIA - Liberar Disco.lnk" -ForegroundColor Green

# 2. MANTENIMIENTO SEMANAL
$lnk2 = $shell.CreateShortcut("$desktop\MANTENIMIENTO SEMANAL.lnk")
$lnk2.TargetPath = "powershell.exe"
$lnk2.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$scriptsDir\mantenimiento-semanal.ps1`""
$lnk2.WorkingDirectory = $scriptsDir
$lnk2.IconLocation = "shell32.dll,19"
$lnk2.Description = "Mantenimiento semanal de la maquina de desarrollo"
$lnk2.WindowStyle = 1
$lnk2.Save()
Write-Host "  [OK] MANTENIMIENTO SEMANAL.lnk" -ForegroundColor Green

# 3. FRENAR VS CODE
$lnk3 = $shell.CreateShortcut("$desktop\FRENAR VS CODE.lnk")
$lnk3.TargetPath = "powershell.exe"
$lnk3.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$scriptsDir\kill-vscode.ps1`""
$lnk3.WorkingDirectory = $scriptsDir
$lnk3.IconLocation = "shell32.dll,131"
$lnk3.Description = "Matar procesos VS Code y Node - Boton de panico"
$lnk3.WindowStyle = 1
$lnk3.Save()
Write-Host "  [OK] FRENAR VS CODE.lnk" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host " 3 ACCESOS DIRECTOS CREADOS" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Ubicacion: $desktop" -ForegroundColor White