"""API endpoints for Telegram account linking with user profiles."""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from config.settings import TELEGRAM_BOT_NAME, TELEGRAM_LINK_TOKEN_EXPIRE
from .models import Profile
from .utils import generate_telegram_token, verify_telegram_token

User = get_user_model()

CONFIRM_TG_LINK_COOLDOWN = getattr(settings, "CONFIRM_TG_LINK_COOLDOWN", 10)


class GenerateTgLinkView(APIView):
    """Генерирует одноразовую ссылку для привязки Tg-аккаунта к профилю."""

    permission_classes = [IsAuthenticated]

    def post(self, request):  # noqa
        user = request.user
        link_token = generate_telegram_token(user.pk)
        telegram_link = f"https://t.me/{TELEGRAM_BOT_NAME}?start={link_token}"

        return Response(
            {
                "telegram_link": telegram_link,
                "link_token": link_token,
                "expires_in": TELEGRAM_LINK_TOKEN_EXPIRE,
            },
            status=status.HTTP_200_OK,
        )


class ConfirmTgLinkView(APIView):
    """Подтверждает и привязывает Tg-аккаунт к профилю пользователя."""

    permission_classes = [AllowAny]

    def post(self, request):  # noqa
        code = request.data.get("code")
        telegram_id = request.data.get("telegram_id")
        if not code or not telegram_id:
            return Response(
                {"error": "Both 'code' and 'telegram_id' are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # rate-limit по telegram_id
        cooldown_key = f"confirm_tg_cooldown:{telegram_id}"
        if cache.get(cooldown_key):
            return Response(
                {"error": "Too many requests. Try again later."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
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
                {"error": "User not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if Profile.objects.filter(telegram_id=telegram_id).exclude(user=user).exists():
            return Response(
                {"error": "This Telegram account is already linked to another user"},
                status=status.HTTP_409_CONFLICT,
            )

        profile, _ = Profile.objects.get_or_create(user=user)
        profile.telegram_id = telegram_id
        profile.save(update_fields=["telegram_id"])

        cache.set(cooldown_key, True, timeout=CONFIRM_TG_LINK_COOLDOWN)

        return Response(
            {"detail": "Telegram account successfully linked"},
            status=status.HTTP_200_OK,
        )
