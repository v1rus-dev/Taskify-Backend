from enum import Enum


class TaskCategory(str, Enum):
    """Категории задач."""
    WORK = "work"
    PERSONAL = "personal"
    SHOPPING = "shopping"
    HEALTH = "health"
    OTHER = "other"
