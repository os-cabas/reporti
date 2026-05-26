import getpass
from django.core.management.base import BaseCommand
from django.db import IntegrityError
from app.models.usuario import Usuario


class Command(BaseCommand):
    help = 'Cria o usuário administrador inicial do sistema.'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Username do administrador')
        parser.add_argument('--password', type=str, help='Senha do administrador')
        parser.add_argument('--email',    type=str, help='E-mail (opcional)', default='')
        parser.add_argument('--nome',     type=str, help='Nome completo (opcional)', default='')
        parser.add_argument('--no-input', action='store_true',
                            help='Usa apenas os argumentos passados, sem perguntas interativas')

    def handle(self, *args, **options):
        no_input = options['no_input']

        # --- username ---
        username = options.get('username')
        if not username:
            if no_input:
                self.stderr.write(self.style.ERROR('--username é obrigatório com --no-input.'))
                return
            username = input('Username: ').strip()
            if not username:
                self.stderr.write(self.style.ERROR('Username não pode ser vazio.'))
                return

        # --- password ---
        password = options.get('password')
        if not password:
            if no_input:
                self.stderr.write(self.style.ERROR('--password é obrigatório com --no-input.'))
                return
            password = getpass.getpass('Senha: ')
            confirm  = getpass.getpass('Confirme a senha: ')
            if password != confirm:
                self.stderr.write(self.style.ERROR('As senhas não coincidem.'))
                return
            if len(password) < 6:
                self.stderr.write(self.style.ERROR('A senha deve ter ao menos 6 caracteres.'))
                return

        # --- campos opcionais ---
        email = options.get('email') or ''
        nome  = options.get('nome')  or ''
        first_name, *rest = (nome.split(' ', 1) if nome else ('', []))
        last_name = rest[0] if rest else ''

        if not no_input and not email:
            email = input('E-mail (Enter para pular): ').strip()

        # --- verifica se já existe ---
        if Usuario.objects.filter(username=username).exists():
            self.stderr.write(self.style.WARNING(
                f'Usuário "{username}" já existe. Nenhuma alteração feita.'
            ))
            return

        # --- cria ---
        try:
            user = Usuario(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                is_staff=True,
                is_superuser=True,
                cargo='Administrador',
            )
            user.set_password(password)
            user.save()

            self.stdout.write(self.style.SUCCESS(
                f'\nAdministrador "{username}" criado com sucesso! '
                f'Acesse /login/ para entrar no sistema.'
            ))
        except IntegrityError as e:
            self.stderr.write(self.style.ERROR(f'Erro ao criar usuário: {e}'))
