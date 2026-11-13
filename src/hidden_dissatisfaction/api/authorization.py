"""HTTP authorization policies shared by protected endpoints."""

from fastapi import HTTPException, status

from hidden_dissatisfaction.domain.auth import Role, User


def require_manager(user: User) -> User:
    """Return a Manager or raise the API Contract's standard forbidden error."""
    if user.role is not Role.MANAGER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Manager role is required", "details": None},
        )
    return user
