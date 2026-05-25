from rest_framework import viewsets
from app.models.ticket import Ticket
from app.serializers.ticket import TicketSerializer

class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.select_related('usuario', 'dispositivo').all()
    serializer_class = TicketSerializer