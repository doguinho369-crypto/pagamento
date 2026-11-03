from datetime import date
from decimal import Decimal

import pytest

from fluxo_dsl.erros import ErroFluxo
from fluxo_dsl.parser import analisar
from fluxo_dsl.validacao import validar

BASE = "principal 10000\njuros 2% ao mes\nparcelas 10 sistema price\nprimeiro_vencimento 2026-12-10\n"


def test_contrato_valido_com_padroes():
    c = validar(analisar(BASE))
    assert c.principal == Decimal("10000")
    assert c.carencia_meses == 0
    assert c.tarifa == Decimal("0")
    assert c.primeiro_vencimento == date(2026, 12, 10)


@pytest.mark.parametrize("texto, esperado", [
    ("principal 10000\njuros 2% ao mes\nparcelas 10 sistema price",
     "linha 3: falta declarar 'primeiro_vencimento'"),
    ("principal 0\njuros 2% ao mes\nparcelas 10 sistema price\nprimeiro_vencimento 2026-12-10",
     "linha 1: 'principal' precisa ser maior que zero"),
    ("principal 100\njuros 2% ao mes\nparcelas 0 sistema price\nprimeiro_vencimento 2026-12-10",
     "linha 3: 'parcelas' precisa ser pelo menos 1"),
    ("principal 100\njuros 2% ao mes\nparcelas 10 sistema price\nprimeiro_vencimento 2026-02-30",
     "linha 4: '2026-02-30' não é uma data válida"),
    (BASE + "tarifa 20000 na contratacao",
     "linha 5: 'tarifa' precisa ser menor que o principal"),
])
def test_erros_de_validacao_apontam_linha(texto, esperado):
    with pytest.raises(ErroFluxo) as info:
        validar(analisar(texto))
    assert str(info.value) == esperado
