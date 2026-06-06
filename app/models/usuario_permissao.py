from django.db import models
from .usuario import Usuario
from .permissao import Permissao


class UsuarioPermissao(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    permissao = models.ForeignKey(Permissao, on_delete=models.CASCADE)
    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'permissao')
