from django.db import models
from .sala import Sala
from .modelo import Modelo


class Dispositivo(models.Model):
    SITUACOES = [
        ('operacional', 'Operacional'),
        ('em_manutencao', 'Em Manutenção'),
        ('reservado', 'Reservado'),
        ('inativo', 'Inativo'),
        ('descartado', 'Descartado'),
    ]

    codigo_qr = models.CharField(max_length=100, unique=True, blank=True)
    patrimonio = models.CharField(max_length=100, blank=True)
    tipo = models.CharField(max_length=100, blank=True)
    marca = models.CharField(max_length=100, blank=True)
    modelo = models.ForeignKey(Modelo, on_delete=models.SET_NULL, null=True, blank=True)
    numero_serie = models.CharField(max_length=100, blank=True)
    situacao = models.CharField(max_length=20, choices=SITUACOES, default='operacional')
    sala = models.ForeignKey(Sala, on_delete=models.SET_NULL, null=True, blank=True, related_name='dispositivos')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Dispositivo'
        verbose_name_plural = 'Dispositivos'

    def __str__(self):
        return f'{self.codigo_qr} – {self.tipo} {self.marca}'
