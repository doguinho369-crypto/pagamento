"""Árvore sintática da linguagem fluxo."""

from dataclasses import dataclass, field
from decimal import Decimal


@dataclass
class Principal:
    valor: Decimal
    linha: int


@dataclass
class Juros:
    taxa: Decimal          # em percentual, ex.: 2 significa 2%
    periodo: str           # "mes" ou "ano"
    linha: int


@dataclass
class Parcelas:
    quantidade: int
    sistema: str           # "price" ou "sac"
    linha: int


@dataclass
class Carencia:
    meses: int
    capitalizada: bool
    linha: int


@dataclass
class Tarifa:
    valor: Decimal
    linha: int


@dataclass
class PrimeiroVencimento:
    data: str              # AAAA-MM-DD (validado depois)
    linha: int


@dataclass
class Programa:
    principal: Principal | None = None
    juros: Juros | None = None
    parcelas: Parcelas | None = None
    carencia: Carencia | None = None
    tarifa: Tarifa | None = None
    primeiro_vencimento: PrimeiroVencimento | None = None
    declaracoes: list = field(default_factory=list)
