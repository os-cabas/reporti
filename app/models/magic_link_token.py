import secrets
from datetime import timedelta

from django.db import models
from django.utils import timezone


class MagicLinkToken(models.Model):
    email = models.EmailField()
    token = models.CharField(max_length=64, unique=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    usado = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Token Magic Link'
        verbose_name_plural = 'Tokens Magic Link'

    def is_valid(self):
        expira_em = self.criado_em + timedelta(minutes=15)
        return not self.usado and timezone.now() < expira_em

    @classmethod
    def gerar(cls, email):
        cls.objects.filter(email=email, usado=False).update(usado=True)
        return cls.objects.create(email=email, token=secrets.token_urlsafe(48))

    def __str__(self):
        return f'Token para {self.email} (usado={self.usado})'
