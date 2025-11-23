
import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

from accounts.models import Profile

User = get_user_model()


@pytest.mark.django_db
def test_profile_creation():
    """Test that a profile is created correctly and linked to a user."""
    user = User.objects.create_user(
        username="testuser",
        password="testpassword",
        email="test@example.com",
    )
    profile = Profile.objects.create(
        user=user,
        telegram_id=123456789,
    )
    assert profile.user == user
    assert profile.telegram_id == 123456789


@pytest.mark.django_db
def test_profile_uniqueness():
    """Test that telegram_id is unique."""
    user1 = User.objects.create_user(
        username="testuser1",
        password="testpassword",
    )
    Profile.objects.create(user=user1, telegram_id=12345)

    user2 = User.objects.create_user(
        username="testuser2",
        password="testpassword",
    )
    with pytest.raises(IntegrityError):
        Profile.objects.create(user=user2, telegram_id=12345)
