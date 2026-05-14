import logging
from datetime import datetime, timedelta, timezone

import jwt

from config.settings import settings
from database import db
from models.user import User

log = logging.getLogger(__name__)


class InvalidCredentialsError(Exception):
    pass


class InactiveUserError(Exception):
    pass


def login(email: str, password: str) -> dict:
    user = db.session.query(User).filter_by(email=email).first()
    if not user or not user.check_password(password):
        raise InvalidCredentialsError('Credenciais inválidas')
    if not user.active:
        raise InactiveUserError('Usuário inativo')

    now = datetime.now(timezone.utc)
    payload = {
        'sub': str(user.id),
        'role': user.role,
        'iat': int(now.timestamp()),
        'exp': int((now + timedelta(minutes=settings.JWT_EXPIRES_MINUTES)).timestamp()),
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

    log.info('auth.login.success', extra={'user_id': user.id})
    return {
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': token,
        'expires_in': settings.JWT_EXPIRES_MINUTES * 60,
    }
