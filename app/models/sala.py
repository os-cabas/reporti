from django.db import models
from .entidade import Entidade

class Sala(models.Model):
    nome = models.CharField(max_length=200)
    andar = models.CharField(max_length=50)
    numero = models.CharField(max_length=20)
    entidade = models.ForeignKey(Entidade, on_delete=models.CASCADE, related_name='salas')

    def __str__(self):
        return f'{self.nome} - {self.entidade}'