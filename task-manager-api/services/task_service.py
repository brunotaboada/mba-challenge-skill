import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import joinedload

from database import db
from models.category import Category
from models.task import Task
from models.user import User

log = logging.getLogger(__name__)


class TaskNotFoundError(Exception):
    pass


class RelatedNotFoundError(Exception):
    pass


def _serialize_with_relations(task: Task) -> dict:
    data = task.to_dict()
    data['user_name'] = task.user.name if task.user else None
    data['category_name'] = task.category.name if task.category else None
    return data


def list_tasks() -> list[dict]:
    tasks = (
        db.session.query(Task)
        .options(joinedload(Task.user), joinedload(Task.category))
        .all()
    )
    return [_serialize_with_relations(t) for t in tasks]


def get_task(task_id: int) -> dict:
    task = (
        db.session.query(Task)
        .options(joinedload(Task.user), joinedload(Task.category))
        .filter(Task.id == task_id)
        .first()
    )
    if not task:
        raise TaskNotFoundError(f'Task {task_id} não encontrada')
    return _serialize_with_relations(task)


def _check_related(user_id: Optional[int], category_id: Optional[int]) -> None:
    if user_id and not db.session.get(User, user_id):
        raise RelatedNotFoundError('Usuário não encontrado')
    if category_id and not db.session.get(Category, category_id):
        raise RelatedNotFoundError('Categoria não encontrada')


def _normalize_tags(tags) -> Optional[str]:
    if tags is None:
        return None
    if isinstance(tags, list):
        return ','.join(str(t) for t in tags)
    return str(tags)


def _due_date_to_dt(value):
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    return datetime.combine(value, datetime.min.time())


def create_task(payload: dict) -> dict:
    _check_related(payload.get('user_id'), payload.get('category_id'))
    task = Task(
        title=payload['title'],
        description=payload.get('description', ''),
        status=payload.get('status', 'pending'),
        priority=payload.get('priority', 3),
        user_id=payload.get('user_id'),
        category_id=payload.get('category_id'),
        due_date=_due_date_to_dt(payload.get('due_date')),
        tags=_normalize_tags(payload.get('tags')),
    )
    db.session.add(task)
    db.session.commit()
    log.info('task.created', extra={'task_id': task.id})
    return _serialize_with_relations(task)


def update_task(task_id: int, payload: dict) -> dict:
    task = db.session.get(Task, task_id)
    if not task:
        raise TaskNotFoundError(f'Task {task_id} não encontrada')

    if 'user_id' in payload or 'category_id' in payload:
        _check_related(payload.get('user_id'), payload.get('category_id'))

    for field in ('title', 'description', 'status', 'priority', 'user_id', 'category_id'):
        if field in payload:
            setattr(task, field, payload[field])
    if 'due_date' in payload:
        task.due_date = _due_date_to_dt(payload['due_date'])
    if 'tags' in payload:
        task.tags = _normalize_tags(payload['tags'])
    task.updated_at = datetime.now(timezone.utc)

    db.session.commit()
    log.info('task.updated', extra={'task_id': task.id})
    return _serialize_with_relations(task)


def delete_task(task_id: int) -> None:
    task = db.session.get(Task, task_id)
    if not task:
        raise TaskNotFoundError(f'Task {task_id} não encontrada')
    db.session.delete(task)
    db.session.commit()
    log.info('task.deleted', extra={'task_id': task_id})


def search_tasks(q: str, status: str, priority: str, user_id: str) -> list[dict]:
    query = (
        db.session.query(Task)
        .options(joinedload(Task.user), joinedload(Task.category))
    )
    if q:
        like = f'%{q}%'
        query = query.filter(db.or_(Task.title.like(like), Task.description.like(like)))
    if status:
        query = query.filter(Task.status == status)
    if priority:
        try:
            query = query.filter(Task.priority == int(priority))
        except ValueError as exc:
            raise RelatedNotFoundError('priority deve ser numérico') from exc
    if user_id:
        try:
            query = query.filter(Task.user_id == int(user_id))
        except ValueError as exc:
            raise RelatedNotFoundError('user_id deve ser numérico') from exc
    return [_serialize_with_relations(t) for t in query.all()]


def task_stats() -> dict:
    base = db.session.query
    total = base(Task).count()
    pending = base(Task).filter_by(status='pending').count()
    in_progress = base(Task).filter_by(status='in_progress').count()
    done = base(Task).filter_by(status='done').count()
    cancelled = base(Task).filter_by(status='cancelled').count()

    overdue_count = sum(
        1
        for t in db.session.query(Task).all()
        if t.is_overdue()
    )
    return {
        'total': total,
        'pending': pending,
        'in_progress': in_progress,
        'done': done,
        'cancelled': cancelled,
        'overdue': overdue_count,
        'completion_rate': round((done / total) * 100, 2) if total > 0 else 0,
    }
