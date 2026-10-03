"""Exportação de relatórios em CSV."""
import csv

from django.http import HttpResponse
from django.utils import timezone

# Excel e LibreOffice executam como fórmula as células que começam com estes caracteres.
_GATILHOS_DE_FORMULA = ('=', '+', '-', '@', '\t', '\r', '\n')


def celula_segura(valor):
    """Neutraliza CSV injection: prefixa com apóstrofo o texto que seria lido como fórmula."""
    if valor is None:
        return ''
    texto = str(valor)
    if texto.startswith(_GATILHOS_DE_FORMULA):
        return "'" + texto
    return texto


def data_local(valor):
    if not valor:
        return ''
    return timezone.localtime(valor).strftime('%d/%m/%Y %H:%M')


def resposta_csv(prefixo, cabecalho, linhas):
    nome = f'{prefixo}-{timezone.localtime():%Y%m%d-%H%M}.csv'
    resposta = HttpResponse(content_type='text/csv; charset=utf-8')
    resposta['Content-Disposition'] = f'attachment; filename="{nome}"'
    resposta['X-Content-Type-Options'] = 'nosniff'
    resposta['Cache-Control'] = 'no-store'
    resposta.write('﻿')  # BOM: o Excel reconhece UTF-8 e exibe os acentos
    escritor = csv.writer(resposta, delimiter=';', quoting=csv.QUOTE_ALL)
    escritor.writerow(cabecalho)
    for linha in linhas:
        escritor.writerow([celula_segura(celula) for celula in linha])
    return resposta
