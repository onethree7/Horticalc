from __future__ import annotations

import pytest

from horticalc.activation import (
    clear_activation_handler,
    configure_activation_handler,
    configure_activation_token,
)


@pytest.fixture(autouse=True)
def reset_activation_state():
    clear_activation_handler()
    yield
    clear_activation_handler()


def test_activation_endpoint_rejects_missing_or_wrong_token(api_client) -> None:
    configure_activation_token("a" * 43)
    configure_activation_handler(lambda _target: True, object())

    assert api_client.post("/_launcher/activate").status_code == 403
    assert (
        api_client.post(
            "/_launcher/activate",
            headers={"X-Horticalc-Activation": "b" * 43},
        ).status_code
        == 403
    )


def test_activation_endpoint_returns_unavailable_until_window_is_ready(api_client) -> None:
    configure_activation_token("a" * 43)

    response = api_client.post(
        "/_launcher/activate",
        headers={"X-Horticalc-Activation": "a" * 43},
    )

    assert response.status_code == 503


def test_activation_endpoint_invokes_configured_window_handler(api_client) -> None:
    calls = []
    target = object()
    configure_activation_token("a" * 43)
    configure_activation_handler(lambda value: calls.append(value) or True, target)

    response = api_client.post(
        "/_launcher/activate",
        headers={"X-Horticalc-Activation": "a" * 43},
    )

    assert response.status_code == 204
    assert response.content == b""
    assert calls == [target]


def test_activation_endpoint_is_hidden_from_public_openapi(api_client) -> None:
    assert "/_launcher/activate" not in api_client.get("/openapi.json").json()["paths"]
