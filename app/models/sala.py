from django.db import models
from .entidade import Entidade


class Sala(models.Model):
    nome = models.CharField(max_length=200)
    bloco = models.CharField(max_length=50, blank=True)
    andar = models.CharField(max_length=50, blank=True)
    numero = models.CharField(max_length=20, blank=True)
    observacao = models.TextField(blank=True)
    entidade = models.ForeignKey(Entidade, on_delete=models.CASCADE, related_name='salas')

    class Meta:
        unique_together = ('nome', 'entidade')
        verbose_name = 'Sala'
        verbose_name_plural = 'Salas'

    def __str__(self):
        return f'{self.nome} - {self.entidade}'
