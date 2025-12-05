#!/bin/bash

echo "🧪 TESTE FINAL - Verificando Todas as Correções"
echo "================================================"
echo ""

# Cores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

API_BASE="https://signature.thebroker.vip"
PASSED=0
FAILED=0

test_endpoint() {
    local name=$1
    local url=$2
    local method=${3:-GET}
    
    echo -n "Testando $name... "
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -o /dev/null -w "%{http_code}" "$url")
    fi
    
    if [ "$response" = "200" ] || [ "$response" = "401" ] || [ "$response" = "422" ]; then
        echo -e "${GREEN}✓${NC} (HTTP $response)"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}✗${NC} (HTTP $response)"
        FAILED=$((FAILED + 1))
    fi
}

echo "1️⃣ Testando API Base"
echo "-------------------"
test_endpoint "Health Check" "$API_BASE/health"
test_endpoint "Docs" "$API_BASE/docs"
echo ""

echo "2️⃣ Testando Endpoints de Autenticação"
echo "-------------------------------------"
test_endpoint "Auth - Me" "$API_BASE/api/v1/auth/me"
test_endpoint "Auth - Login" "$API_BASE/api/v1/auth/login"
echo ""

echo "3️⃣ Testando Endpoints de Usuário"
echo "--------------------------------"
test_endpoint "Users - Me" "$API_BASE/api/v1/users/me"
echo ""

echo "4️⃣ Testando Endpoints de Upload"
echo "-------------------------------"
test_endpoint "Upload - Avatar" "$API_BASE/api/v1/upload/avatar"
test_endpoint "Upload - Logo" "$API_BASE/api/v1/upload/logo"
echo ""

echo "5️⃣ Testando Endpoints de Assinaturas"
echo "------------------------------------"
test_endpoint "Signatures - List" "$API_BASE/api/v1/signatures/"
test_endpoint "Templates - List" "$API_BASE/api/v1/signature-templates/"
echo ""

echo "6️⃣ Verificando Arquivos Locais"
echo "------------------------------"

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✓${NC} $1 existe"
        PASSED=$((PASSED + 1))
    else
        echo -e "${RED}✗${NC} $1 NÃO existe"
        FAILED=$((FAILED + 1))
    fi
}

check_file "app/api/v1/users.py"
check_file "app/api/v1/upload_fix.py"
check_file "preview_assinatura_premium.html"
check_file "index.html"

echo ""
echo "7️⃣ Verificando Pillow"
echo "--------------------"
sudo docker-compose exec api pip list | grep -i pillow > /dev/null
if [ $? -eq 0 ]; then
    VERSION=$(sudo docker-compose exec api pip list | grep -i pillow | awk '{print $2}')
    echo -e "${GREEN}✓${NC} Pillow instalado (versão $VERSION)"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗${NC} Pillow NÃO instalado"
    FAILED=$((FAILED + 1))
fi

echo ""
echo "8️⃣ Verificando Containers Docker"
echo "--------------------------------"
CONTAINERS_UP=$(sudo docker-compose ps | grep "Up" | wc -l)
if [ $CONTAINERS_UP -ge 5 ]; then
    echo -e "${GREEN}✓${NC} $CONTAINERS_UP containers rodando"
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}✗${NC} Apenas $CONTAINERS_UP containers rodando (esperado: 5)"
    FAILED=$((FAILED + 1))
fi

echo ""
echo "================================================"
echo "📊 RESULTADO FINAL"
echo "================================================"
echo -e "Testes Passaram: ${GREEN}$PASSED${NC}"
echo -e "Testes Falharam: ${RED}$FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ TODOS OS TESTES PASSARAM!${NC}"
    echo ""
    echo "🎉 PRÓXIMOS PASSOS:"
    echo "1. Acesse: https://signature.thebroker.vip/"
    echo "2. Faça login"
    echo "3. Teste:"
    echo "   - Alterar dados no perfil (Configurações)"
    echo "   - Upload de avatar"
    echo "   - Criar nova assinatura (botão + Nova Assinatura)"
    echo "   - Verificar diferenciação Admin/Membro"
else
    echo -e "${YELLOW}⚠️ ALGUNS TESTES FALHARAM${NC}"
    echo ""
    echo "Verifique:"
    echo "1. Se todos os scripts anteriores foram executados"
    echo "2. Se a API está rodando: sudo docker-compose ps"
    echo "3. Logs da API: sudo docker-compose logs api"
fi

echo ""
echo "================================================"
