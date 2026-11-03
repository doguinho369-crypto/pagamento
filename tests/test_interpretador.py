from datetime import date
from decimal import Decimal

from fluxo_dsl.interpretador import executar, somar_meses, taxa_mensal_equivalente

PRICE = "principal 10000\njuros 2% ao mes\nparcelas 10 sistema price\nprimeiro_vencimento 2026-12-10\n"
SAC = "principal 10000\njuros 2% ao mes\nparcelas 10 sistema sac\nprimeiro_vencimento 2026-12-10\n"


def test_price_soma_amortizacoes_igual_principal_e_saldo_zero():
    cron = executar(PRICE)
    assert sum(l.amortizacao for l in cron.linhas) == Decimal("10000")
    assert cron.linhas[-1].saldo == Decimal("0")
    assert len(cron.linhas) == 10


def test_price_parcela_fixa_exceto_ajuste_final():
    cron = executar(PRICE)
    parcelas = {l.parcela for l in cron.linhas[:-1]}
    assert len(parcelas) == 1
    # PMT de 10000 a 2% em 10 meses = 1113.27
    assert parcelas.pop() == Decimal("1113.27")
    assert abs(cron.linhas[-1].parcela - Decimal("1113.27")) <= Decimal("0.10")


def test_sac_amortizacao_constante():
    cron = executar(SAC)
    assert {l.amortizacao for l in cron.linhas} == {Decimal("1000.00")}
    assert cron.linhas[-1].saldo == Decimal("0")
    assert cron.linhas[0].parcela > cron.linhas[-1].parcela


def test_taxa_anual_12_68_equivale_a_1_ao_mes():
    mensal = taxa_mensal_equivalente(Decimal("12.68"), "ano")
    assert abs(mensal - Decimal("0.01")) < Decimal("0.00001")
    # dividir por 12 daria 1,0567%, o que seria errado
    assert mensal < Decimal("0.0105")


def test_carencia_2_meses_muda_data_da_primeira_amortizacao():
    sem = executar(PRICE)
    com = executar(PRICE + "carencia 2 meses\n")
    assert sem.linhas[0].vencimento == date(2026, 12, 10)
    assert com.linhas[0].carencia and com.linhas[1].carencia
    assert com.linhas[0].amortizacao == 0 and com.linhas[0].parcela == Decimal("200.00")
    primeira_amortizacao = next(l for l in com.linhas if l.amortizacao > 0)
    assert primeira_amortizacao.vencimento == date(2027, 2, 10)
    assert len(com.linhas) == 12
    assert com.linhas[-1].saldo == 0


def test_carencia_capitalizada_soma_juros_ao_saldo():
    cron = executar(PRICE + "carencia 2 meses capitalizada\n")
    assert cron.linhas[0].parcela == 0
    assert cron.linhas[1].saldo == Decimal("10404.00")
    assert cron.linhas[-1].saldo == 0


def test_dia_31_vira_ultimo_dia_em_meses_curtos():
    assert somar_meses(date(2027, 1, 31), 1) == date(2027, 2, 28)
    assert somar_meses(date(2027, 1, 31), 2) == date(2027, 3, 31)
    assert somar_meses(date(2027, 1, 31), 3) == date(2027, 4, 30)
    assert somar_meses(date(2028, 1, 31), 1) == date(2028, 2, 29)  # bissexto
    cron = executar(PRICE.replace("2026-12-10", "2027-01-31"))
    assert [l.vencimento for l in cron.linhas[:3]] == [
        date(2027, 1, 31), date(2027, 2, 28), date(2027, 3, 31)]


def test_cet_com_tarifa_e_maior_que_taxa_informada():
    sem = executar(PRICE)
    com = executar(PRICE + "tarifa 150 na contratacao\n")
    assert abs(sem.cet_mensal - Decimal("0.02")) < Decimal("0.0001")
    assert com.cet_mensal > Decimal("0.02")
    assert com.cet_anual > sem.cet_anual


def test_juros_zero_nao_quebra():
    cron = executar(PRICE.replace("2%", "0%"))
    assert {l.parcela for l in cron.linhas} == {Decimal("1000.00")}
    assert cron.cet_mensal == 0
