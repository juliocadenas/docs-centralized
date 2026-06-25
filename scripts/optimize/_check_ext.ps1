$ext = "C:\Users\julio\.vscode-insiders\extensions"
if (Test-Path $ext) {
    Write-Host "=== EXTENSIONES VS CODE >50MB ==="
    Get-ChildItem $ext -Directory | ForEach-Object {
        $sz = [math]::Round((Get-ChildItem $_.FullName -Recurse -Force -EA SilentlyContinue | Measure-Object Length -Sum).Sum / 1MB, 0)
        if ($sz -gt 50) {
            $color = if ($sz -gt 200) { "Red" } else { "Yellow" }
            Write-Host "$($_.Name) = $sz MB" -ForegroundColor $color
        }
    }
}