#!/bin/bash

echo "🔧 PASSO 1: Instalando Pillow"
echo "================================"
echo ""

# Adicionar Pillow ao requirements.txt se não existir
if ! grep -q "Pillow" requirements.txt; then
    echo "Pillow==10.2.0" >> requirements.txt
    echo "✅ Pillow adicionado ao requirements.txt"
else
    echo "ℹ️ Pillow já está no requirements.txt"
fi

echo ""
echo "📦 Instalando Pillow no container..."
sudo docker-compose exec api pip install Pillow==10.2.0 --break-system-packages

echo ""
echo "🔄 Reiniciando API..."
sudo docker-compose restart api

echo ""
echo "⏳ Aguardando API reiniciar (15 segundos)..."
sleep 15

echo ""
echo "🧪 Testando se a API voltou..."
curl -s https://signature.thebroker.vip/health | python3 -m json.tool

echo ""
echo "================================"
echo "✅ PASSO 1 CONCLUÍDO!"
echo "================================"
echo ""
echo "👉 Execute este script com:"
echo "   bash 01_instalar_pillow.sh"
echo ""
echo "👉 Depois me confirme se funcionou!"
