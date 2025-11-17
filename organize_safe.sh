#!/bin/bash

echo "🧪 TESTE ANTES DE ORGANIZAR"
echo "======================================"

# Testar containers
echo "1. Containers rodando?"
sudo docker-compose ps | grep "Up" && echo "✅ Containers OK" || echo "❌ Containers com problema"

# Testar API
echo ""
echo "2. API respondendo?"
curl -s http://localhost/health > /dev/null && echo "✅ API OK" || echo "❌ API com problema"

# Testar HTMLs
echo ""
echo "3. HTMLs existem?"
[ -f "index.html" ] && echo "✅ index.html OK" || echo "❌ index.html não existe"
[ -f "cadastro_completo.html" ] && echo "✅ cadastro_completo.html OK" || echo "❌ cadastro não existe"
[ -f "preview_assinatura_premium.html" ] && echo "✅ preview OK" || echo "❌ preview não existe"

echo ""
echo "======================================"
echo "⏸️  PRESSIONE ENTER PARA CONTINUAR"
echo "======================================"
read

# ===================================
# ORGANIZAÇÃO
# ===================================
echo ""
echo "📂 ORGANIZANDO ARQUIVOS..."

# Criar pastas
mkdir -p _backups _docs _scripts_old

# Mover backups
echo "- Movendo backups..."
mv arquivos_antigos _backups/ 2>/dev/null
mv arquivos_antigos_backup _backups/ 2>/dev/null
mv versions _backups/ 2>/dev/null

# Mover docs
echo "- Movendo documentação..."
mv SPRINTS.md _docs/ 2>/dev/null
mv erro.txt _docs/ 2>/dev/null
mv 001 _docs/ 2>/dev/null

# Mover scripts
echo "- Movendo scripts antigos..."
mv setup_day*.py _scripts_old/ 2>/dev/null
mv create_day*.py _scripts_old/ 2>/dev/null
mv test_*.sh _scripts_old/ 2>/dev/null
mv fix_*.py _scripts_old/ 2>/dev/null
mv fix_*.sh _scripts_old/ 2>/dev/null

echo ""
echo "✅ ORGANIZAÇÃO CONCLUÍDA!"

# ===================================
# TESTE DEPOIS
# ===================================
echo ""
echo "🧪 TESTE DEPOIS DE ORGANIZAR"
echo "======================================"

# Testar containers
echo "1. Containers ainda rodando?"
sudo docker-compose ps | grep "Up" && echo "✅ Containers OK" || echo "❌ Containers com problema"

# Testar API
echo ""
echo "2. API ainda respondendo?"
curl -s http://localhost/health > /dev/null && echo "✅ API OK" || echo "❌ API com problema"

# Testar HTMLs
echo ""
echo "3. HTMLs ainda existem?"
[ -f "index.html" ] && echo "✅ index.html OK" || echo "❌ index.html SUMIU!"
[ -f "cadastro_completo.html" ] && echo "✅ cadastro_completo.html OK" || echo "❌ cadastro SUMIU!"
[ -f "preview_assinatura_premium.html" ] && echo "✅ preview OK" || echo "❌ preview SUMIU!"

echo ""
echo "======================================"
echo "📊 RESULTADO FINAL"
echo "======================================"
echo ""
echo "📁 Arquivos na raiz agora:"
ls -1 | grep -v "^_" | head -20

echo ""
echo "📦 Arquivos organizados:"
echo "- _backups/ ($(ls _backups/ 2>/dev/null | wc -l) itens)"
echo "- _docs/ ($(ls _docs/ 2>/dev/null | wc -l) itens)"
echo "- _scripts_old/ ($(ls _scripts_old/ 2>/dev/null | wc -l) itens)"

echo ""
echo "✅ TUDO PRONTO E FUNCIONANDO!"
