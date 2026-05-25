from django.contrib.auth.models import AbstractUser
from django.db import models
from .permissao import Permissao
from .usuario import Usuario

class UsuarioPermissao(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    permissao = models.ForeignKey(Permissao, on_delete=models.CASCADE)
    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('usuario', 'permissao')
