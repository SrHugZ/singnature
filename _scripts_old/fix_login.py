with open('index.html', 'r') as f:
    content = f.read()

# Corrigir fetch sem parênteses
content = content.replace("fetch`${API_BASE}/api/v1/auth/me`", "fetch(`${API_BASE}/api/v1/auth/me`")

# Garantir redirecionamento correto
content = content.replace("'preview_assinatura.html'", "'preview_assinatura_premium.html'")

with open('index.html', 'w') as f:
    f.write(content)

print("✅ index.html corrigido!")
