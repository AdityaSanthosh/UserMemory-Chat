import uuid
from datetime import datetime
from typing import Optional


class User:
    def __init__(
        self,
        username: str,
        hashed_password: str,
        id: Optional[str] = None,
        created_at: Optional[datetime] = None,
    ):
        self.id = id if id else str(uuid.uuid4())
        self.username = username
        self.hashed_password = hashed_password
        self.created_at = created_at if created_at else datetime.now()

    def __str__(self) -> str:
        return f"<User {self.username}>"
