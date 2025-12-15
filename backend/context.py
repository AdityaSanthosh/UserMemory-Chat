"""
Context management for tracking the current user across async operations.

This module provides a ContextVar to store the current user_id, allowing
tools and services to access user context without explicit parameter passing.
"""

from contextvars import ContextVar
from typing import Optional

# Context variable to store the current user ID
user_id_context: ContextVar[Optional[str]] = ContextVar("user_id", default=None)


def get_current_user_id() -> str:
    """
    Get the current user ID from context.

    Returns:
        str: The current user ID

    Raises:
        ValueError: If no user context is set
    """
    user_id = user_id_context.get()
    if not user_id:
        raise ValueError(
            "No user context set. Ensure user_id_context is set before calling this function."
        )
    return user_id


def set_current_user_id(user_id: str) -> None:
    """
    Set the current user ID in context.

    Args:
        user_id: The user ID to set in context
    """
    user_id_context.set(user_id)


def clear_current_user_id() -> None:
    """
    Clear the current user ID from context.
    """
    user_id_context.set(None)
