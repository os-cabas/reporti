from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from app.models import Entidade, Sala, Dispositivo, Ticket
from app.models.usuario import Usuario


class Command(BaseCommand):
    help = 'Popula o banco com dados de desenvolvimento'

    def handle(self, *args, **kwargs):
        self.stdout.write('Criando dados de dev...\n')

        # ── Entidade ─────────────────────────────────────────────────────────
        entidade, _ = Entidade.objects.get_or_create(
            nome='Escola Estadual ReporTi Demo',
            defaults=dict(tipo='escola', email_responsavel='admin@reporti.demo', status='ativa'),
        )

        # ── Salas ─────────────────────────────────────────────────────────────
        sala_a, _ = Sala.objects.get_or_create(nome='Lab de Informática A', entidade=entidade, defaults=dict(bloco='A', andar='1'))
        sala_b, _ = Sala.objects.get_or_create(nome='Biblioteca',           entidade=entidade, defaults=dict(bloco='B', andar='1'))
        sala_c, _ = Sala.objects.get_or_create(nome='Sala dos Professores', entidade=entidade, defaults=dict(bloco='A', andar='2'))

        # ── Usuários ──────────────────────────────────────────────────────────
        def criar_usuario(email, nome, perfil, senha='Senha@123'):
            u, criado = Usuario.objects.get_or_create(
                email=email,
                defaults=dict(username=email, first_name=nome.split()[0], last_name=' '.join(nome.split()[1:]),
                              perfil=perfil, entidade=entidade),
            )
            if criado:
                u.set_password(senha)
                u.save()
            return u

        comum   = criar_usuario('aluno@reporti.demo',   'Carlos Mendes',  'comum')
        tecnico = criar_usuario('tecnico@reporti.demo', 'Ana Souza',      'tecnico')
        admin   = criar_usuario('admin@reporti.demo',   'Bruno Ferreira', 'admin_entidade', senha='Admin@123')

        # ── Dispositivos ──────────────────────────────────────────────────────
        dispositivos_spec = [
            ('QR-2024-001', 'Computador', 'Dell',    'operacional',    sala_a),
            ('QR-2024-002', 'Computador', 'HP',      'em_manutencao',  sala_a),
            ('QR-2024-003', 'Projetor',   'Epson',   'operacional',    sala_b),
            ('QR-2024-004', 'Impressora', 'Brother', 'operacional',    sala_c),
            ('QR-2024-005', 'Computador', 'Lenovo',  'inativo',        sala_b),
        ]
        disps = []
        for cod, tipo, marca, situacao, sala in dispositivos_spec:
            d, _ = Dispositivo.objects.get_or_create(
                codigo_qr=cod,
                defaults=dict(tipo=tipo, marca=marca, situacao=situacao, sala=sala),
            )
            disps.append(d)

        # ── Tickets ───────────────────────────────────────────────────────────
        agora = timezone.now()
        tickets_spec = [
            (disps[0], 'Monitor não liga',              'O monitor do PC 01 não está ligando desde ontem.',                       'aberto',       None,    agora - timedelta(days=1)),
            (disps[0], 'Teclado com teclas travadas',   'As teclas A e S estão presas, dificultando a digitação.',               'assumido',     tecnico, agora - timedelta(days=3)),
            (disps[1], 'Computador reiniciando sozinho','O PC desliga e reinicia sem motivo durante as aulas.',                  'em_andamento', tecnico, agora - timedelta(days=5)),
            (disps[2], 'Projetor sem imagem',           'O projetor liga mas não exibe imagem no telão.',                        'aberto',       None,    agora - timedelta(hours=4)),
            (disps[3], 'Impressora não imprime',        'Ao enviar qualquer documento, a impressora fica em fila e não imprime.','resolvido',    tecnico, agora - timedelta(days=10)),
            (disps[0], 'Mouse com defeito',             '',                                                                      'encerrado',    tecnico, agora - timedelta(days=15)),
        ]

        for disp, titulo, desc, status, tec, criado_em in tickets_spec:
            t, criado = Ticket.objects.get_or_create(
                titulo=titulo,
                usuario=comum,
                defaults=dict(descricao=desc, status=status, tecnico=tec, dispositivo=disp),
            )
            if criado:
                Ticket.objects.filter(pk=t.pk).update(criado_em=criado_em)

        self.stdout.write(self.style.SUCCESS('\nDados criados com sucesso!\n'))
        self.stdout.write('-' * 44)
        self.stdout.write('\n USUÁRIOS DE TESTE\n')
        self.stdout.write('-' * 44)
        self.stdout.write(f'\n Comum    | aluno@reporti.demo    | Senha@123')
        self.stdout.write(f'\n Técnico  | tecnico@reporti.demo  | Senha@123')
        self.stdout.write(f'\n Admin    | admin@reporti.demo    | Admin@123')
        self.stdout.write('\n')
        self.stdout.write('-' * 44)
        self.stdout.write('\n DISPOSITIVOS (para testar busca)\n')
        self.stdout.write('-' * 44)
        for cod, tipo, marca, situacao, sala in dispositivos_spec:
            self.stdout.write(f'\n {cod}  ->  {tipo} {marca} ({situacao})')
        self.stdout.write('\n' + '-' * 44 + '\n')
