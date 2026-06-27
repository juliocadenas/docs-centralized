#!/bin/bash
# ============================================================
#  🧪 TEST COMPLETO - AI Hub Madrid
#  Verifica todos los endpoints del Gateway
#  Ejecutar en NAB9 o desde cualquier PC con acceso
# ============================================================

GATEWAY="${1:-http://localhost:9000}"
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; CYAN='\033[0;36m'; NC='\033[0m'
PASS=0; FAIL=0; WARN=0

echo -e "${CYAN}🧪 TEST AI Hub Madrid - $GATEWAY${NC}"
echo "================================================"

test_endpoint() {
  local name=$1
  local method=$2
  local url=$3
  local data=$4
  local expect=$5
  
  if [ "$method" = "GET" ]; then
    RESP=$(curl -s -m 15 -w "\n%{http_code}" "$GATEWAY$url" 2>/dev/null)
  else
    RESP=$(curl -s -m 30 -w "\n%{http_code}" -X "$method" "$GATEWAY$url" -H "Content-Type: application/json" -d "$data" 2>/dev/null)
  fi
  
  CODE=$(echo "$RESP" | tail -1)
  BODY=$(echo "$RESP" | head -n -1)
  
  if [ "$CODE" = "200" ] || [ "$CODE" = "201" ]; then
    if [ -n "$expect" ] && echo "$BODY" | grep -q "$expect"; then
      echo -e "${GREEN}  ✅ $name ($CODE)${NC}"
      PASS=$((PASS+1))
    elif [ -z "$expect" ]; then
      echo -e "${GREEN}  ✅ $name ($CODE)${NC}"
      PASS=$((PASS+1))
    else
      echo -e "${YELLOW}  ⚠️  $name ($CODE) - respuesta inesperada${NC}"
      WARN=$((WARN+1))
    fi
  elif [ "$CODE" = "404" ]; then
    echo -e "${RED}  ❌ $name (404 - No existe en esta versión)${NC}"
    FAIL=$((FAIL+1))
  else
    echo -e "${RED}  ❌ $name ($CODE)${NC}"
    FAIL=$((FAIL+1))
  fi
}

echo ""
echo -e "${CYAN}=== CORE ===${NC}"
test_endpoint "Gateway root" GET "/" "" "AI Hub Madrid"
test_endpoint "Gateway version" GET "/" "" "version"
test_endpoint "Health check" GET "/v1/health" "" ""
test_endpoint "System status" GET "/v1/status" "" "services"
test_endpoint "List models" GET "/v1/models" "" "data"
test_endpoint "Infrastructure" GET "/v1/infrastructure" "" ""

echo ""
echo -e "${CYAN}=== LLM ===${NC}"
test_endpoint "Chat qwen2.5:7b" POST "/v1/chat/completions" \
  '{"model":"qwen2.5:7b","messages":[{"role":"user","content":"di OK"}]}' \
  "choices"
test_endpoint "Chat llama3.1" POST "/v1/chat/completions" \
  '{"model":"llama3.1","messages":[{"role":"user","content":"di OK"}]}' \
  "choices"
test_endpoint "Embeddings" POST "/v1/embeddings" \
  '{"model":"nomic-embed-text","input":"test"}' \
  "embedding"

echo ""
echo -e "${CYAN}=== RAG (v2.3.0+) ===${NC}"
test_endpoint "RAG health" GET "/v1/rag/health" "" "status"
test_endpoint "RAG collections" GET "/v1/rag/collections" "" ""

echo ""
echo -e "${CYAN}=== VISION ===${NC}"
test_endpoint "Chat vision" POST "/v1/chat/vision" \
  '{"image_url":"test","prompt":"describe"}' \
  ""

echo ""
echo -e "${CYAN}=== TTS ===${NC}"
test_endpoint "Piper TTS" POST "/v1/audio/speech" \
  '{"model":"piper","input":"hola","language":"es"}' \
  ""

echo ""
echo -e "${CYAN}=== VIDEO AGENTIC (v2.3.0+) ===${NC}"
test_endpoint "Agentic video info" GET "/docs" "" ""

echo ""
echo "================================================"
echo -e "${GREEN}✅ Pass: $PASS${NC}  ${YELLOW}⚠️  Warn: $WARN${NC}  ${RED}❌ Fail: $FAIL${NC}"
echo ""

if [ $FAIL -gt 0 ]; then
  echo -e "${YELLOW}Los endpoints con ❌ requieren deploy v2.3.0${NC}"
  echo -e "${YELLOW}Ejecutar en NAB9: sudo bash DEPLOY_V23_NAB9.sh${NC}"
fi