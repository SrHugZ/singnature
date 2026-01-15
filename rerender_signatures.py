#!/usr/bin/env python3
"""
Script para re-renderizar todas as assinaturas existentes
Útil após atualizar o template ou adicionar novos campos
"""

import sys
from sqlalchemy.orm import Session

# Adicionar o diretório do app ao path
sys.path.insert(0, '/app')

from app.db.session import SessionLocal
from app.db.models import Signature, User, SignatureTemplate
from app.services.signature_service import signature_service


def rerender_all_signatures():
    """Re-renderiza todas as assinaturas com os dados atualizados"""

    db: Session = SessionLocal()

    try:
        # Buscar todas as assinaturas
        signatures = db.query(Signature).all()

        print(f"📋 Encontradas {len(signatures)} assinaturas para re-renderizar")

        updated_count = 0
        error_count = 0

        for signature in signatures:
            try:
                # Buscar usuário e template
                user = db.query(User).filter(User.id == signature.user_id).first()
                template = db.query(SignatureTemplate).filter(
                    SignatureTemplate.id == signature.template_id
                ).first()

                if not user:
                    print(f"⚠️  Assinatura {signature.id}: Usuário não encontrado")
                    error_count += 1
                    continue

                if not template:
                    print(f"⚠️  Assinatura {signature.id}: Template não encontrado")
                    error_count += 1
                    continue

                # Re-renderizar HTML
                old_html = signature.html_content
                new_html = signature_service.render_signature(
                    template=template,
                    user=user,
                    custom_data=signature.custom_data
                )

                # Atualizar HTML se mudou
                if old_html != new_html:
                    signature.html_content = new_html
                    updated_count += 1
                    print(f"✅ Assinatura {signature.id} ('{signature.name}') - Atualizada")
                else:
                    print(f"⏭️  Assinatura {signature.id} ('{signature.name}') - Sem alterações")

            except Exception as e:
                print(f"❌ Erro ao processar assinatura {signature.id}: {e}")
                error_count += 1
                continue

        # Commit todas as mudanças
        if updated_count > 0:
            db.commit()
            print(f"\n🎉 Concluído!")
            print(f"   ✅ {updated_count} assinaturas atualizadas")
            print(f"   ⏭️  {len(signatures) - updated_count - error_count} sem alterações")
            if error_count > 0:
                print(f"   ❌ {error_count} erros")
        else:
            print(f"\n✅ Nenhuma assinatura precisou ser atualizada")

    except Exception as e:
        print(f"❌ Erro geral: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    print("🔄 Iniciando re-renderização de assinaturas...\n")
    rerender_all_signatures()
