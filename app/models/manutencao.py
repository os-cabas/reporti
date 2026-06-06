from django.db import models
from .dispositivo import Dispositivo


class Manutencao(models.Model):
    TIPOS = [
        ('preventiva', 'Preventiva'),
        ('corretiva', 'Corretiva'),
        ('preditiva', 'Preditiva'),
    ]

    dispositivo = models.ForeignKey(Dispositivo, on_delete=models.CASCADE, related_name='manutencoes')
    tipo = models.CharField(max_length=20, choices=TIPOS)
    descricao = models.TextField()
    data_inicio = models.DateTimeField()
    data_fim = models.DateTimeField(null=True, blank=True)
    tecnico = models.ForeignKey(
        'Usuario',
        on_delete=models.SET_NULL,
        null=True,
        related_name='manutencoes',
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Manutenção'
        verbose_name_plural = 'Manutenções'
        ordering = ['-data_inicio']

    def __str__(self):
        return f'{self.get_tipo_display()} – {self.dispositivo} ({self.data_inicio:%d/%m/%Y})'
