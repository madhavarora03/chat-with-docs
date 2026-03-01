import pytest

from app.core import security
from app.exceptions import InvalidTokenError


# ─── create_access_token ───
def test_create_access_token_with_additional_claims() -> None:
    token = security.create_access_token(
        subject="user-123", additional_claims={"role": "admin"}
    )
    payload = security.decode_access_token(token)
    assert payload["role"] == "admin"
    assert payload["sub"] == "user-123"


# ─── decode_access_token ───
def test_decode_access_token_wrong_type() -> None:
    token = security.create_access_token(
        subject="user-123", additional_claims={"typ": "refresh"}
    )
    with pytest.raises(InvalidTokenError):
        security.decode_access_token(token)
