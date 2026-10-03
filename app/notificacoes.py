"""
Alertas por e-mail dos chamados.

O envio acontece depois do commit da transação e nunca derruba a requisição:
qualquer falha de SMTP vai para o log.
"""
import logging

from django.conf import settings
from django.core import mail
from django.db import transaction

from app.models.usuario import Usuario

logger = logging.getLogger('app.notificacoes')

MAX_DESTINATARIOS = 50
TIMEOUT_SMTP_PADRAO = 10  # segundos; usado quando EMAIL_TIMEOUT não está definido


def _linha(texto, limite=120):
    """Texto em uma linha só. Evita header injection no assunto do e-mail."""
    return ' '.join(str(texto or '').split())[:limite]


def _nome(usuario):
    return usuario.get_full_name() or usuario.username


def _conexao():
    kwargs = {}
    usa_smtp = settings.EMAIL_BACKEND.endswith('smtp.EmailBackend')
    if usa_smtp and getattr(settings, 'EMAIL_TIMEOUT', None) is None:
        kwargs['timeout'] = TIMEOUT_SMTP_PADRAO
    return mail.get_connection(**kwargs)


def _enviar(assunto, corpo, destinatarios):
    # Um e-mail por destinatário: ninguém vê o endereço dos demais.
    destinatarios = [d for d in dict.fromkeys(destinatarios) if d][:MAX_DESTINATARIOS]
    if not destinatarios:
        return

    def _despachar():
        try:
            conexao = _conexao()
            mensagens = [
                mail.EmailMessage(assunto, corpo, settings.DEFAULT_FROM_EMAIL, [d], connection=conexao)
                for d in destinatarios
            ]
            conexao.send_messages(mensagens)
        except Exception:
            logger.exception('Falha ao enviar alerta por e-mail: %s', assunto)

    transaction.on_commit(_despachar)


def _emails_tecnicos(ticket, exceto=None):
    """Técnicos e administradores ativos da entidade dona do equipamento."""
    sala = getattr(ticket.dispositivo, 'sala', None)
    entidade_id = getattr(sala, 'entidade_id', None)
    if not entidade_id:
        return []
    qs = Usuario.objects.filter(
        perfil__in=('tecnico', 'admin_entidade'),
        is_active=True,
        entidade_id=entidade_id,
    ).exclude(email='')
    if exceto is not None:
        qs = qs.exclude(pk=exceto.pk)
    return list(qs.values_list('email', flat=True)[:MAX_DESTINATARIOS])


def _email_solicitante(ticket, exceto=None):
    usuario = ticket.usuario
    if not usuario or not usuario.is_active or not usuario.email:
        return []
    if exceto is not None and usuario.pk == exceto.pk:
        return []
    return [usuario.email]


def _identificacao(ticket):
    linhas = [
        f'Chamado #{ticket.pk}: {_linha(ticket.titulo, 200)}',
        f'Prioridade: {ticket.get_prioridade_display()}',
        f'Tipo de problema: {ticket.get_tipo_problema_display()}',
    ]
    if ticket.dispositivo:
        linhas.append(f'Equipamento: {_linha(ticket.dispositivo)}')
        if ticket.dispositivo.sala:
            linhas.append(f'Local: {_linha(ticket.dispositivo.sala.nome)}')
    return '\n'.join(linhas)


def notificar_abertura(ticket, base_url):
    """Avisa os técnicos da entidade de que há um chamado novo."""
    assunto = f'[ReporTi] Novo chamado #{ticket.pk}: {_linha(ticket.titulo)}'
    corpo = (
        'Um novo chamado foi aberto.\n\n'
        f'{_identificacao(ticket)}\n'
        f'Aberto por: {_nome(ticket.usuario) if ticket.usuario else "—"}\n\n'
        f'{ticket.descricao}\n\n'
        f'Atenda em: {base_url}/tickets/'
    )
    _enviar(assunto, corpo, _emails_tecnicos(ticket, exceto=ticket.usuario))


def notificar_status(ticket, descricao, autor, base_url):
    """Avisa quem abriu o chamado de que o status mudou."""
    assunto = f'[ReporTi] Chamado #{ticket.pk} agora está: {ticket.get_status_display()}'
    corpo = (
        f'O seu chamado mudou para "{ticket.get_status_display()}".\n\n'
        f'{_identificacao(ticket)}\n'
        f'Técnico responsável: {_nome(ticket.tecnico) if ticket.tecnico else "—"}\n\n'
        f'{descricao}\n\n'
        f'Acompanhe em: {base_url}/meus-reportes/'
    )
    _enviar(assunto, corpo, _email_solicitante(ticket, exceto=autor))


def notificar_comentario(ticket, texto, autor, base_url):
    """Comentário do solicitante vai para o técnico (ou a equipe); o do técnico, para o solicitante."""
    if ticket.usuario_id == autor.pk:
        if ticket.tecnico and ticket.tecnico.is_active and ticket.tecnico.email:
            destinatarios = [ticket.tecnico.email]
        else:
            destinatarios = _emails_tecnicos(ticket, exceto=autor)
        link = f'{base_url}/tickets/'
    else:
        destinatarios = _email_solicitante(ticket, exceto=autor)
        link = f'{base_url}/meus-reportes/'

    assunto = f'[ReporTi] Novo comentário no chamado #{ticket.pk}'
    corpo = (
        f'{_nome(autor)} comentou no chamado.\n\n'
        f'{_identificacao(ticket)}\n\n'
        f'{texto}\n\n'
        f'Responda em: {link}'
    )
    _enviar(assunto, corpo, destinatarios)
