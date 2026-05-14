import logging

from database import db
from models.category import Category
from models.task import Task

log = logging.getLogger(__name__)


class CategoryNotFoundError(Exception):
    pass


def list_categories() -> list[dict]:
    cats = db.session.query(Category).all()
    result = []
    for c in cats:
        d = c.to_dict()
        d['task_count'] = db.session.query(Task).filter_by(category_id=c.id).count()
        result.append(d)
    return result


def create_category(payload: dict) -> dict:
    cat = Category(
        name=payload['name'],
        description=payload.get('description', ''),
        color=payload.get('color', '#000000'),
    )
    db.session.add(cat)
    db.session.commit()
    log.info('category.created', extra={'category_id': cat.id})
    return cat.to_dict()


def update_category(category_id: int, payload: dict) -> dict:
    cat = db.session.get(Category, category_id)
    if not cat:
        raise CategoryNotFoundError('Categoria não encontrada')
    for field in ('name', 'description', 'color'):
        if field in payload:
            setattr(cat, field, payload[field])
    db.session.commit()
    return cat.to_dict()


def delete_category(category_id: int) -> None:
    cat = db.session.get(Category, category_id)
    if not cat:
        raise CategoryNotFoundError('Categoria não encontrada')
    db.session.delete(cat)
    db.session.commit()
    log.info('category.deleted', extra={'category_id': category_id})
