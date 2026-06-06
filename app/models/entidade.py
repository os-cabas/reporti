from django.db import models


class Entidade(models.Model):
    TIPOS = [
        ('escola', 'Escola'),
        ('empresa', 'Empresa'),
        ('universidade', 'Universidade'),
        ('outro', 'Outro'),
    ]
    STATUS = [
        ('ativa', 'Ativa'),
        ('inativa', 'Inativa'),
    ]

    nome = models.CharField(max_length=200, unique=True)
    tipo = models.CharField(max_length=50, choices=TIPOS, default='outro')
    email_responsavel = models.EmailField()
    descricao = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS, default='ativa')
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Entidade'
        verbose_name_plural = 'Entidades'

    def __str__(self):
        return self.nome
