from django.db import models
from .ticket import Ticket


class HistoricoTicket(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='historico')
    acao = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)
    usuario = models.ForeignKey(
        'Usuario',
        on_delete=models.SET_NULL,
        null=True,
        related_name='historico_tickets',
    )
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Histórico de Ticket'
        verbose_name_plural = 'Históricos de Tickets'
        ordering = ['-criado_em']

    def __str__(self):
        return f'{self.acao} – Ticket #{self.ticket_id} ({self.criado_em:%d/%m/%Y %H:%M})'
