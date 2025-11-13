#!/bin/bash

# Encontrar e substituir a linha do preview no script de teste
sed -i 's|/api/v1/signatures/preview|/api/v1/signatures/preview/|g' test_all_days_complete.sh

echo "✅ Script corrigido!"
