from django.db import models
from .usuario import Usuario
from .dispositivo import Dispositivo

class Ticket(models.Model):
    STATUS = [
        ('aberto', 'Aberto'),
        ('em_andamento', 'Em andamento'),
        ('fechado', 'Fechado'),
    ]

    titulo = models.CharField(max_length=200)
    descricao = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS, default='aberto')
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True)
    dispositivo = models.ForeignKey(Dispositivo, on_delete=models.SET_NULL, null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.titulo