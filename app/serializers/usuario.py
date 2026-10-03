from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from app.models.usuario import Usuario


class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    # Perfis que só o Administrador Geral pode conceder
    PERFIS_RESTRITOS = ('admin_entidade', 'admin_geral')

    class Meta:
        model = Usuario
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'cargo', 'perfil', 'entidade', 'is_active', 'password',
        ]
        read_only_fields = ['id']

    def validate(self, attrs):
        """
        RN005 / RN006 – quem não é Administrador Geral só gerencia usuários da
        própria entidade e não concede perfis administrativos.
        """
        request = self.context.get('request')
        autor = getattr(request, 'user', None)
        if autor is None or not autor.is_authenticated:
            raise PermissionDenied('Autenticação obrigatória.')
        if autor.perfil == 'admin_geral':
            return attrs

        if self.instance is not None and self.instance.perfil == 'admin_geral':
            raise PermissionDenied('Apenas o Administrador Geral pode alterar um Administrador Geral.')

        perfil_atual = self.instance.perfil if self.instance is not None else None
        perfil = attrs.get('perfil')
        if perfil in self.PERFIS_RESTRITOS and perfil != perfil_atual:
            raise serializers.ValidationError(
                {'perfil': 'Apenas o Administrador Geral pode conceder este perfil.'}
            )

        entidade = attrs.get('entidade')
        if entidade is not None and entidade.pk != autor.entidade_id:
            raise serializers.ValidationError(
                {'entidade': 'Você só pode gerenciar usuários da sua própria entidade.'}
            )
        if self.instance is None or 'entidade' in attrs:
            attrs['entidade'] = autor.entidade
        return attrs

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = Usuario(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance
