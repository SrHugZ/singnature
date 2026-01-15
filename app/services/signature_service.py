from jinja2 import Template
from sqlalchemy.orm import Session
from typing import Dict, Any
from premailer import transform

from app.db.models import SignatureTemplate, Signature, User


class SignatureService:
    """Serviço de renderização de assinaturas"""
    
    def render_signature(
        self,
        template: SignatureTemplate,
        user: User,
        custom_data: Dict[str, Any] = None
    ) -> str:
        """
        Renderiza uma assinatura baseada no template e dados do usuário
        """
        # Preparar contexto com dados do usuário
        context = {
            "full_name": user.full_name,
            "email": user.email,
            "phone": user.phone or "",
            "job_title": user.job_title or "",
            "avatar_url": user.avatar_url or "",
            "organization_name": user.organization.name if user.organization else "",
            "organization_logo": user.organization.logo_url if user.organization else "",
            "department": user.department.name if user.department else "",
        }

        # Adicionar dados do custom_data do usuário (phone2, website, address, redes sociais)
        if user.custom_data:
            context.update(user.custom_data)

        # Adicionar dados customizados da assinatura (sobrescreve os do usuário se houver)
        if custom_data:
            context.update(custom_data)
        
        # Renderizar template HTML
        template_obj = Template(template.html_template)
        html_content = template_obj.render(**context)
        
        # Inline CSS (para compatibilidade com email clients)
        if template.css_styles:
            full_html = f"<style>{template.css_styles}</style>{html_content}"
            html_content = transform(full_html)
        
        return html_content
    
    def create_signature_from_template(
        self,
        db: Session,
        user: User,
        template: SignatureTemplate,
        name: str,
        custom_data: Dict[str, Any] = None
    ) -> Signature:
        """Criar uma nova assinatura baseada em um template"""
        
        # Renderizar HTML
        html_content = self.render_signature(template, user, custom_data)
        
        # Criar assinatura
        signature = Signature(
            user_id=user.id,
            template_id=template.id,
            name=name,
            custom_data=custom_data,
            html_content=html_content,
            is_active=True
        )
        
        db.add(signature)
        db.commit()
        db.refresh(signature)
        
        return signature
    
    def update_signature(
        self,
        db: Session,
        signature: Signature,
        user: User,
        template: SignatureTemplate = None,
        custom_data: Dict[str, Any] = None
    ) -> Signature:
        """Atualizar uma assinatura existente"""
        
        if template:
            signature.template_id = template.id
        
        if custom_data:
            signature.custom_data = custom_data
        
        # Re-renderizar HTML
        current_template = template or signature.template
        signature.html_content = self.render_signature(
            current_template,
            user,
            signature.custom_data
        )
        
        db.commit()
        db.refresh(signature)
        
        return signature


# Instância global do serviço
signature_service = SignatureService()
