from decimal import Decimal

import pytest

from fluxo_dsl import ast
from fluxo_dsl.erros import ErroFluxo
from fluxo_dsl.parser import analisar

EXEMPLO = """
# contrato de teste
principal 10000
juros 2% ao mes
parcelas 10 sistema price
carencia 2 meses capitalizada
tarifa 150 na contratacao
primeiro_vencimento 2026-12-10
"""


def test_monta_ast_completa():
    prog = analisar(EXEMPLO)
    assert prog.principal == ast.Principal(Decimal("10000"), 3)
    assert prog.juros == ast.Juros(Decimal("2"), "mes", 4)
    assert prog.parcelas == ast.Parcelas(10, "price", 5)
    assert prog.carencia == ast.Carencia(2, True, 6)
    assert prog.tarifa == ast.Tarifa(Decimal("150"), 7)
    assert prog.primeiro_vencimento == ast.PrimeiroVencimento("2026-12-10", 8)
    assert len(prog.declaracoes) == 6


def test_carencia_sem_capitalizada():
    prog = analisar("carencia 3 meses")
    assert prog.carencia.capitalizada is False


@pytest.mark.parametrize("texto, esperado", [
    ("principal 100\njuros 2% ao mes\nparcelas 10 sistema bullet",
     "linha 3: 'sistema' precisa ser price ou sac"),
    ("principal 100\njuros 2 ao mes",
     "linha 2: esperava um percentual em 'juros' (ex.: 2%), encontrei '2'"),
    ("principal 100\njuros 2% ao dia",
     "linha 2: 'juros' precisa ser mes ou ano"),
    ("principal 100\nprincipal 200",
     "linha 2: 'principal' já foi declarado antes"),
    ("valor 100",
     "linha 1: comando desconhecido 'valor'; use um de: principal, juros, parcelas, carencia, tarifa, primeiro_vencimento"),
    ("principal 100 reais",
     "linha 1: texto inesperado no fim da linha: 'reais'"),
    ("parcelas 2.5 sistema price",
     "linha 1: 'parcelas' precisa ser um número inteiro"),
    ("primeiro_vencimento dezembro",
     "linha 1: esperava uma data AAAA-MM-DD em 'primeiro_vencimento', encontrei 'dezembro'"),
    ("primeiro_vencimento 10/12/2026",
     "linha 1: caractere inesperado '/' na coluna 23"),
])
def test_erros_de_sintaxe_apontam_linha(texto, esperado):
    with pytest.raises(ErroFluxo) as info:
        analisar(texto)
    assert str(info.value) == esperado
