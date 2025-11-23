
from unittest.mock import patch

import pytest
from django.core.cache import cache

from accounts.utils import generate_telegram_token, verify_telegram_token


@pytest.fixture(autouse=True)
def clear_cache():
    """Fixture to clear cache before each test."""
    cache.clear()
    yield
    cache.clear()


def test_generate_and_verify_token():
    """Test that a token can be generated and successfully verified."""
    user_id = 1
    token = generate_telegram_token(user_id)
    assert isinstance(token, str)
    assert len(token) > 0

    verified_user_id = verify_telegram_token(token)
    assert verified_user_id == user_id


def test_verify_invalid_token():
    """Test that an invalid token returns None."""
    invalid_token = "invalid_token"
    verified_user_id = verify_telegram_token(invalid_token)
    assert verified_user_id is None


def test_token_expiration():
    """Test that a token expires and cannot be verified."""
    user_id = 1
    token = generate_telegram_token(user_id, expire=-1)
    verified_user_id = verify_telegram_token(token)
    assert verified_user_id is None
