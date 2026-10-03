import csv
import io
from datetime import timedelta
from unittest import mock

from django.core import mail
from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from app.exportacao import celula_segura
from app.models import Dispositivo, Entidade, HistoricoTicket, Sala, Ticket, Usuario
from app.notificacoes import _linha
from app.throttles import AberturaTicketThrottle


class BaseTestCase(TestCase):
    """Duas entidades (A e B) para exercitar o isolamento entre organizações (RN005)."""

    @classmethod
    def setUpTestData(cls):
        cls.ent_a = Entidade.objects.create(nome='Entidade A', email_responsavel='a@a.test')
        cls.ent_b = Entidade.objects.create(nome='Entidade B', email_responsavel='b@b.test')

        cls.sala_a = Sala.objects.create(nome='Lab A', bloco='1', entidade=cls.ent_a)
        cls.sala_a2 = Sala.objects.create(nome='Biblioteca A', entidade=cls.ent_a)
        cls.sala_b = Sala.objects.create(nome='Lab B', entidade=cls.ent_b)

        cls.disp_a = Dispositivo.objects.create(codigo_qr='A-001', tipo='Computador', marca='Dell', sala=cls.sala_a)
        cls.disp_a2 = Dispositivo.objects.create(codigo_qr='A-002', tipo='Projetor', marca='Epson', sala=cls.sala_a2)
        cls.disp_a_desc = Dispositivo.objects.create(
            codigo_qr='A-003', tipo='Monitor', sala=cls.sala_a, situacao='descartado',
        )
        cls.disp_b = Dispositivo.objects.create(codigo_qr='B-001', tipo='Computador', marca='HP', sala=cls.sala_b)

        def usuario(email, perfil, entidade, nome='Fulano'):
            return Usuario.objects.create_user(
                username=email, email=email, password='Senha@123',
                first_name=nome, perfil=perfil, entidade=entidade,
            )

        cls.comum = usuario('comum@a.test', 'comum', cls.ent_a, 'Carlos')
        cls.comum2 = usuario('comum2@a.test', 'comum', cls.ent_a, 'Clara')
        cls.tecnico_a = usuario('tecnico@a.test', 'tecnico', cls.ent_a, 'Ana')
        cls.admin_a = usuario('admin@a.test', 'admin_entidade', cls.ent_a, 'Bruno')
        cls.tecnico_b = usuario('tecnico@b.test', 'tecnico', cls.ent_b, 'Beto')
        cls.admin_b = usuario('admin@b.test', 'admin_entidade', cls.ent_b, 'Bia')
        cls.admin_geral = usuario('geral@root.test', 'admin_geral', None, 'Root')

    def setUp(self):
        cache.clear()   # zera os contadores de throttle entre os testes

    def como(self, usuario=None):
        client = APIClient()
        if usuario is not None:
            client.force_authenticate(usuario)
        return client

    def abrir(self, usuario=None, dispositivo=None, **extra):
        dados = {'titulo': 'Monitor não liga', 'dispositivo': (dispositivo or self.disp_a).pk, **extra}
        return self.como(usuario or self.comum).post('/api/tickets/', dados, format='json')

    def ler_csv(self, resposta):
        texto = resposta.content.decode('utf-8-sig')
        return list(csv.reader(io.StringIO(texto), delimiter=';'))


class TicketPrioridadeTipoTests(BaseTestCase):
    def test_padrao_e_media_e_outro(self):
        res = self.abrir()
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data['prioridade'], 'media')
        self.assertEqual(res.data['tipo_problema'], 'outro')

    def test_solicitante_informa_prioridade_e_tipo(self):
        res = self.abrir(prioridade='critica', tipo_problema='rede')
        self.assertEqual(res.status_code, 201)
        ticket = Ticket.objects.get(pk=res.data['id'])
        self.assertEqual((ticket.prioridade, ticket.tipo_problema), ('critica', 'rede'))

    def test_valores_invalidos_sao_rejeitados(self):
        self.assertEqual(self.abrir(prioridade='urgentissima').status_code, 400)
        self.assertEqual(self.abrir(tipo_problema='<script>').status_code, 400)

    def test_mudanca_de_prioridade_gera_historico(self):
        ticket_id = self.abrir().data['id']
        res = self.como(self.tecnico_a).patch(f'/api/tickets/{ticket_id}/', {'prioridade': 'alta'}, format='json')
        self.assertEqual(res.status_code, 200)
        registro = HistoricoTicket.objects.get(ticket_id=ticket_id, acao='prioridade')
        self.assertIn('"Média" para "Alta"', registro.descricao)

    def test_usuario_comum_nao_altera_prioridade_depois(self):
        ticket_id = self.abrir().data['id']
        res = self.como(self.comum).patch(f'/api/tickets/{ticket_id}/', {'prioridade': 'critica'}, format='json')
        self.assertEqual(res.status_code, 403)


