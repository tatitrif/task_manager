"""API endpoints for Telegram account linking with user profiles."""

import logging
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model

from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from config.settings import TELEGRAM_BOT_NAME, TELEGRAM_LINK_TOKEN_EXPIRE
from .models import Profile
from .utils import generate_telegram_token, verify_telegram_token

logger = logging.getLogger(__name__)
User = get_user_model()

SIMPLE_JWT = getattr(settings, "SIMPLE_JWT", {})
ACCESS_TOKEN_LIFETIME = SIMPLE_JWT.get("ACCESS_TOKEN_LIFETIME", timedelta(minutes=5))
REFRESH_TOKEN_LIFETIME = SIMPLE_JWT.get("REFRESH_TOKEN_LIFETIME", timedelta(days=1))


class GenerateTgLinkView(APIView):
    """Генерирует одноразовую ссылку для привязки Telegram-аккаунта."""

    permission_classes = [IsAuthenticated]

    def post(self, request):  # noqa
        user = request.user
        link_token = generate_telegram_token(user.pk)
        telegram_link = f"https://t.me/{TELEGRAM_BOT_NAME}?start={link_token}"

        logger.info(f"Generated Telegram link for user {user.pk}")

        return Response(
            {
                "telegram_link": telegram_link,
                "link_token": link_token,
                "expires_in": TELEGRAM_LINK_TOKEN_EXPIRE,
            },
            status=status.HTTP_200_OK,
        )


class ConfirmTgLinkView(APIView):
    """Подтверждает и привязывает Telegram-аккаунт к профилю пользователя."""

    permission_classes = [AllowAny]

    def post(self, request):  # noqa
        code = request.data.get("code")
        telegram_id = request.data.get("telegram_id")

        if not code or not telegram_id:
            return Response(
                {"error": "Both 'code' and 'telegram_id' are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_id = verify_telegram_token(code)
        if not user_id:
            return Response(
                {"error": "Invalid or expired code"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.filter(pk=user_id).first()
        if not user:
            return Response(
                {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )

        if Profile.objects.filter(telegram_id=telegram_id).exclude(user=user).exists():
            return Response(
                {"error": "This Telegram account is already linked to another user"},
                status=status.HTTP_409_CONFLICT,
            )

        profile, _ = Profile.objects.get_or_create(user=user)
        profile.telegram_id = telegram_id

        # Генерация JWT токенов
        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)

        now = timezone.now()
        refresh_exp = now + REFRESH_TOKEN_LIFETIME

        # Сохраняем срок жизни refresh в БД
        profile.jwt_refresh_expires = refresh_exp
        profile.save(update_fields=["telegram_id", "jwt_refresh_expires"])

        # Логируем успешную привязку
        logger.info(f"User {user.pk} linked Telegram ID {telegram_id}")

        return Response(
            {
                "detail": "Telegram account successfully linked",
                "access": access,
                "refresh": str(refresh),
                "access_expires_in": int(ACCESS_TOKEN_LIFETIME.total_seconds()),
                "refresh_expires_at": refresh_exp.isoformat(),
            },
            status=status.HTTP_200_OK,
        )
