from rest_framework.throttling import UserRateThrottle


class AberturaTicketThrottle(UserRateThrottle):
    """Cada abertura dispara e-mail para os técnicos: limita o volume por usuário."""

    scope = 'ticket_abertura'
    rate = '60/hour'


class ComentarioTicketThrottle(UserRateThrottle):
    """Cada comentário dispara e-mail para a outra parte: limita o volume por usuário."""

    scope = 'ticket_comentario'
    rate = '120/hour'
