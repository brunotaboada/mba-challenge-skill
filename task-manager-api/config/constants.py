from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    CANCELLED = "cancelled"

    @classmethod
    def values(cls) -> list[str]:
        return [item.value for item in cls]


class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    MANAGER = "manager"

    @classmethod
    def values(cls) -> list[str]:
        return [item.value for item in cls]


PRIORITY_MIN = 1
PRIORITY_MAX = 5
TITLE_MIN_LEN = 3
TITLE_MAX_LEN = 200
PASSWORD_MIN_LEN = 8
