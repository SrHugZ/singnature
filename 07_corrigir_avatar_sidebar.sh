#!/bin/bash

echo "🔧 CORREÇÃO: Avatar na Sidebar"
echo "=============================="
echo ""

# Fazer backup
cp preview_assinatura_premium.html preview_assinatura_premium.html.backup_avatar_$(date +%Y%m%d_%H%M%S)
echo "✅ Backup criado!"

# Atualizar HTML para mostrar avatar na sidebar
python3 << 'PYTHON_EOF'
import re

with open('preview_assinatura_premium.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Substituir a área do logo na sidebar
old_logo = r'<div class="logo-animation">✨</div>'
new_logo = '''<div class="logo-animation" id="sidebarAvatarContainer">
            <img id="sidebarAvatar" src="" alt="Avatar" style="width: 100%; height: 100%; object-fit: cover; border-radius: 20px; display: none;">
            <span id="sidebarAvatarPlaceholder">✨</span>
        </div>'''

if old_logo in content:
    content = content.replace(old_logo, new_logo)
    print("✅ Logo da sidebar atualizado")
else:
    print("ℹ️ Logo já estava atualizado")

# Adicionar função para atualizar avatar na sidebar
avatar_function = '''
        // Função para atualizar avatar na sidebar
        function updateSidebarAvatar(avatarUrl) {
            const sidebarAvatar = document.getElementById('sidebarAvatar');
            const sidebarPlaceholder = document.getElementById('sidebarAvatarPlaceholder');
            
            if (avatarUrl && avatarUrl !== 'null' && avatarUrl !== '') {
                sidebarAvatar.src = avatarUrl + '?t=' + Date.now();
                sidebarAvatar.style.display = 'block';
                if (sidebarPlaceholder) sidebarPlaceholder.style.display = 'none';
            } else {
                sidebarAvatar.style.display = 'none';
                if (sidebarPlaceholder) sidebarPlaceholder.style.display = 'block';
            }
        }
'''

# Adicionar antes do loadUserData() se não existir
if 'function updateSidebarAvatar' not in content:
    content = content.replace(
        '// INICIALIZAÇÃO\n        loadUserData();',
        avatar_function + '\n        // INICIALIZAÇÃO\n        loadUserData();'
    )
    print("✅ Função updateSidebarAvatar adicionada")
else:
    print("ℹ️ Função já existia")

# Atualizar loadUserData para carregar avatar na sidebar
old_load_user = 'document.getElementById(\'userName\').textContent = currentUserData.full_name || \'Usuário\';'
new_load_user = '''document.getElementById('userName').textContent = currentUserData.full_name || 'Usuário';
                
                // Atualizar avatar na sidebar
                updateSidebarAvatar(currentUserData.avatar_url);'''

if old_load_user in content and 'updateSidebarAvatar(currentUserData.avatar_url)' not in content:
    content = content.replace(old_load_user, new_load_user)
    print("✅ loadUserData atualizado")
else:
    print("ℹ️ loadUserData já estava atualizado")

# Atualizar função de upload para atualizar sidebar imediatamente
old_upload = '''const sidebarAvatar = document.getElementById('userAvatar');
        if (sidebarAvatar) {
            sidebarAvatar.src = data.avatar_url + '?t=' + Date.now();
        }'''

new_upload = '''// Atualizar sidebar
        updateSidebarAvatar(data.avatar_url);'''

if old_upload in content:
    content = content.replace(old_upload, new_upload)
    print("✅ Upload atualizado")
else:
    # Se não encontrou o antigo, adicionar após sucesso do upload
    if 'alert(\'✅ Foto de perfil atualizada com sucesso!\');' in content:
        content = content.replace(
            'alert(\'✅ Foto de perfil atualizada com sucesso!\');',
            '''updateSidebarAvatar(data.avatar_url);
        alert('✅ Foto de perfil atualizada com sucesso!');'''
        )
        print("✅ Upload atualizado (alternativo)")

# Atualizar remoção de avatar
if 'avatar removido com sucesso' in content and 'updateSidebarAvatar(null)' not in content:
    content = content.replace(
        'alert(\'✅ Foto removida com sucesso!\');',
        '''updateSidebarAvatar(null);
        alert('✅ Foto removida com sucesso!');'''
    )
    print("✅ Remoção de avatar atualizada")

with open('preview_assinatura_premium.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n✅ Correções aplicadas!")
PYTHON_EOF

echo ""
echo "=============================="
echo "✅ CORREÇÃO CONCLUÍDA!"
echo "=============================="
echo ""
echo "👉 Agora:"
echo "1. Recarregue a página (Ctrl+F5)"
echo "2. O avatar deve aparecer na sidebar"
echo "3. Se não aparecer, faça upload novamente"