class TicketCamposProtegidosTests(BaseTestCase):
    """status, tecnico e usuario não podem ser definidos pelo corpo da requisição."""

    def test_criacao_ignora_status_tecnico_e_usuario(self):
        res = self.como(self.comum).post('/api/tickets/', {
            'titulo': 'Monitor não liga', 'dispositivo': self.disp_a.pk,
            'status': 'encerrado', 'tecnico': self.tecnico_a.pk, 'usuario': self.comum2.pk,
        }, format='json')
        self.assertEqual(res.status_code, 201)
        ticket = Ticket.objects.get(pk=res.data['id'])
        self.assertEqual(ticket.status, 'aberto')
        self.assertIsNone(ticket.tecnico)
        self.assertEqual(ticket.usuario, self.comum)

    def test_edicao_nao_muda_status_sem_passar_pelas_acoes(self):
        ticket_id = self.abrir().data['id']
        self.como(self.tecnico_a).patch(
            f'/api/tickets/{ticket_id}/', {'status': 'encerrado', 'usuario': self.comum2.pk}, format='json',
        )
        ticket = Ticket.objects.get(pk=ticket_id)
        self.assertEqual(ticket.status, 'aberto')
        self.assertEqual(ticket.usuario, self.comum)

    def test_titulo_com_quebra_de_linha_e_rejeitado(self):
        res = self.abrir(titulo='Assunto\r\nBcc: vitima@x.test')
        self.assertEqual(res.status_code, 400)
        self.assertIn('titulo', res.data)

    def test_descricao_gigante_e_rejeitada(self):
        self.assertEqual(self.abrir(descricao='a' * 5001).status_code, 400)

    def test_status_nao_textual_nao_gera_erro_500(self):
        ticket_id = self.abrir().data['id']
        res = self.como(self.tecnico_a).post(
            f'/api/tickets/{ticket_id}/atualizar-status/', {'status': 123}, format='json',
        )
        self.assertEqual(res.status_code, 400)

    def test_limite_de_abertura_por_usuario(self):
        with mock.patch.object(AberturaTicketThrottle, 'rate', '2/hour'):
            self.assertEqual(self.abrir().status_code, 201)
            self.assertEqual(self.abrir().status_code, 201)
            self.assertEqual(self.abrir().status_code, 429)
            # o limite é por usuário: outro usuário continua podendo abrir
            self.assertEqual(self.abrir(usuario=self.comum2).status_code, 201)


