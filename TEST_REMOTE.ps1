# ============================================================
#  🧪 TEST REMOTO - AI Hub Madrid desde Windows
#  Verifica el estado del NAB9 sin necesidad de SSH
# ============================================================

$Gateway = "http://100.105.27.27:9000"
$Studio = "http://100.105.27.27:3000"
$Pass = 0; $Warn = 0; $Fail = 0

Write-Host "🧪 TEST AI Hub Madrid - NAB9 Remoto" -ForegroundColor Cyan
Write-Host "============================================"

function Test-Endpoint {
    param($Name, $Url, $Method = "GET", $Body = $null, $Expect = $null)
    
    try {
        $headers = @{ "Content-Type" = "application/json" }
        if ($Method -eq "GET") {
            $resp = Invoke-WebRequest -Uri $Url -Method GET -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
        } else {
            $resp = Invoke-WebRequest -Uri $Url -Method POST -Headers $headers -Body $Body -TimeoutSec 20 -UseBasicParsing -ErrorAction Stop
        }
        
        $content = $resp.Content
        if ($Expect -and $content -match $Expect) {
            Write-Host "  ✅ $Name ($($resp.StatusCode))" -ForegroundColor Green
            $script:Pass++
        } elseif (-not $Expect) {
            Write-Host "  ✅ $Name ($($resp.StatusCode))" -ForegroundColor Green
            $script:Pass++
        } else {
            Write-Host "  ⚠️  $Name ($($resp.StatusCode)) - respuesta inesperada" -ForegroundColor Yellow
            $script:Warn++
        }
    } catch {
        $code = $_.Exception.Response.StatusCode.value__
        if ($code -eq 404) {
            Write-Host "  ❌ $Name (404 - No existe en v2.1.0)" -ForegroundColor Red
            $script:Fail++
        } elseif ($_.Exception.Message -match "timed out") {
            Write-Host "  ⚠️  $Name (Timeout)" -ForegroundColor Yellow
            $script:Warn++
        } else {
            Write-Host "  ❌ $Name ($code)" -ForegroundColor Red
            $script:Fail++
        }
    }
}

Write-Host ""
Write-Host "=== CORE ===" -ForegroundColor Cyan
Test-Endpoint "Gateway root" "$Gateway/" "GET" $null "AI Hub Madrid"
Test-Endpoint "Gateway version" "$Gateway/" "GET" $null "version"
Test-Endpoint "System status" "$Gateway/v1/status" "GET" $null "services"
Test-Endpoint "List models" "$Gateway/v1/models" "GET" $null "data"
Test-Endpoint "Studio UI" "$Studio" "GET" $null "AI Hub Madrid"

Write-Host ""
Write-Host "=== LLM ===" -ForegroundColor Cyan
Test-Endpoint "Chat qwen2.5:7b" "$Gateway/v1/chat/completions" "POST" '{"model":"qwen2.5:7b","messages":[{"role":"user","content":"di OK"}]}' "choices"
Test-Endpoint "Embeddings" "$Gateway/v1/embeddings" "POST" '{"model":"nomic-embed-text","input":"test"}' "embedding"

Write-Host ""
Write-Host "=== RAG (v2.3.0+) ===" -ForegroundColor Cyan
Test-Endpoint "RAG health" "$Gateway/v1/rag/health" "GET" $null "status"
Test-Endpoint "RAG collections" "$Gateway/v1/rag/collections" "GET" $null $null

Write-Host ""
Write-Host "=== VISION ===" -ForegroundColor Cyan
Test-Endpoint "Chat vision" "$Gateway/v1/chat/vision" "POST" '{"image_url":"test","prompt":"describe"}' $null

Write-Host ""
Write-Host "=== TTS ===" -ForegroundColor Cyan
Test-Endpoint "Piper TTS" "$Gateway/v1/audio/speech" "POST" '{"model":"piper","input":"hola","language":"es"}' $null

Write-Host ""
Write-Host "============================================"
Write-Host "✅ Pass: $Pass  ⚠️  Warn: $Warn  ❌ Fail: $Fail" -ForegroundColor $(if ($Fail -gt 0) {"Yellow"} else {"Green"})
Write-Host ""

# Extraer versión
try {
    $root = (Invoke-WebRequest -Uri "$Gateway/" -TimeoutSec 5 -UseBasicParsing).Content | ConvertFrom-Json
    Write-Host "Gateway version: $($root.version)" -ForegroundColor Cyan
    
    if ($root.version -lt "2.3.0") {
        Write-Host ""
        Write-Host "⚠️  Gateway desactualizado ($($root.version) < 2.3.0)" -ForegroundColor Yellow
        Write-Host "Para actualizar, ejecuta en el NAB9:" -ForegroundColor Yellow
        Write-Host "  sudo bash DEPLOY_V23_NAB9.sh" -ForegroundColor White
    } else {
        Write-Host ""
        Write-Host "✅ Gateway actualizado!" -ForegroundColor Green
    }
} catch {
    Write-Host "No se pudo obtener la versión del Gateway" -ForegroundColor Red
}