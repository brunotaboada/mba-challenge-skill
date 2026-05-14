import logging

from sqlalchemy.orm import joinedload

from database import db
from models.task import Task
from models.user import User

log = logging.getLogger(__name__)


class UserNotFoundError(Exception):
    pass


class EmailAlreadyUsedError(Exception):
    pass


def list_users() -> list[dict]:
    users = db.session.query(User).options(joinedload(User.tasks)).all()
    result = []
    for u in users:
        data = u.to_dict()
        data['task_count'] = len(u.tasks)
        result.append(data)
    return result


def get_user(user_id: int) -> dict:
    user = db.session.get(User, user_id)
    if not user:
        raise UserNotFoundError('Usuário não encontrado')
    data = user.to_dict()
    tasks = db.session.query(Task).filter_by(user_id=user_id).all()
    data['tasks'] = [t.to_dict() for t in tasks]
    return data


def create_user(payload: dict) -> dict:
    if db.session.query(User).filter_by(email=payload['email']).first():
        raise EmailAlreadyUsedError('Email já cadastrado')
    user = User(
        name=payload['name'],
        email=payload['email'],
        role=payload.get('role', 'user'),
    )
    user.set_password(payload['password'])
    db.session.add(user)
    db.session.commit()
    log.info('user.created', extra={'user_id': user.id})
    return user.to_dict()


def update_user(user_id: int, payload: dict) -> dict:
    user = db.session.get(User, user_id)
    if not user:
        raise UserNotFoundError('Usuário não encontrado')

    if 'email' in payload:
        existing = db.session.query(User).filter_by(email=payload['email']).first()
        if existing and existing.id != user_id:
            raise EmailAlreadyUsedError('Email já cadastrado')
        user.email = payload['email']

    for field in ('name', 'role', 'active'):
        if field in payload:
            setattr(user, field, payload[field])
    if 'password' in payload:
        user.set_password(payload['password'])

    db.session.commit()
    log.info('user.updated', extra={'user_id': user.id})
    return user.to_dict()


def delete_user(user_id: int) -> None:
    user = db.session.get(User, user_id)
    if not user:
        raise UserNotFoundError('Usuário não encontrado')
    tasks = db.session.query(Task).filter_by(user_id=user_id).all()
    for t in tasks:
        db.session.delete(t)
    db.session.delete(user)
    db.session.commit()
    log.info('user.deleted', extra={'user_id': user_id})


def get_user_tasks(user_id: int) -> list[dict]:
    user = db.session.get(User, user_id)
    if not user:
        raise UserNotFoundError('Usuário não encontrado')
    tasks = db.session.query(Task).filter_by(user_id=user_id).all()
    return [t.to_dict() for t in tasks]
