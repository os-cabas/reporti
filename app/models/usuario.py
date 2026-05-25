from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    cargo = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'