class AlertaEmailTests(BaseTestCase):
    def test_abertura_avisa_tecnicos_da_entidade(self):
        with self.captureOnCommitCallbacks(execute=True):
            res = self.abrir(prioridade='alta')
        self.assertEqual(res.status_code, 201)

        destinatarios = sorted(m.to[0] for m in mail.outbox)
        self.assertEqual(destinatarios, ['admin@a.test', 'tecnico@a.test'])
        # um e-mail por destinatário: ninguém vê o endereço dos outros
        self.assertTrue(all(len(m.to) == 1 and not m.cc and not m.bcc for m in mail.outbox))
        self.assertIn('Novo chamado', mail.outbox[0].subject)
        self.assertIn('Prioridade: Alta', mail.outbox[0].body)

    def test_abertura_nao_vaza_para_outra_entidade(self):
        with self.captureOnCommitCallbacks(execute=True):
            self.abrir()
        self.assertFalse(any(m.to[0].endswith('@b.test') for m in mail.outbox))

    def test_tecnico_inativo_nao_recebe(self):
        Usuario.objects.filter(pk=self.tecnico_a.pk).update(is_active=False)
        with self.captureOnCommitCallbacks(execute=True):
            self.abrir()
        self.assertEqual([m.to[0] for m in mail.outbox], ['admin@a.test'])

    def test_mudanca_de_status_avisa_o_solicitante(self):
        ticket_id = self.abrir().data['id']
        tecnico = self.como(self.tecnico_a)

        with self.captureOnCommitCallbacks(execute=True):
            tecnico.post(f'/api/tickets/{ticket_id}/assumir/')
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['comum@a.test'])
        self.assertIn('Assumido', mail.outbox[0].subject)

        with self.captureOnCommitCallbacks(execute=True):
            tecnico.post(f'/api/tickets/{ticket_id}/resolver/', {'descricao': 'Cabo trocado.'}, format='json')
        self.assertEqual(len(mail.outbox), 2)
        self.assertIn('Resolvido', mail.outbox[1].subject)
        self.assertIn('Cabo trocado.', mail.outbox[1].body)

    def test_quem_muda_o_status_do_proprio_chamado_nao_recebe_email(self):
        ticket_id = self.abrir(usuario=self.tecnico_a).data['id']
        mail.outbox.clear()
        with self.captureOnCommitCallbacks(execute=True):
            self.como(self.tecnico_a).post(f'/api/tickets/{ticket_id}/assumir/')
        self.assertEqual(mail.outbox, [])

    def test_falha_no_envio_nao_derruba_a_requisicao(self):
        with mock.patch('app.notificacoes.mail.get_connection', side_effect=OSError('SMTP fora do ar')):
            with self.captureOnCommitCallbacks(execute=True):
                res = self.abrir()
        self.assertEqual(res.status_code, 201)
        self.assertTrue(Ticket.objects.filter(pk=res.data['id']).exists())

    def test_assunto_fica_em_uma_linha(self):
        self.assertEqual(_linha('Assunto\r\nBcc: x@y.test'), 'Assunto Bcc: x@y.test')


