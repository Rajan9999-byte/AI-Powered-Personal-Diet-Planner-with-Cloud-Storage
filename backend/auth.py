from __future__ import annotations

from functools import wraps
from typing import Callable, Any

from flask import g, jsonify, session


def current_user_id() -> str | None:
    return session.get("user_id")


def login_required(view: Callable[..., Any]):
    @wraps(view)
    def wrapped(*args, **kwargs):
        user_id = current_user_id()
        if not user_id:
            return jsonify({"error": "Authentication required."}), 401
        g.user_id = user_id
        return view(*args, **kwargs)

    return wrapped
