from pathlib import Path

import pytest

from fluxo_dsl.cli import main

EXEMPLOS = Path(__file__).resolve().parent.parent / "exemplos"


@pytest.mark.parametrize("nome", ["price_simples", "sac_simples", "com_carencia", "com_tarifa"])
def test_exemplos_validos_rodam(nome, capsys):
    assert main([str(EXEMPLOS / f"{nome}.fluxo"), "--tudo"]) == 0
    assert "      0,00\n" in capsys.readouterr().out  # saldo final zero


@pytest.mark.parametrize("nome, mensagem", [
    ("erro_sistema", "erro: linha 4: 'sistema' precisa ser price ou sac"),
    ("erro_falta_campo", "erro: linha 4: falta declarar 'primeiro_vencimento'"),
])
def test_exemplos_com_erro(nome, mensagem, capsys):
    assert main([str(EXEMPLOS / f"{nome}.fluxo")]) == 1
    assert capsys.readouterr().err.strip() == mensagem