class ComentarioTests(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.ticket_id = self.abrir().data['id']
        self.url = f'/api/tickets/{self.ticket_id}/comentar/'

    def test_solicitante_e_tecnico_conversam(self):
        res = self.como(self.comum).post(self.url, {'texto': 'O problema voltou.'}, format='json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(res.data['acao'], 'comentario')

        res = self.como(self.tecnico_a).post(self.url, {'texto': 'Vou verificar hoje.'}, format='json')
        self.assertEqual(res.status_code, 201)

        historico = self.como(self.comum).get(f'/api/tickets/{self.ticket_id}/historico/').data
        comentarios = [h for h in historico if h['acao'] == 'comentario']
        self.assertEqual({c['descricao'] for c in comentarios}, {'O problema voltou.', 'Vou verificar hoje.'})
        self.assertEqual({c['usuario_nome'] for c in comentarios}, {'Carlos', 'Ana'})

    def test_outro_usuario_comum_nao_comenta_nem_le(self):
        cliente = self.como(self.comum2)
        self.assertEqual(cliente.post(self.url, {'texto': 'intruso'}, format='json').status_code, 404)
        self.assertEqual(cliente.get(f'/api/tickets/{self.ticket_id}/historico/').status_code, 404)
        self.assertEqual(cliente.get(f'/api/tickets/{self.ticket_id}/').status_code, 404)

    def test_tecnico_de_outra_entidade_nao_comenta(self):
        res = self.como(self.tecnico_b).post(self.url, {'texto': 'intruso'}, format='json')
        self.assertEqual(res.status_code, 404)

    def test_anonimo_nao_comenta(self):
        self.assertEqual(self.como().post(self.url, {'texto': 'x'}, format='json').status_code, 401)

    def test_texto_vazio_ou_longo_demais(self):
        cliente = self.como(self.comum)
        self.assertEqual(cliente.post(self.url, {'texto': '   '}, format='json').status_code, 400)
        self.assertEqual(cliente.post(self.url, {}, format='json').status_code, 400)
        self.assertEqual(cliente.post(self.url, {'texto': 'a' * 2001}, format='json').status_code, 400)

    def test_ticket_encerrado_nao_recebe_comentario(self):
        Ticket.objects.filter(pk=self.ticket_id).update(status='encerrado')
        res = self.como(self.comum).post(self.url, {'texto': 'ainda dá?'}, format='json')
        self.assertEqual(res.status_code, 403)

    def test_comentario_do_tecnico_avisa_o_solicitante(self):
        with self.captureOnCommitCallbacks(execute=True):
            self.como(self.tecnico_a).post(self.url, {'texto': 'Qual o horário?'}, format='json')
        self.assertEqual([m.to for m in mail.outbox], [['comum@a.test']])

    def test_comentario_e_devolvido_como_texto_puro(self):
        # a API não interpreta HTML; quem escapa é o front-end (função esc)
        carga = '<img src=x onerror=alert(1)>'
        res = self.como(self.comum).post(self.url, {'texto': carga}, format='json')
        self.assertEqual(res.data['descricao'], carga)
        self.assertEqual(res['Content-Type'], 'application/json')


class DashboardTests(BaseTestCase):
    def test_usuario_comum_e_anonimo_nao_acessam(self):
        self.assertEqual(self.como().get('/api/dashboard/').status_code, 401)
        self.assertEqual(self.como(self.comum).get('/api/dashboard/').status_code, 403)

    def test_contagens_nao_dependem_da_paginacao(self):
        Ticket.objects.bulk_create(
            Ticket(titulo=f'Chamado {i}', usuario=self.comum, dispositivo=self.disp_a) for i in range(60)
        )
        Ticket.objects.bulk_create(
            Ticket(titulo=f'Em curso {i}', usuario=self.comum, dispositivo=self.disp_a, status='em_andamento')
            for i in range(55)
        )
        dados = self.como(self.tecnico_a).get('/api/dashboard/').data
        self.assertEqual(dados['chamados_aguardando'], 60)
        self.assertEqual(dados['chamados_em_andamento'], 55)
        self.assertEqual(dados['chamados_abertos'], 115)
        self.assertEqual(len(dados['recentes']), 10)

    def test_equipamentos(self):
        dados = self.como(self.tecnico_a).get('/api/dashboard/').data
        self.assertEqual(dados['equipamentos_total'], 3)
        self.assertEqual(dados['equipamentos_ativos'], 2)
        self.assertEqual(dados['equipamentos_inativos'], 1)

    def test_tempo_medio_de_atendimento(self):
        ticket_id = self.abrir().data['id']
        tecnico = self.como(self.tecnico_a)
        tecnico.post(f'/api/tickets/{ticket_id}/assumir/')
        tecnico.post(f'/api/tickets/{ticket_id}/resolver/', {'descricao': 'ok'}, format='json')

        aberto_em = Ticket.objects.get(pk=ticket_id).criado_em
        HistoricoTicket.objects.filter(ticket_id=ticket_id, acao='assumido').update(
            criado_em=aberto_em + timedelta(minutes=30))
        HistoricoTicket.objects.filter(ticket_id=ticket_id, acao='resolvido').update(
            criado_em=aberto_em + timedelta(hours=2))

        self.abrir()   # chamado ainda não assumido: fica fora da média

        dados = tecnico.get('/api/dashboard/').data
        self.assertEqual(dados['tempo_medio_assumir_min'], 30.0)
        self.assertEqual(dados['tempo_medio_resolver_min'], 120.0)
        self.assertEqual(dados['chamados_medidos_assumir'], 1)
        self.assertEqual(dados['chamados_medidos_resolver'], 1)

    def test_sem_chamados_medidos_o_tempo_medio_e_nulo(self):
        dados = self.como(self.tecnico_a).get('/api/dashboard/').data
        self.assertIsNone(dados['tempo_medio_assumir_min'])
        self.assertIsNone(dados['tempo_medio_resolver_min'])

    def test_ranking_e_cortes(self):
        for _ in range(3):
            self.abrir(dispositivo=self.disp_a, tipo_problema='hardware', prioridade='alta')
        self.abrir(dispositivo=self.disp_a2, tipo_problema='rede')

        dados = self.como(self.tecnico_a).get('/api/dashboard/').data
        self.assertEqual([(d['codigo_qr'], d['total']) for d in dados['top_dispositivos']],
                         [('A-001', 3), ('A-002', 1)])
        self.assertEqual([(s['nome'], s['total']) for s in dados['top_salas']],
                         [('Lab A', 3), ('Biblioteca A', 1)])
        self.assertEqual(dados['chamados_por_tipo']['hardware'], 3)
        self.assertEqual(dados['chamados_por_tipo']['rede'], 1)
        self.assertEqual(dados['pendentes_por_prioridade']['alta'], 3)

    def test_isolamento_entre_entidades(self):
        self.abrir(dispositivo=self.disp_a, titulo='Segredo da entidade A')
        dados = self.como(self.tecnico_b).get('/api/dashboard/').data
        self.assertEqual(dados['chamados_abertos'], 0)
        self.assertEqual(dados['recentes'], [])
        self.assertEqual(dados['top_dispositivos'], [])
        self.assertEqual(dados['equipamentos_total'], 1)

        geral = self.como(self.admin_geral).get('/api/dashboard/').data
        self.assertEqual(geral['chamados_abertos'], 1)


class JaReportadoTests(BaseTestCase):
    def test_busca_informa_so_a_contagem(self):
        self.abrir(titulo='Assunto sigiloso')
        self.abrir(titulo='Outro assunto')
        Ticket.objects.create(titulo='Antigo', usuario=self.comum, dispositivo=self.disp_a, status='encerrado')

        res = self.como(self.comum2).get('/api/dispositivos/buscar/?q=A-001')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['chamados_abertos'], 2)
        self.assertNotIn('Assunto sigiloso', str(res.data))

    def test_pagina_do_qr_mostra_aviso_sem_expor_os_chamados(self):
        self.abrir(titulo='Assunto sigiloso')
        html = self.client.get('/r/A-001/').content.decode()
        self.assertIn('já tem 1', html)
        self.assertNotIn('Assunto sigiloso', html)

    def test_pagina_do_qr_sem_chamados_nao_mostra_aviso(self):
        html = self.client.get('/r/A-002/').content.decode()
        self.assertNotIn('chamado em aberto', html)
        self.assertNotIn('chamados em aberto', html)

    def test_codigo_do_qr_e_escapado_na_pagina(self):
        html = self.client.get('/r/%3Cscript%3Ealert(1)%3C%2Fscript%3E/').content.decode()
        self.assertNotIn('<script>alert(1)</script>', html)


class ExportacaoCsvTests(BaseTestCase):
    def test_somente_administradores_exportam(self):
        for url in ('/api/tickets/exportar/', '/api/dispositivos/exportar/'):
            self.assertEqual(self.como().get(url).status_code, 401, url)
            self.assertEqual(self.como(self.comum).get(url).status_code, 403, url)
            self.assertEqual(self.como(self.tecnico_a).get(url).status_code, 403, url)
            self.assertEqual(self.como(self.admin_a).get(url).status_code, 200, url)
            self.assertEqual(self.como(self.admin_geral).get(url).status_code, 200, url)

    def test_csv_de_tickets(self):
        self.abrir(titulo='Teclado com defeito', prioridade='alta', tipo_problema='periferico')
        res = self.como(self.admin_a).get('/api/tickets/exportar/')

        self.assertTrue(res['Content-Type'].startswith('text/csv'))
        self.assertIn('attachment; filename="tickets-', res['Content-Disposition'])
        self.assertEqual(res['X-Content-Type-Options'], 'nosniff')
        self.assertTrue(res.content.startswith(b'\xef\xbb\xbf'))   # BOM para o Excel

        cabecalho, linha = self.ler_csv(res)
        self.assertEqual(cabecalho[:6], ['ID', 'Título', 'Descrição', 'Status', 'Prioridade', 'Tipo de problema'])
        self.assertEqual(linha[1], 'Teclado com defeito')
        self.assertEqual(linha[3:6], ['Aberto', 'Alta', 'Periférico'])
        self.assertEqual(linha[6], 'comum@a.test')
        self.assertEqual(linha[8], 'A-001')

    def test_formulas_sao_neutralizadas(self):
        self.abrir(titulo='=HYPERLINK("http://mal.test","clique")', descricao='@SUM(1+1)')
        self.abrir(titulo='+55 67 99999-0000', descricao='-2+3')
        linhas = self.ler_csv(self.como(self.admin_a).get('/api/tickets/exportar/'))[1:]
        for linha in linhas:
            self.assertTrue(linha[1].startswith("'"), linha[1])
            self.assertTrue(linha[2].startswith("'"), linha[2])

    def test_celula_segura(self):
        for perigoso in ('=1+1', '+1', '-1', '@x', '\tx', '\rx', '\nx'):
            self.assertEqual(celula_segura(perigoso), "'" + perigoso)
        self.assertEqual(celula_segura('Monitor = quebrado'), 'Monitor = quebrado')
        self.assertEqual(celula_segura(None), '')
        self.assertEqual(celula_segura(42), '42')

    def test_exportacao_respeita_a_entidade(self):
        self.abrir(dispositivo=self.disp_a, titulo='Chamado da A')
        self.abrir(usuario=self.tecnico_b, dispositivo=self.disp_b, titulo='Chamado da B')

        titulos_a = [linha[1] for linha in self.ler_csv(self.como(self.admin_a).get('/api/tickets/exportar/'))[1:]]
        self.assertEqual(titulos_a, ['Chamado da A'])

        codigos_b = [linha[1] for linha in self.ler_csv(self.como(self.admin_b).get('/api/dispositivos/exportar/'))[1:]]
        self.assertEqual(codigos_b, ['B-001'])

        todos = self.ler_csv(self.como(self.admin_geral).get('/api/dispositivos/exportar/'))[1:]
        self.assertEqual(len(todos), 4)


class EtiquetasQrLoteTests(BaseTestCase):
    def test_gera_etiquetas_da_sala(self):
        res = self.como(self.tecnico_a).get(f'/api/dispositivos/qr-lote/?sala={self.sala_a.pk}')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['sala'], 'Lab A')
        self.assertFalse(res.data['truncado'])
        # o descartado A-003 fica de fora
        self.assertEqual([e['codigo_qr'] for e in res.data['etiquetas']], ['A-001'])
        self.assertTrue(res.data['etiquetas'][0]['image'].startswith('data:image/png;base64,'))

    def test_sala_de_outra_entidade_nao_e_acessivel(self):
        res = self.como(self.tecnico_a).get(f'/api/dispositivos/qr-lote/?sala={self.sala_b.pk}')
        self.assertEqual(res.status_code, 404)

    def test_parametro_invalido(self):
        tecnico = self.como(self.tecnico_a)
        self.assertEqual(tecnico.get('/api/dispositivos/qr-lote/').status_code, 404)
        self.assertEqual(tecnico.get('/api/dispositivos/qr-lote/?sala=abc').status_code, 404)
        self.assertEqual(tecnico.get("/api/dispositivos/qr-lote/?sala=1' OR '1'='1").status_code, 404)

    def test_usuario_comum_e_anonimo_nao_geram(self):
        url = f'/api/dispositivos/qr-lote/?sala={self.sala_a.pk}'
        self.assertEqual(self.como().get(url).status_code, 401)
        self.assertEqual(self.como(self.comum).get(url).status_code, 403)

    def test_codigo_longo_demais_no_qr_individual(self):
        res = self.como(self.tecnico_a).get('/api/dispositivos/qr-image/?codigo=' + 'A' * 5000)
        self.assertEqual(res.status_code, 400)

    def test_mover_para_sala_de_outra_entidade_e_bloqueado(self):
        res = self.como(self.tecnico_a).post(
            f'/api/dispositivos/{self.disp_a.pk}/mover/', {'sala_id': self.sala_b.pk}, format='json',
        )
        self.assertEqual(res.status_code, 404)
        self.disp_a.refresh_from_db()
        self.assertEqual(self.disp_a.sala, self.sala_a)


