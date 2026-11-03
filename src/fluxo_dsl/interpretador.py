"""Interpretador: transforma um Contrato validado no cronograma de pagamentos.

Todo dinheiro é Decimal. Arredondamento comercial (meio para cima) em 2 casas.
"""

import calendar
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal, getcontext

from .validacao import Contrato

getcontext().prec = 28

CENTAVO = Decimal("0.01")
UM = Decimal("1")
CEM = Decimal("100")
DOZE = Decimal("12")


def arredondar(valor: Decimal) -> Decimal:
    return valor.quantize(CENTAVO, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Linha:
    numero: int
    vencimento: date
    parcela: Decimal
    juros: Decimal
    amortizacao: Decimal
    saldo: Decimal
    carencia: bool = False


@dataclass(frozen=True)
class Cronograma:
    contrato: Contrato
    taxa_mensal: Decimal          # fração, ex.: 0.02
    linhas: list[Linha]
    cet_mensal: Decimal           # fração
    cet_anual: Decimal            # fração

    @property
    def total_pago(self) -> Decimal:
        return sum((l.parcela for l in self.linhas), Decimal("0"))

    @property
    def total_juros(self) -> Decimal:
        return sum((l.juros for l in self.linhas), Decimal("0"))


# --- taxas ---------------------------------------------------------------

def taxa_mensal_equivalente(taxa_percentual: Decimal, periodo: str) -> Decimal:
    """Converte a taxa informada em taxa mensal (fração) pela taxa equivalente.

    ao mes: i
    ao ano: (1 + i_a) ** (1/12) - 1   (capitalização composta, nunca i_a / 12)
    """
    fracao = taxa_percentual / CEM
    if periodo == "mes":
        return fracao
    if fracao == 0:
        return Decimal("0")
    return (UM + fracao) ** (UM / DOZE) - UM


def mensal_para_anual(taxa_mensal: Decimal) -> Decimal:
    return (UM + taxa_mensal) ** 12 - UM


# --- datas ---------------------------------------------------------------

def somar_meses(base: date, meses: int) -> date:
    """Soma meses mantendo o dia; se o mês não tiver esse dia, usa o último dia."""
    indice = base.year * 12 + (base.month - 1) + meses
    ano, mes = divmod(indice, 12)
    mes += 1
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    return date(ano, mes, min(base.day, ultimo_dia))


# --- cronograma ----------------------------------------------------------

def gerar_cronograma(c: Contrato) -> Cronograma:
    i = taxa_mensal_equivalente(c.taxa_percentual, c.periodo_taxa)
    linhas: list[Linha] = []
    saldo = arredondar(c.principal)
    numero = 0

    # carência: só juros, ou juros capitalizados no saldo
    for _ in range(c.carencia_meses):
        numero += 1
        juros = arredondar(saldo * i)
        if c.carencia_capitalizada:
            saldo = saldo + juros
            parcela = Decimal("0.00")
        else:
            parcela = juros
        linhas.append(Linha(numero, somar_meses(c.primeiro_vencimento, numero - 1),
                            parcela, juros, Decimal("0.00"), saldo, carencia=True))

    n = c.parcelas
    saldo_inicial = saldo
    if c.sistema == "price":
        if i == 0:
            parcela_fixa = arredondar(saldo_inicial / n)
        else:
            fator = (UM + i) ** n
            parcela_fixa = arredondar(saldo_inicial * i * fator / (fator - UM))
    else:
        amortizacao_fixa = arredondar(saldo_inicial / n)

    for k in range(1, n + 1):
        numero += 1
        juros = arredondar(saldo * i)
        if k == n:
            amortizacao = saldo            # ajuste final: saldo fecha em zero
        elif c.sistema == "price":
            amortizacao = parcela_fixa - juros
        else:
            amortizacao = amortizacao_fixa
        parcela = amortizacao + juros
        saldo = saldo - amortizacao
        linhas.append(Linha(numero, somar_meses(c.primeiro_vencimento, numero - 1),
                            parcela, juros, amortizacao, saldo))

    cet_m = calcular_cet(c.principal - c.tarifa, [l.parcela for l in linhas])
    return Cronograma(c, i, linhas, cet_m, mensal_para_anual(cet_m))


# --- CET -----------------------------------------------------------------

def valor_presente(fluxos: list[Decimal], taxa: Decimal) -> Decimal:
    total = Decimal("0")
    fator = UM
    for pagamento in fluxos:
        fator = fator * (UM + taxa)
        total += pagamento / fator
    return total


def calcular_cet(liquido_recebido: Decimal, pagamentos: list[Decimal],
                 tolerancia: Decimal = Decimal("1e-12"), max_iteracoes: int = 200) -> Decimal:
    """Taxa mensal que iguala o valor presente dos pagamentos ao valor líquido recebido.

    Bisseção: f(taxa) = VP(pagamentos, taxa) - liquido é decrescente em taxa.
    """
    if sum(pagamentos) <= liquido_recebido:
        return Decimal("0")
    baixo = Decimal("0")
    alto = UM  # 100% ao mês é teto mais que suficiente
    while valor_presente(pagamentos, alto) > liquido_recebido:
        alto *= 2
    for _ in range(max_iteracoes):
        meio = (baixo + alto) / 2
        if valor_presente(pagamentos, meio) > liquido_recebido:
            baixo = meio
        else:
            alto = meio
        if alto - baixo < tolerancia:
            break
    return (baixo + alto) / 2


def executar(texto: str) -> Cronograma:
    """Atalho: texto .fluxo -> cronograma."""
    from .parser import analisar
    from .validacao import validar

    return gerar_cronograma(validar(analisar(texto)))
