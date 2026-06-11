from django.db import models
from .usuario import Usuario
from .dispositivo import Dispositivo


class Ticket(models.Model):
    STATUS = [
        ('aberto', 'Aberto'),
        ('assumido', 'Assumido'),
        ('em_andamento', 'Em andamento'),
        ('resolvido', 'Resolvido'),
        ('encerrado', 'Encerrado'),
    ]

    titulo = models.CharField(max_length=200)
    descricao = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS, default='aberto')
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        related_name='tickets_abertos',
    )
    tecnico = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tickets_atendidos',
    )
    dispositivo = models.ForeignKey(Dispositivo, on_delete=models.SET_NULL, null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'

    def __str__(self):
        return self.titulo
