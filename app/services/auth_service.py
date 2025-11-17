from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime
import redis

from app.db.models import User, Organization, UserRole, UserStatus, SignatureTemplate, Signature
from app.schemas.user import UserCreate, UserLogin, TokenResponse
from app.services.security import hash_password, verify_password, create_access_token, create_refresh_token


def register_user(db: Session, user_create: UserCreate) -> TokenResponse:
    """Register a new user and create organization with default signature"""
    
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_create.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if organization slug already exists
    existing_org = db.query(Organization).filter(
        Organization.slug == user_create.organization_slug
    ).first()
    if existing_org:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization slug already taken"
        )
    
    # Create organization
    organization = Organization(
        name=user_create.organization_name,
        slug=user_create.organization_slug
    )
    db.add(organization)
    db.flush()
    
    # Create user (owner) — agora salvando phone, job_title e avatar_url
    hashed_pwd = hash_password(user_create.password)
    user = User(
        organization_id=organization.id,
        email=user_create.email,
        full_name=user_create.full_name,
        hashed_password=hashed_pwd,
        role=UserRole.OWNER,
        status=UserStatus.ACTIVE,
        phone=user_create.phone,           # telefone principal (phone1)
        job_title=user_create.job_title,   # cargo
        avatar_url=user_create.avatar_url  # foto, se tiver
    )
    db.add(user)
    db.flush()
    
    # Create default signature template for organization
    default_template = SignatureTemplate(
        organization_id=organization.id,
        name="Template Padrão",
        description="Template de assinatura criado automaticamente",
        html_template="""
<table style="font-family: Arial, sans-serif; font-size: 14px; color: #333; border-collapse: collapse;">
    <tr>
        <td style="padding-right: 20px; vertical-align: top;">
            {% if avatar_url %}
            <img src="{{ avatar_url }}" alt="{{ full_name }}" style="width: 80px; height: 80px; border-radius: 50%; object-fit: cover; border: 3px solid #667eea;">
            {% else %}
            <div style="width: 80px; height: 80px; border-radius: 50%; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); display: flex; align-items: center; justify-content: center; color: white; font-size: 32px; font-weight: bold;">
                {{ full_name[0] }}
            </div>
            {% endif %}
        </td>
        <td style="vertical-align: top; border-left: 3px solid #667eea; padding-left: 20px;">
            <div style="font-weight: bold; font-size: 18px; color: #667eea; margin-bottom: 5px;">
                {{ full_name }}
            </div>
            {% if job_title %}
            <div style="font-style: italic; color: #666; margin-bottom: 10px; font-size: 13px;">
                {{ job_title }}
            </div>
            {% endif %}
            {% if email %}
            <div style="margin-bottom: 5px;">
                <span style="color: #667eea;">📧</span> 
                <a href="mailto:{{ email }}" style="color: #667eea; text-decoration: none;">{{ email }}</a>
            </div>
            {% endif %}
            {% if phone %}
            <div style="margin-bottom: 5px;">
                <span style="color: #667eea;">📱</span> 
                <span style="color: #666;">{{ phone }}</span>
            </div>
            {% endif %}

            {% if phone2 %}
            <div style="margin-bottom: 5px;">
                <span style="color: #667eea;">📞</span> 
                <span style="color: #666;">{{ phone2 }}</span>
            </div>
            {% endif %}

            {% if website %}
            <div style="margin-bottom: 5px;">
                <span style="color: #667eea;">🌐</span> 
                <a href="{{ website }}" style="color: #667eea; text-decoration: none;" target="_blank">{{ website }}</a>
            </div>
            {% endif %}

            {% if address %}
            <div style="margin-bottom: 5px; color:#666;">
                <span style="color: #667eea;">📍</span> {{ address }}
            </div>
            {% endif %}

            {% if facebook or instagram or linkedin or twitter %}
            <div style="margin-top: 10px; font-size: 12px; color:#666;">
                {% if facebook %}
                    <div>Facebook: <a href="{{ facebook }}" style="color:#667eea;" target="_blank">{{ facebook }}</a></div>
                {% endif %}
                {% if instagram %}
                    <div>Instagram: <a href="{{ instagram }}" style="color:#667eea;" target="_blank">{{ instagram }}</a></div>
                {% endif %}
                {% if linkedin %}
                    <div>LinkedIn: <a href="{{ linkedin }}" style="color:#667eea;" target="_blank">{{ linkedin }}</a></div>
                {% endif %}
                {% if twitter %}
                    <div>Twitter: <a href="{{ twitter }}" style="color:#667eea;" target="_blank">{{ twitter }}</a></div>
                {% endif %}
            </div>
            {% endif %}

            {% if organization_name %}
            <div style="margin-top: 15px; padding-top: 10px; border-top: 1px solid #ddd;">
                <strong style="color: #333;">{{ organization_name }}</strong>
                {% if organization_logo %}
                <br><img src="{{ organization_logo }}" alt="{{ organization_name }}" style="max-width: 150px; margin-top: 10px;">
                {% endif %}
            </div>
            {% endif %}
        </td>
    </tr>
</table>
        """,
        variables=[
            "full_name",
            "email",
            "phone",
            "job_title",
            "avatar_url",
            "organization_name",
            "organization_logo",
            "phone2",
            "website",
            "address",
            "facebook",
            "twitter",
            "instagram",
            "linkedin",
        ],
        is_default=True,
        is_active=True
    )
    db.add(default_template)
    db.flush()
    
    # Create default signature for user using Jinja2
    from jinja2 import Template
    
    custom = user_create.custom_data or {}

    context = {
        "full_name": user.full_name,
        "email": user.email,
        "phone": user.phone or "",
        "job_title": user.job_title or "",
        "avatar_url": user.avatar_url or "",
        "organization_name": organization.name,
        "organization_logo": custom.get("logo_url") or organization.logo_url or "",
        "phone2": custom.get("phone2", ""),
        "website": custom.get("website", ""),
        "address": custom.get("address", ""),
        "facebook": custom.get("facebook", ""),
        "twitter": custom.get("twitter", ""),
        "instagram": custom.get("instagram", ""),
        "linkedin": custom.get("linkedin", ""),
    }
    
    template_obj = Template(default_template.html_template)
    html_content = template_obj.render(**context)
    
    default_signature = Signature(
        user_id=user.id,
        template_id=default_template.id,
        name="Minha Assinatura Principal",
        custom_data=user_create.custom_data or {},
        html_content=html_content,
        is_active=True
    )
    db.add(default_signature)
    
    db.commit()
    db.refresh(user)
    
    # Generate tokens
    access_token = create_access_token(
        data={"sub": str(user.id), "org_id": organization.id, "role": user.role.value}
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id)}
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=1800  # 30 minutes
    )


def login_user(db: Session, user_login: UserLogin) -> TokenResponse:
    """Authenticate user and return tokens"""
    
    # Find user
    user = db.query(User).filter(User.email == user_login.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Verify password
    if not verify_password(user_login.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Check if user is active
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active"
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Generate tokens
    access_token = create_access_token(
        data={"sub": str(user.id), "org_id": user.organization_id, "role": user.role.value}
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id)}
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=1800  # 30 minutes
    )


def invalidate_token(redis_client: redis.Redis, token: str, exp: datetime):
    """Add token to blacklist"""
    ttl = int((exp - datetime.utcnow()).total_seconds())
    if ttl > 0:
        redis_client.setex(f"blacklist:{token}", ttl, "1")


def is_token_blacklisted(redis_client: redis.Redis, token: str) -> bool:
    """Check if token is blacklisted"""
    return redis_client.exists(f"blacklist:{token}") > 0
