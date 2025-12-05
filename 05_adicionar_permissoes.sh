#!/bin/bash

echo "🔧 PASSO 5: Adicionando Diferenciação de Permissões"
echo "==================================================="
echo ""

# Adicionar indicadores visuais de permissão no dashboard
python3 << 'PYTHON_EOF'
with open('preview_assinatura_premium.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Procurar onde atualizar o role
role_update = '''
                currentUserData = await response.json();
                document.getElementById('userName').textContent = currentUserData.full_name || 'Usuário';
                
                // Atualizar role com cores e ícones
                const roleElement = document.getElementById('userRole');
                const roleMap = {
                    'OWNER': { text: '👑 Proprietário', color: '#ffd700', bg: '#fff3cd' },
                    'ADMIN': { text: '⭐ Administrador', color: '#667eea', bg: '#e8edff' },
                    'MEMBER': { text: '👤 Membro', color: '#6b7280', bg: '#f3f4f6' }
                };
                
                const roleInfo = roleMap[currentUserData.role] || roleMap['MEMBER'];
                roleElement.textContent = roleInfo.text;
                roleElement.style.background = roleInfo.bg;
                roleElement.style.color = roleInfo.color;
                roleElement.style.border = `2px solid ${roleInfo.color}`;
                
                // Mostrar/ocultar funcionalidades baseado em permissão
                updateUIBasedOnRole(currentUserData.role);
'''

if 'document.getElementById(\'userRole\').textContent = currentUserData.role' in content:
    content = content.replace(
        '''currentUserData = await response.json();
                document.getElementById('userName').textContent = currentUserData.full_name || 'Usuário';
                document.getElementById('userRole').textContent = currentUserData.role || 'Usuário';''',
        role_update
    )
    
    # Adicionar função para atualizar UI baseada em permissões
    ui_function = '''
        function updateUIBasedOnRole(role) {
            const isAdmin = role === 'OWNER' || role === 'ADMIN';
            
            // Botões que só admin pode ver
            const exportBtn = document.getElementById('exportBtn');
            
            if (exportBtn) {
                if (isAdmin) {
                    exportBtn.style.display = 'inline-flex';
                    exportBtn.title = 'Exportar relatórios (Admin)';
                } else {
                    exportBtn.style.display = 'none';
                }
            }
            
            // Adicionar badge nas funcionalidades restritas
            const navItems = document.querySelectorAll('.nav-item');
            navItems.forEach(item => {
                const target = item.getAttribute('data-target');
                
                if (target === 'templates' && !isAdmin) {
                    // Adicionar indicador visual
                    if (!item.querySelector('.admin-badge')) {
                        const badge = document.createElement('span');
                        badge.className = 'admin-badge';
                        badge.textContent = '🔒 Admin';
                        badge.style.cssText = 'font-size: 0.7rem; background: #ffd700; color: #000; padding: 2px 8px; border-radius: 10px; margin-left: auto;';
                        item.appendChild(badge);
                    }
                    
                    // Adicionar aviso ao clicar
                    item.addEventListener('click', function(e) {
                        if (!isAdmin) {
                            alert('⚠️ Você precisa de permissão de Administrador para acessar esta função.\\n\\nContate o proprietário da conta.');
                            e.stopPropagation();
                        }
                    }, { once: false });
                }
            });
            
            // Atualizar cards de analytics
            const analyticsCards = document.querySelectorAll('.analytics-card');
            if (!isAdmin && analyticsCards.length > 0) {
                analyticsCards.forEach(card => {
                    card.style.filter = 'blur(2px)';
                    card.style.pointerEvents = 'none';
                    card.title = 'Disponível apenas para Administradores';
                });
            }
        }
'''
    
    # Adicionar antes do loadUserData()
    if 'function updateUIBasedOnRole' not in content:
        content = content.replace(
            '// INICIALIZAÇÃO\n        loadUserData();',
            ui_function + '\n        // INICIALIZAÇÃO\n        loadUserData();'
        )
    
    with open('preview_assinatura_premium.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Diferenciação de permissões adicionada!")
else:
    print("ℹ️ Código já atualizado ou estrutura diferente")
PYTHON_EOF

echo ""
echo "==================================================="
echo "✅ PASSO 5 CONCLUÍDO!"
echo "==================================================="
echo ""
echo "👉 Execute: bash 05_adicionar_permissoes.sh"
