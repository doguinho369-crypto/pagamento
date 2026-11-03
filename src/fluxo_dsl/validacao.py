"""Validação semântica: campos obrigatórios, faixas de valores, datas reais."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from . import ast
from .erros import ErroFluxo


@dataclass(frozen=True)
class Contrato:
    """Programa validado, pronto para o interpretador."""

    principal: Decimal
    taxa_percentual: Decimal
    periodo_taxa: str            # "mes" ou "ano"
    parcelas: int
    sistema: str                 # "price" ou "sac"
    carencia_meses: int
    carencia_capitalizada: bool
    tarifa: Decimal
    primeiro_vencimento: date


def validar(prog: ast.Programa) -> Contrato:
    ultima_linha = prog.declaracoes[-1].linha if prog.declaracoes else 1

    for campo in ("principal", "juros", "parcelas", "primeiro_vencimento"):
        if getattr(prog, campo) is None:
            raise ErroFluxo(ultima_linha, f"falta declarar '{campo}'")

    assert prog.principal and prog.juros and prog.parcelas and prog.primeiro_vencimento

    if prog.principal.valor <= 0:
        raise ErroFluxo(prog.principal.linha, "'principal' precisa ser maior que zero")
    if prog.juros.taxa < 0:
        raise ErroFluxo(prog.juros.linha, "'juros' não pode ser negativo")
    if prog.parcelas.quantidade < 1:
        raise ErroFluxo(prog.parcelas.linha, "'parcelas' precisa ser pelo menos 1")

    carencia_meses = 0
    carencia_capitalizada = False
    if prog.carencia is not None:
        if prog.carencia.meses < 0:
            raise ErroFluxo(prog.carencia.linha, "'carencia' não pode ser negativa")
        carencia_meses = prog.carencia.meses
        carencia_capitalizada = prog.carencia.capitalizada

    tarifa = Decimal("0")
    if prog.tarifa is not None:
        if prog.tarifa.valor < 0:
            raise ErroFluxo(prog.tarifa.linha, "'tarifa' não pode ser negativa")
        if prog.tarifa.valor >= prog.principal.valor:
            raise ErroFluxo(prog.tarifa.linha, "'tarifa' precisa ser menor que o principal")
        tarifa = prog.tarifa.valor

    try:
        primeiro = date.fromisoformat(prog.primeiro_vencimento.data)
    except ValueError:
        raise ErroFluxo(
            prog.primeiro_vencimento.linha,
            f"'{prog.primeiro_vencimento.data}' não é uma data válida",
        ) from None

    return Contrato(
        principal=prog.principal.valor,
        taxa_percentual=prog.juros.taxa,
        periodo_taxa=prog.juros.periodo,
        parcelas=prog.parcelas.quantidade,
        sistema=prog.parcelas.sistema,
        carencia_meses=carencia_meses,
        carencia_capitalizada=carencia_capitalizada,
        tarifa=tarifa,
        primeiro_vencimento=primeiro,
    )
