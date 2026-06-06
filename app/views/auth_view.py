"""
RF001 – Autenticação via Google OAuth
RF002 – Login por Magic Link (e-mail)
"""
import uuid

import requests
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from app.models.magic_link_token import MagicLinkToken
from app.models.usuario import Usuario


def _gerar_tokens(usuario):
    refresh = RefreshToken.for_user(usuario)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'usuario': {
            'id': usuario.pk,
            'nome': usuario.get_full_name() or usuario.username,
            'email': usuario.email,
            'perfil': usuario.perfil,
            'entidade_id': usuario.entidade_id,
        },
    }


def _username_unico(base: str) -> str:
    """Garante unicidade de username prefixando com parte de um UUID se necessário."""
    candidato = base[:140]
    if not Usuario.objects.filter(username=candidato).exists():
        return candidato
    return f'{candidato[:128]}_{uuid.uuid4().hex[:8]}'


# ─── RF001: Google OAuth ──────────────────────────────────────────────────────

class GoogleAuthView(APIView):
    """
    POST /api/auth/google/
    Body: { "id_token": "<token Google>" }
    """
    permission_classes = [AllowAny]
    GOOGLE_TOKENINFO_URL = 'https://oauth2.googleapis.com/tokeninfo'

    def post(self, request):
        id_token = request.data.get('id_token')
        if not id_token:
            return Response(
                {'erro': 'Campo id_token é obrigatório.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        resp = requests.get(self.GOOGLE_TOKENINFO_URL, params={'id_token': id_token}, timeout=5)
        if resp.status_code != 200:
            return Response({'erro': 'Token Google inválido.'}, status=status.HTTP_401_UNAUTHORIZED)

        payload = resp.json()

        # Garante que o token foi emitido para esta aplicação (previne token substitution)
        if payload.get('aud') != settings.GOOGLE_CLIENT_ID:
            return Response(
                {'erro': 'Token não pertence a esta aplicação.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        email = payload.get('email')
        if not email:
            return Response({'erro': 'Token não contém e-mail.'}, status=status.HTTP_400_BAD_REQUEST)

        allowed_domains = getattr(settings, 'GOOGLE_ALLOWED_DOMAINS', [])
        if allowed_domains:
            domain = email.split('@')[-1]
            if domain not in allowed_domains:
                return Response(
                    {'erro': f'Domínio {domain!r} não autorizado.'},
                    status=status.HTTP_403_FORBIDDEN,
                )

        with transaction.atomic():
            usuario, _ = Usuario.objects.get_or_create(
                email=email,
                defaults={
                    'username': _username_unico(email.split('@')[0]),
                    'first_name': payload.get('given_name', ''),
                    'last_name': payload.get('family_name', ''),
                },
            )

        return Response(_gerar_tokens(usuario))


# ─── RF002: Magic Link ────────────────────────────────────────────────────────

class MagicLinkSolicitarView(APIView):
    """
    POST /api/auth/magic-link/
    Body: { "email": "usuario@exemplo.com" }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email', '').strip().lower()
        if not email:
            return Response({'erro': 'Campo email é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)

        token_obj = MagicLinkToken.gerar(email)
        link = request.build_absolute_uri(f'/acesso/?token={token_obj.token}')

        send_mail(
            subject='Seu link de acesso – ReporTi',
            message=(
                f'Olá!\n\n'
                f'Clique no link abaixo para acessar o sistema (válido por 15 minutos):\n\n'
                f'{link}\n\n'
                f'Se você não solicitou este acesso, ignore este e-mail.'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )

        resposta = {'mensagem': 'Link enviado para o e-mail informado.'}
        if settings.DEBUG:
            resposta['debug_link'] = link
        return Response(resposta)


class MagicLinkVerificarView(APIView):
    """
    POST /api/auth/magic-link/verificar/
    Body: { "token": "<token>" }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        token_str = request.data.get('token', '').strip()
        if not token_str:
            return Response({'erro': 'Token é obrigatório.'}, status=status.HTTP_400_BAD_REQUEST)

        # select_for_update evita race condition: dois requests simultâneos
        # com o mesmo token não conseguem ambos passar pela validação.
        with transaction.atomic():
            try:
                token_obj = MagicLinkToken.objects.select_for_update().get(token=token_str)
            except MagicLinkToken.DoesNotExist:
                return Response({'erro': 'Token inválido.'}, status=status.HTTP_401_UNAUTHORIZED)

            if not token_obj.is_valid():
                return Response(
                    {'erro': 'Token expirado ou já utilizado.'},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            token_obj.usado = True
            token_obj.save(update_fields=['usado'])

            usuario, _ = Usuario.objects.get_or_create(
                email=token_obj.email,
                defaults={'username': _username_unico(token_obj.email.split('@')[0])},
            )

        return Response(_gerar_tokens(usuario))
