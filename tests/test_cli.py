from fluxo_dsl.cli import main

PRICE = "principal 10000\njuros 2% ao mes\nparcelas 24 sistema price\nprimeiro_vencimento 2026-12-10\n"


def escrever(tmp_path, texto, nome="c.fluxo"):
    arq = tmp_path / nome
    arq.write_text(texto, encoding="utf-8")
    return str(arq)


def test_texto_mostra_no_maximo_10_linhas(tmp_path, capsys):
    assert main([escrever(tmp_path, PRICE)]) == 0
    saida = capsys.readouterr().out
    assert "CET:" in saida
    assert "14 linhas ocultas" in saida
    assert "10/12/2026" in saida


def test_tudo_mostra_todas(tmp_path, capsys):
    assert main([escrever(tmp_path, PRICE), "--tudo"]) == 0
    saida = capsys.readouterr().out
    assert "ocultas" not in saida
    assert "10/11/2028" in saida


def test_csv(tmp_path, capsys):
    assert main([escrever(tmp_path, PRICE), "--formato", "csv", "--tudo"]) == 0
    linhas = capsys.readouterr().out.splitlines()
    assert linhas[0] == "numero,vencimento,parcela,juros,amortizacao,saldo"
    assert len(linhas) == 25
    assert linhas[-1].endswith(",0.00")


def test_erro_vai_para_stderr_com_linha(tmp_path, capsys):
    arq = escrever(tmp_path, "principal 100\njuros 2% ao mes\nparcelas 5 sistema bullet\n")
    assert main([arq]) == 1
    err = capsys.readouterr().err
    assert err.strip() == "erro: linha 3: 'sistema' precisa ser price ou sac"
    assert "Traceback" not in err


def test_arquivo_inexistente(tmp_path, capsys):
    assert main([str(tmp_path / "nao_existe.fluxo")]) == 2
    assert "não consegui ler" in capsys.readouterr().err
