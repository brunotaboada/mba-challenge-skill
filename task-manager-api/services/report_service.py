from collections import defaultdict
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import joinedload

from database import db
from models.category import Category
from models.task import Task
from models.user import User


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def summary_report() -> dict:
    total_tasks = db.session.query(Task).count()
    total_users = db.session.query(User).count()
    total_categories = db.session.query(Category).count()

    status_counts = defaultdict(int)
    priority_counts = defaultdict(int)
    overdue = []

    tasks = db.session.query(Task).all()
    for t in tasks:
        status_counts[t.status] += 1
        priority_counts[t.priority] += 1
        if t.is_overdue():
            overdue.append({
                'id': t.id,
                'title': t.title,
                'due_date': str(t.due_date),
                'days_overdue': (_now() - t.due_date.replace(tzinfo=None)).days,
            })

    seven_days_ago = _now() - timedelta(days=7)
    recent_tasks = (
        db.session.query(Task).filter(Task.created_at >= seven_days_ago).count()
    )
    recent_done = (
        db.session.query(Task)
        .filter(Task.status == 'done', Task.updated_at >= seven_days_ago)
        .count()
    )

    # Eager-load tasks; sem N+1
    users = db.session.query(User).options(joinedload(User.tasks)).all()
    user_stats = []
    for u in users:
        total = len(u.tasks)
        completed = sum(1 for t in u.tasks if t.status == 'done')
        user_stats.append({
            'user_id': u.id,
            'user_name': u.name,
            'total_tasks': total,
            'completed_tasks': completed,
            'completion_rate': round((completed / total) * 100, 2) if total > 0 else 0,
        })

    return {
        'generated_at': str(datetime.now(timezone.utc)),
        'overview': {
            'total_tasks': total_tasks,
            'total_users': total_users,
            'total_categories': total_categories,
        },
        'tasks_by_status': {
            'pending': status_counts.get('pending', 0),
            'in_progress': status_counts.get('in_progress', 0),
            'done': status_counts.get('done', 0),
            'cancelled': status_counts.get('cancelled', 0),
        },
        'tasks_by_priority': {
            'critical': priority_counts.get(1, 0),
            'high': priority_counts.get(2, 0),
            'medium': priority_counts.get(3, 0),
            'low': priority_counts.get(4, 0),
            'minimal': priority_counts.get(5, 0),
        },
        'overdue': {'count': len(overdue), 'tasks': overdue},
        'recent_activity': {
            'tasks_created_last_7_days': recent_tasks,
            'tasks_completed_last_7_days': recent_done,
        },
        'user_productivity': user_stats,
    }


def user_report(user_id: int) -> dict | None:
    user = db.session.get(User, user_id)
    if not user:
        return None
    tasks = db.session.query(Task).filter_by(user_id=user_id).all()
    stats = {'done': 0, 'pending': 0, 'in_progress': 0, 'cancelled': 0,
             'overdue': 0, 'high_priority': 0}
    for t in tasks:
        if t.status in stats:
            stats[t.status] += 1
        if t.priority <= 2:
            stats['high_priority'] += 1
        if t.is_overdue():
            stats['overdue'] += 1
    total = len(tasks)
    return {
        'user': {'id': user.id, 'name': user.name, 'email': user.email},
        'statistics': {
            'total_tasks': total,
            **stats,
            'completion_rate': round((stats['done'] / total) * 100, 2) if total else 0,
        },
    }
