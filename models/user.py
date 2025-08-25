# models/user.py

from dataclasses import dataclass

@dataclass
class User:
    """
    Simple User model to represent authenticated users.
    """
    user_id: int
    username: str
    role: str
