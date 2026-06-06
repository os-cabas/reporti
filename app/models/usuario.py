from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    PERFIS = [
        ('comum', 'Comum'),
        ('tecnico', 'Técnico'),
        ('admin_entidade', 'Administrador da Entidade'),
        ('admin_geral', 'Administrador Geral'),
    ]

    cargo = models.CharField(max_length=100, blank=True)
    perfil = models.CharField(max_length=20, choices=PERFIS, default='comum')
    entidade = models.ForeignKey(
        'Entidade',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='usuarios',
    )
    email = models.EmailField(unique=True)

    # Login feito por e-mail; username continua existindo mas não é usado para autenticar
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
