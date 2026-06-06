from rest_framework import serializers
from app.models.usuario_permissao import UsuarioPermissao

class UsuarioPermissaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsuarioPermissao
        fields = ['id', 'usuario', 'permissao', 'data']
        read_only_fields = ['data']