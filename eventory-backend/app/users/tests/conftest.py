"""Shared fixtures for user, authentication, and OTP tests."""

from __future__ import annotations

import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from app.users.models import User


@pytest.fixture(autouse=True)
def clear_test_cache():
    """Keep OTP state and DRF throttle counters isolated between tests."""
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api_client() -> APIClient:
    """Return an unauthenticated DRF API client."""
    return APIClient()


@pytest.fixture
def verified_phone_user(db) -> User:
    """Create a user with a verified phone and a known raw password."""
    return User.objects.create_user(
        phone="+989121234567",
        password="StrongPass1!",
        username="TestUser",
        last_name="Tester",
        email="test.user@example.com",
        is_active=True,
        is_phone_verified=True,
        is_email_verified=True,
    )
