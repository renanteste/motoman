from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from src.mrb.common.security.auth_service import AuthService
from src.mrb.comercial.models.model_vendedores import vendedores_sa3

# from src.mrb.common.email.email_service import EmailService


def autentica_representante_app(
    db: Session, id_usuario: str, ponto_acesso: str
) -> AuthService:
    # Valida se tem acesso
    auth_service = AuthService(db)
    if not auth_service.valida_acesso(id_usuario, ponto_acesso):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Sem acesso ao endpoint '{ponto_acesso}'!",
        )

    # Valida se é representante
    if not auth_service.dados_usuario.dados_representante:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não está cadastrado como representante!",
        )

    return auth_service
