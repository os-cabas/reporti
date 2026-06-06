from django.db import models
from .dispositivo import Dispositivo


class HistoricoDispositivo(models.Model):
    ACOES = [
        ('criacao', 'Criação'),
        ('status', 'Mudança de Status'),
        ('localizacao', 'Mudança de Localização'),
        ('manutencao', 'Manutenção'),
        ('chamado', 'Chamado'),
        ('edicao', 'Edição'),
    ]

    dispositivo = models.ForeignKey(Dispositivo, on_delete=models.CASCADE, related_name='historico')
    acao = models.CharField(max_length=20, choices=ACOES)
    descricao = models.TextField()
    usuario = models.ForeignKey(
        'Usuario',
        on_delete=models.SET_NULL,
        null=True,
        related_name='historico_dispositivos',
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Histórico de Dispositivo'
        verbose_name_plural = 'Históricos de Dispositivos'
        ordering = ['-criado_em']

    def __str__(self):
        return f'{self.get_acao_display()} – {self.dispositivo} ({self.criado_em:%d/%m/%Y %H:%M})'
