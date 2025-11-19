"""API endpoints for Telegram account linking with user profiles."""

import logging
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth import logout as django_logout
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from config.settings import TELEGRAM_BOT_NAME, TELEGRAM_LINK_TOKEN_EXPIRE, SIMPLE_JWT
from .models import Profile
from .serializers import RegisterSerializer
from .utils import generate_telegram_token, verify_telegram_token

logger = logging.getLogger(__name__)
User = get_user_model()

ACCESS_TOKEN_LIFETIME = SIMPLE_JWT.get("ACCESS_TOKEN_LIFETIME", timedelta(minutes=5))
REFRESH_TOKEN_LIFETIME = SIMPLE_JWT.get("REFRESH_TOKEN_LIFETIME", timedelta(days=1))


class GenerateTgLinkView(APIView):
    """Одноразовая ссылка, токен для привязки Telegram-аккаунта и время его жизни."""

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
    """Подтверждение и привязка Telegram-аккаунта к пользователю."""

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

        # Проверка на существование user_id
        user = get_object_or_404(User, pk=user_id)

        # Проверка на существующий telegram_id у другого пользователя
        if Profile.objects.filter(telegram_id=telegram_id).exclude(user=user).exists():
            return Response(
                {"error": "This Telegram account is already linked to another user"},
                status=status.HTTP_409_CONFLICT,
            )

        # Генерация JWT токенов
        refresh = RefreshToken.for_user(user)

        # Добавление в Profile
        with transaction.atomic():
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.telegram_id = telegram_id
            profile.jwt_refresh_expires = timezone.now() + REFRESH_TOKEN_LIFETIME
            profile.save(update_fields=["telegram_id", "jwt_refresh_expires"])

        # Логируем успешную привязку
        logger.info("User  %s linked Telegram ID  %s", user, telegram_id)

        return Response(
            {
                "message": "Telegram account successfully linked",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_200_OK,
        )


# POST /api/auth/register/
class RegisterView(generics.CreateAPIView):
    """Регистрация нового пользователя."""

    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        """Валидирует данные и создает пользователя, возвращая успешный ответ."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {
                "message": "User registered successfully",
                "user_id": user.id,
            },
            status=status.HTTP_201_CREATED,
        )


# POST /api/auth/logout/
class LogoutView(APIView):
    """Выход пользователя: сессии и JWT."""

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):  # noqa
        try:
            # Удаляем сессию
            django_logout(request)

            # Получаем refresh_token из тела запроса
            refresh_token = request.data.get("refresh_token")

            if not refresh_token:
                return Response(
                    {"error": "Refresh token is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Добавляем refresh_token в blacklist
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(
                {"message": "Successfully logged out"}, status=status.HTTP_200_OK
            )
        except TokenError:
            # Если токен уже был в blacklist или невалиден
            return Response(
                {"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )


class LoginView(TokenObtainPairView):
    """Аутентификация пользователя и выдача токенов."""

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):  # noqa
        # Вызываем родительский метод для проверки данных
        response = super().post(request, *args, **kwargs)

        if response.status_code == 200:
            # Извлекаем токены из стандартного ответа
            refresh_str = response.data["refresh"]
            access_str = response.data["access"]

            # Создаем RefreshToken из строки
            refresh = RefreshToken(refresh_str)

            # Вычисляем время жизни
            now = timezone.now()
            refresh_exp = now + REFRESH_TOKEN_LIFETIME

            # Формируем кастомный ответ
            response.data = {
                "access": access_str,
                "refresh": str(refresh),
                "access_expires_in": int(ACCESS_TOKEN_LIFETIME.total_seconds()),
                "refresh_expires_at": refresh_exp.isoformat(),
            }
        return response