class UsuarioPrivilegiosTests(BaseTestCase):
    """Escalada de privilégio pela API de usuários."""

    def novo(self, **extra):
        return {'username': 'novo@x.test', 'email': 'novo@x.test', 'password': 'Senha@123', **extra}

    def test_anonimo_nao_cria_usuario(self):
        res = self.como().post('/api/usuarios/', self.novo(perfil='admin_geral'), format='json')
        self.assertEqual(res.status_code, 401)
        self.assertFalse(Usuario.objects.filter(email='novo@x.test').exists())

    def test_comum_e_tecnico_nao_criam_usuario(self):
        for autor in (self.comum, self.tecnico_a):
            res = self.como(autor).post('/api/usuarios/', self.novo(), format='json')
            self.assertEqual(res.status_code, 403)

    def test_admin_da_entidade_cria_tecnico_na_propria_entidade(self):
        res = self.como(self.admin_a).post('/api/usuarios/', self.novo(perfil='tecnico'), format='json')
        self.assertEqual(res.status_code, 201)
        self.assertEqual(Usuario.objects.get(email='novo@x.test').entidade, self.ent_a)

    def test_admin_da_entidade_nao_concede_perfil_administrativo(self):
        for perfil in ('admin_geral', 'admin_entidade'):
            res = self.como(self.admin_a).post('/api/usuarios/', self.novo(perfil=perfil), format='json')
            self.assertEqual(res.status_code, 400, perfil)

        res = self.como(self.admin_a).patch(
            f'/api/usuarios/{self.tecnico_a.pk}/', {'perfil': 'admin_geral'}, format='json',
        )
        self.assertEqual(res.status_code, 400)
        self.tecnico_a.refresh_from_db()
        self.assertEqual(self.tecnico_a.perfil, 'tecnico')

    def test_admin_da_entidade_nao_se_promove(self):
        res = self.como(self.admin_a).patch(
            f'/api/usuarios/{self.admin_a.pk}/', {'perfil': 'admin_geral'}, format='json',
        )
        self.assertEqual(res.status_code, 400)

    def test_admin_da_entidade_edita_colega_mantendo_o_perfil(self):
        res = self.como(self.admin_a).patch(
            f'/api/usuarios/{self.admin_a.pk}/', {'perfil': 'admin_entidade', 'cargo': 'Coordenador'}, format='json',
        )
        self.assertEqual(res.status_code, 200)

    def test_admin_da_entidade_nao_cria_usuario_em_outra_entidade(self):
        res = self.como(self.admin_a).post(
            '/api/usuarios/', self.novo(perfil='tecnico', entidade=self.ent_b.pk), format='json',
        )
        self.assertEqual(res.status_code, 400)

    def test_admin_da_entidade_nao_alcanca_usuario_de_outra_entidade(self):
        res = self.como(self.admin_a).patch(
            f'/api/usuarios/{self.tecnico_b.pk}/', {'password': 'Tomada@123'}, format='json',
        )
        self.assertEqual(res.status_code, 404)

    def test_admin_da_entidade_nao_altera_nem_exclui_admin_geral(self):
        Usuario.objects.filter(pk=self.admin_geral.pk).update(entidade=self.ent_a)
        cliente = self.como(self.admin_a)

        res = cliente.patch(f'/api/usuarios/{self.admin_geral.pk}/', {'password': 'Tomada@123'}, format='json')
        self.assertEqual(res.status_code, 403)
        self.admin_geral.refresh_from_db()
        self.assertTrue(self.admin_geral.check_password('Senha@123'))

        self.assertEqual(cliente.delete(f'/api/usuarios/{self.admin_geral.pk}/').status_code, 403)
        self.assertTrue(Usuario.objects.filter(pk=self.admin_geral.pk).exists())

    def test_admin_geral_cria_qualquer_perfil(self):
        res = self.como(self.admin_geral).post(
            '/api/usuarios/', self.novo(perfil='admin_entidade', entidade=self.ent_b.pk), format='json',
        )
        self.assertEqual(res.status_code, 201)
        self.assertEqual(Usuario.objects.get(email='novo@x.test').entidade, self.ent_b)

    def test_senha_nunca_e_devolvida(self):
        res = self.como(self.admin_a).get('/api/usuarios/')
        self.assertNotIn('password', res.data['results'][0])
