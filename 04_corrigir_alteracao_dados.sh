#!/bin/bash

echo "🔧 PASSO 4: Corrigindo Alteração de Dados"
echo "========================================="
echo ""

# Corrigir o endpoint de atualização de usuário
python3 << 'PYTHON_EOF'
# Ler o arquivo atual
with open('preview_assinatura_premium.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Procurar e substituir o endpoint incorreto
old_endpoint = "fetch(`${API_BASE}/api/v1/members/${currentUserData.id}`"
new_endpoint = "fetch(`${API_BASE}/api/v1/users/me`"

if old_endpoint in content:
    content = content.replace(old_endpoint, new_endpoint)
    content = content.replace("method: 'PATCH'", "method: 'PUT'")
    
    with open('preview_assinatura_premium.html', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Endpoint de atualização corrigido!")
else:
    print("ℹ️ Endpoint já estava correto")
PYTHON_EOF

echo ""

# Criar o endpoint correto no backend
cat > app/api/v1/users.py << 'EOF'
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User
from app.schemas.user import UserUpdate, UserResponse
from app.api.deps import get_current_user

router = APIRouter()


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """Obter informações do usuário atual"""
    return current_user


@router.put("/me", response_model=UserResponse)
def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Atualizar informações do usuário atual"""
    
    # Atualizar campos permitidos
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    
    if user_update.phone is not None:
        current_user.phone = user_update.phone
    
    if user_update.job_title is not None:
        current_user.job_title = user_update.job_title
    
    if user_update.avatar_url is not None:
        current_user.avatar_url = user_update.avatar_url
    
    try:
        db.commit()
        db.refresh(current_user)
        return current_user
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar usuário: {str(e)}"
        )
EOF

echo "✅ Endpoint /users/me criado!"
echo ""

# Atualizar main.py
python3 << 'PYTHON_EOF'
with open('app/main.py', 'r') as f:
    content = f.read()

# Adicionar import se não existir
if 'users' not in content:
    content = content.replace(
        'from app.api.v1 import auth, organizations, members, signature_templates, signatures, banners, analytics, uploads',
        'from app.api.v1 import auth, organizations, members, signature_templates, signatures, banners, analytics, uploads, users'
    )
    
    # Adicionar router
    content = content.replace(
        'app.include_router(uploads.router',
        '''app.include_router(users.router, prefix=f"{settings.API_V1_STR}/users", tags=["users"])
app.include_router(uploads.router'''
    )
    
    with open('app/main.py', 'w') as f:
        f.write(content)
    
    print("✅ main.py atualizado!")
else:
    print("ℹ️ main.py já contém users")
PYTHON_EOF

echo ""
echo "🔄 Reiniciando API..."
sudo docker-compose restart api

echo ""
echo "⏳ Aguardando API (15 segundos)..."
sleep 15

echo ""
echo "🧪 Testando API..."
curl -s https://signature.thebroker.vip/health | python3 -m json.tool

echo ""
echo "========================================="
echo "✅ PASSO 4 CONCLUÍDO!"
echo "========================================="
echo ""
echo "👉 Execute: bash 04_corrigir_alteracao_dados.sh"
