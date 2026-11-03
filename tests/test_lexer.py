from decimal import Decimal

import pytest

from fluxo_dsl.erros import ErroFluxo
from fluxo_dsl.lexer import tokenizar


def tipos(texto):
    return [t.tipo for t in tokenizar(texto)]


def test_tokens_basicos_com_linha_e_coluna():
    toks = tokenizar("principal 10000\njuros 2% ao mes\n")
    assert (toks[0].tipo, toks[0].valor, toks[0].linha, toks[0].coluna) == ("PALAVRA", "principal", 1, 1)
    assert (toks[1].tipo, toks[1].valor, toks[1].coluna) == ("NUMERO", Decimal("10000"), 11)
    assert toks[2].tipo == "QUEBRA"
    assert (toks[4].tipo, toks[4].valor, toks[4].linha, toks[4].coluna) == ("PERCENTUAL", Decimal("2"), 2, 7)
    assert toks[-1].tipo == "FIM"


def test_percentual_com_virgula_decimal():
    toks = tokenizar("juros 12,68% ao ano")
    assert toks[1].tipo == "PERCENTUAL"
    assert toks[1].valor == Decimal("12.68")


def test_data_iso():
    toks = tokenizar("primeiro_vencimento 2026-12-10")
    assert toks[1].tipo == "DATA"
    assert toks[1].valor == "2026-12-10"


def test_comentarios_e_linhas_em_branco_sao_ignorados():
    texto = "# cabeçalho\n\nprincipal 100  # inline\n\n   \n"
    assert tipos(texto) == ["PALAVRA", "NUMERO", "QUEBRA", "FIM"]
    assert tokenizar(texto)[0].linha == 3


def test_caractere_invalido_aponta_linha():
    with pytest.raises(ErroFluxo) as info:
        tokenizar("principal 100\njuros 2% @ mes")
    assert str(info.value) == "linha 2: caractere inesperado '@' na coluna 10"
