from datetime import datetime, timezone

from database import db


def _utcnow():
    return datetime.now(timezone.utc)


class Task(db.Model):
    __tablename__ = 'tasks'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='pending')
    priority = db.Column(db.Integer, default=3)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=_utcnow)
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)
    due_date = db.Column(db.DateTime, nullable=True)
    tags = db.Column(db.String(500), nullable=True)

    user = db.relationship('User', backref='tasks')
    category = db.relationship('Category', backref='tasks')

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'user_id': self.user_id,
            'category_id': self.category_id,
            'created_at': str(self.created_at),
            'updated_at': str(self.updated_at),
            'due_date': str(self.due_date) if self.due_date else None,
            'tags': self.tags.split(',') if self.tags else [],
            'overdue': self.is_overdue(),
        }

    def is_overdue(self) -> bool:
        if not self.due_date:
            return False
        if self.status in ('done', 'cancelled'):
            return False
        # SQLite armazena datetime sem tz; comparamos naive contra naive UTC.
        now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
        due_naive = self.due_date.replace(tzinfo=None) if self.due_date.tzinfo else self.due_date
        return due_naive < now_naive
