import http
from functools import wraps
from typing import Callable, Optional, List, Dict

from flask import abort, g

from .enums import UserRole


def login_required(fn: Callable):
    """Check is user authenticated"""

    def wrapper(fn: Callable) -> Callable:
        @wraps(fn)
        def decorated_view(*args: List, **kwargs: Dict) -> Optional[Callable]:
            if not g.current_user:
                abort(http.HTTPStatus.UNAUTHORIZED)
            return fn(*args, **kwargs)

        return decorated_view

    return wrapper(fn)


def role_required(*roles: UserRole) -> Callable:
    """Decorator For Roles"""

    roles_ = [role.value for role in roles]

    def wrapper(fn: Callable) -> Callable:
        @wraps(fn)
        def decorated_view(*args: List, **kwargs: Dict) -> Optional[Callable]:
            if not hasattr(g.current_user, "role"):
                abort(
                    http.HTTPStatus.FORBIDDEN,
                )

            if g.current_user.role not in roles_:
                abort(
                    http.HTTPStatus.FORBIDDEN,
                )

            return fn(*args, **kwargs)

        return decorated_view

    return wrapper
