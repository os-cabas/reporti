from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class AdminTokenObtainSerializer(TokenObtainPairSerializer):
    """
    Serializer JWT para login de administradores e servidores (email + senha).
    Usuários com perfil 'comum' não podem autenticar por este endpoint —
    eles devem usar Google OAuth ou Magic Link.
    """

    PERFIS_PERMITIDOS = ('admin_geral', 'admin_entidade', 'tecnico')

    def validate(self, attrs):
        data = super().validate(attrs)

        user = self.user
        if user.perfil not in self.PERFIS_PERMITIDOS:
            raise serializers.ValidationError(
                'Este login é exclusivo para administradores e servidores. '
                'Usuários comuns devem acessar via Google ou link enviado ao e-mail.'
            )

        # Inclui informações do usuário na resposta para o frontend não precisar de chamada extra
        data['usuario'] = {
            'id': user.id,
            'nome': user.get_full_name() or user.username,
            'email': user.email,
            'perfil': user.perfil,
            'entidade_id': user.entidade_id,
        }

        return data
