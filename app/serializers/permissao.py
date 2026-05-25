from app import serializers
from app.models.permissao import Permissao

class PermissaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permissao
        fields = ['id', 'nome']