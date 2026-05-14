"""Helpers puros. Validação e regra de negócio moveram-se para `schemas/`
e `services/` respectivamente."""
import re
from datetime import datetime
from typing import Optional

EMAIL_RE = re.compile(r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


def format_date(value: Optional[datetime]) -> Optional[str]:
    return str(value) if value else None


def calculate_percentage(part: float, total: float) -> float:
    if total == 0:
        return 0
    return round((part / total) * 100, 2)


def validate_email(email: str) -> bool:
    return bool(EMAIL_RE.match(email or ''))


def parse_date(value: str) -> Optional[datetime]:
    for fmt in ('%Y-%m-%d', '%d/%m/%Y'):
        try:
            return datetime.strptime(value, fmt)
        except (ValueError, TypeError):
            continue
    return None


def is_valid_color(color: str) -> bool:
    return bool(color) and len(color) == 7 and color.startswith('#')
