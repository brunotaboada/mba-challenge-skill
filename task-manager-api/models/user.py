from datetime import datetime, timezone

import bcrypt

from database import db


def _utcnow():
    return datetime.now(timezone.utc)


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='user')
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=_utcnow)

    def to_dict(self) -> dict:
        """Public serialization. Senha NUNCA é retornada."""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at),
        }

    def set_password(self, pwd: str) -> None:
        self.password = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()

    def check_password(self, pwd: str) -> bool:
        try:
            return bcrypt.checkpw(pwd.encode(), self.password.encode())
        except (ValueError, TypeError):
            return False

    def is_admin(self) -> bool:
        return self.role == 'admin'
