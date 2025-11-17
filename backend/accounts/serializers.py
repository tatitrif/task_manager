"""Django REST Framework serializers for the accounts app."""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """Сериализатор для регистрации пользователя."""

    password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)

    class Meta:  # noqa
        model = User
        fields = ("username", "email", "password", "confirm_password")

    def create(self, validated_data):
        """Удаляет подтверждение пароля и создает пользователя."""
        validated_data.pop("confirm_password")
        # create_user специальный метод для создания пользователя с шифрованием пароля.
        user = User.objects.create_user(**validated_data)
        return user
