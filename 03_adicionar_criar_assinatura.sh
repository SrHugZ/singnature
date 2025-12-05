#!/bin/bash

echo "🔧 PASSO 3: Adicionando Botão Criar Assinatura"
echo "=============================================="
echo ""

# Criar backup do HTML
cp preview_assinatura_premium.html preview_assinatura_premium.html.backup_$(date +%Y%m%d_%H%M%S)
echo "✅ Backup criado!"

# Adicionar funcionalidade de criar assinatura
python3 << 'PYTHON_EOF'
import re

with open('preview_assinatura_premium.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Procurar pelo botão "Nova Assinatura"
if 'id="newSignatureBtn"' in content and 'onclick' not in re.search(r'id="newSignatureBtn"[^>]*>', content).group():
    # Adicionar onclick ao botão
    content = re.sub(
        r'(<button[^>]*id="newSignatureBtn"[^>]*)(>)',
        r'\1 onclick="openNewSignatureModal()"\2',
        content
    )
    
    # Adicionar modal antes do </body>
    modal_html = '''
    <!-- MODAL: CRIAR NOVA ASSINATURA -->
    <div id="newSignatureModal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 9999; align-items: center; justify-content: center;">
        <div style="background: white; border-radius: 20px; padding: 40px; max-width: 600px; width: 90%; max-height: 80vh; overflow-y: auto;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px;">
                <h2 style="margin: 0; font-size: 1.8rem; color: #1a1a2e;">✨ Nova Assinatura</h2>
                <button onclick="closeNewSignatureModal()" style="background: none; border: none; font-size: 2rem; cursor: pointer; color: #999;">×</button>
            </div>
            
            <form id="newSignatureForm" onsubmit="createNewSignature(event)">
                <div style="margin-bottom: 25px;">
                    <label style="display: block; font-weight: 600; margin-bottom: 8px; color: #374151;">Nome da Assinatura *</label>
                    <input type="text" id="newSigName" required 
                           style="width: 100%; padding: 12px; border: 2px solid #e5e7eb; border-radius: 10px; font-size: 1rem;"
                           placeholder="Ex: Assinatura Corporativa">
                </div>
                
                <div style="margin-bottom: 25px;">
                    <label style="display: block; font-weight: 600; margin-bottom: 8px; color: #374151;">Selecione um Template *</label>
                    <select id="newSigTemplate" required
                            style="width: 100%; padding: 12px; border: 2px solid #e5e7eb; border-radius: 10px; font-size: 1rem;">
                        <option value="">Carregando templates...</option>
                    </select>
                </div>
                
                <div style="margin-bottom: 25px;">
                    <label style="display: block; font-weight: 600; margin-bottom: 8px; color: #374151;">Informações Adicionais (Opcional)</label>
                    <textarea id="newSigNotes" rows="3"
                              style="width: 100%; padding: 12px; border: 2px solid #e5e7eb; border-radius: 10px; font-size: 1rem; resize: vertical;"
                              placeholder="Ex: Website, endereço, telefone secundário..."></textarea>
                    <small style="color: #6b7280; font-size: 0.85rem;">Adicione informações extras que aparecerão na assinatura</small>
                </div>
                
                <div style="display: flex; gap: 15px; margin-top: 30px;">
                    <button type="button" onclick="closeNewSignatureModal()" 
                            style="flex: 1; padding: 14px; border: 2px solid #e5e7eb; background: white; border-radius: 10px; font-weight: 600; cursor: pointer; color: #6b7280;">
                        Cancelar
                    </button>
                    <button type="submit" id="createSigBtn"
                            style="flex: 1; padding: 14px; border: none; background: linear-gradient(135deg, #667eea, #764ba2); color: white; border-radius: 10px; font-weight: 600; cursor: pointer;">
                        <span id="createSigText">Criar Assinatura</span>
                        <span id="createSigLoading" style="display: none;">⏳</span>
                    </button>
                </div>
            </form>
        </div>
    </div>

    <script>
        // Funções do modal
        function openNewSignatureModal() {
            document.getElementById('newSignatureModal').style.display = 'flex';
            loadTemplatesForModal();
        }

        function closeNewSignatureModal() {
            document.getElementById('newSignatureModal').style.display = 'none';
            document.getElementById('newSignatureForm').reset();
        }

        async function loadTemplatesForModal() {
            const select = document.getElementById('newSigTemplate');
            select.innerHTML = '<option value="">Carregando...</option>';
            
            try {
                const response = await fetch(`${API_BASE}/api/v1/signature-templates/`, {
                    headers: getHeaders()
                });
                
                if (!response.ok) throw new Error('Erro ao carregar templates');
                
                const templates = await response.json();
                
                if (templates.length === 0) {
                    select.innerHTML = '<option value="">Nenhum template disponível</option>';
                    return;
                }
                
                select.innerHTML = '<option value="">Selecione um template</option>';
                templates.forEach(template => {
                    const option = document.createElement('option');
                    option.value = template.id;
                    option.textContent = template.name;
                    if (template.is_default) {
                        option.textContent += ' (Padrão)';
                        option.selected = true;
                    }
                    select.appendChild(option);
                });
                
            } catch (error) {
                console.error('Erro ao carregar templates:', error);
                select.innerHTML = '<option value="">Erro ao carregar templates</option>';
            }
        }

        async function createNewSignature(event) {
            event.preventDefault();
            
            const btn = document.getElementById('createSigBtn');
            const btnText = document.getElementById('createSigText');
            const btnLoading = document.getElementById('createSigLoading');
            
            const name = document.getElementById('newSigName').value.trim();
            const templateId = document.getElementById('newSigTemplate').value;
            const notes = document.getElementById('newSigNotes').value.trim();
            
            if (!templateId) {
                alert('⚠️ Por favor, selecione um template');
                return;
            }
            
            // Desabilitar botão
            btn.disabled = true;
            btnText.style.display = 'none';
            btnLoading.style.display = 'inline';
            
            try {
                const customData = {};
                if (notes) {
                    // Tentar parsear como JSON ou usar como texto
                    try {
                        Object.assign(customData, JSON.parse(notes));
                    } catch {
                        customData.notes = notes;
                    }
                }
                
                const response = await fetch(`${API_BASE}/api/v1/signatures/`, {
                    method: 'POST',
                    headers: getHeaders(),
                    body: JSON.stringify({
                        name: name,
                        template_id: parseInt(templateId),
                        custom_data: customData
                    })
                });
                
                if (!response.ok) {
                    const error = await response.json();
                    throw new Error(error.detail || 'Erro ao criar assinatura');
                }
                
                alert('✅ Assinatura criada com sucesso!');
                closeNewSignatureModal();
                
                // Recarregar assinaturas
                mySignatures = [];
                loadSignatures();
                
                // Se estiver em outra aba, ir para "Minhas Assinaturas"
                document.querySelector('.nav-item[data-target="my-signatures"]').click();
                
            } catch (error) {
                console.error('Erro:', error);
                alert('❌ ' + error.message);
            } finally {
                btn.disabled = false;
                btnText.style.display = 'inline';
                btnLoading.style.display = 'none';
            }
        }
        
        // Fechar modal ao clicar fora
        document.getElementById('newSignatureModal')?.addEventListener('click', function(e) {
            if (e.target === this) {
                closeNewSignatureModal();
            }
        });
    </script>
'''
    
    content = content.replace('</body>', modal_html + '</body>')
    
    with open('preview_assinatura_premium.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Modal de criar assinatura adicionado!")
else:
    print("ℹ️ Modal já existe ou botão já tem onclick")
PYTHON_EOF

echo ""
echo "=============================================="
echo "✅ PASSO 3 CONCLUÍDO!"
echo "=============================================="
echo ""
echo "👉 Execute este script com:"
echo "   bash 03_adicionar_criar_assinatura.sh"
