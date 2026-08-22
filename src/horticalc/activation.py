from __future__ import annotations

import secrets
import threading
from collections.abc import Callable
from typing import Any


class InvalidActivationToken(Exception):
    pass


class ActivationUnavailable(Exception):
    pass


_state_lock = threading.RLock()
_activation_token: str | None = None
_activation_handler: Callable[[Any], bool] | None = None
_activation_target: Any = None


def configure_activation_token(token: str) -> None:
    global _activation_token
    with _state_lock:
        _activation_token = token


def activation_token_configured() -> bool:
    with _state_lock:
        return _activation_token is not None


def validate_activation_token(token: str) -> bool:
    with _state_lock:
        expected_token = _activation_token
    return expected_token is not None and secrets.compare_digest(token, expected_token)


def configure_activation_handler(handler: Callable[[Any], bool], target: Any) -> None:
    global _activation_handler, _activation_target
    with _state_lock:
        _activation_handler = handler
        _activation_target = target


def clear_activation_handler() -> None:
    global _activation_token, _activation_handler, _activation_target
    with _state_lock:
        _activation_token = None
        _activation_handler = None
        _activation_target = None


def request_activation(token: str) -> None:
    with _state_lock:
        handler = _activation_handler
        target = _activation_target
    if not validate_activation_token(token):
        raise InvalidActivationToken
    if handler is None or target is None or not handler(target):
        raise ActivationUnavailable
