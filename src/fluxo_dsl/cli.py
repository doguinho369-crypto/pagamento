"""Interface de linha de comando: python -m fluxo_dsl arquivo.fluxo"""

import argparse
import csv
import io
import sys
from decimal import Decimal

from .erros import ErroFluxo
from .interpretador import Cronograma, executar

LIMITE_PADRAO = 10
CABECALHO = ("numero", "vencimento", "parcela", "juros", "amortizacao", "saldo")


def _dinheiro(v: Decimal) -> str:
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _percentual(fracao: Decimal) -> str:
    return _dinheiro((fracao * 100).quantize(Decimal("0.01"))) + "%"


def formatar_texto(cron: Cronograma, tudo: bool) -> str:
    c = cron.contrato
    saida = io.StringIO()
    p = saida.write
    p(f"Principal:      R$ {_dinheiro(c.principal)}\n")
    p(f"Sistema:        {c.sistema.upper()}, {c.parcelas} parcelas")
    if c.carencia_meses:
        tipo = "capitalizada" if c.carencia_capitalizada else "só juros"
        p(f", carência de {c.carencia_meses} meses ({tipo})")
    p("\n")
    periodo = "mês" if c.periodo_taxa == "mes" else "ano"
    p(f"Juros:          {_percentual(c.taxa_percentual / 100)} ao {periodo}")
    if c.periodo_taxa == "ano":
        p(f" (equivale a {_percentual(cron.taxa_mensal)} ao mês)")
    p("\n")
    if c.tarifa:
        p(f"Tarifa:         R$ {_dinheiro(c.tarifa)} na contratação\n")
    p(f"CET:            {_percentual(cron.cet_mensal)} ao mês / {_percentual(cron.cet_anual)} ao ano\n")
    p(f"Total pago:     R$ {_dinheiro(cron.total_pago)} (juros: R$ {_dinheiro(cron.total_juros)})\n")
    p("\n")

    colunas = ["Nº", "Vencimento", "Parcela", "Juros", "Amortização", "Saldo"]
    linhas = cron.linhas if tudo else cron.linhas[:LIMITE_PADRAO]
    tabela = [[
        str(l.numero) + ("*" if l.carencia else ""),
        l.vencimento.strftime("%d/%m/%Y"),
        _dinheiro(l.parcela), _dinheiro(l.juros), _dinheiro(l.amortizacao), _dinheiro(l.saldo),
    ] for l in linhas]
    larguras = [max(len(colunas[i]), *(len(r[i]) for r in tabela)) for i in range(6)]
    p("  ".join(colunas[i].rjust(larguras[i]) for i in range(6)) + "\n")
    p("  ".join("-" * w for w in larguras) + "\n")
    for r in tabela:
        p("  ".join(r[i].rjust(larguras[i]) for i in range(6)) + "\n")
    ocultas = len(cron.linhas) - len(linhas)
    if ocultas:
        p(f"... {ocultas} linhas ocultas (use --tudo para ver todas)\n")
    if any(l.carencia for l in linhas):
        p("* parcela de carência\n")
    return saida.getvalue()


def formatar_csv(cron: Cronograma, tudo: bool) -> str:
    saida = io.StringIO()
    escritor = csv.writer(saida, lineterminator="\n")
    escritor.writerow(CABECALHO)
    linhas = cron.linhas if tudo else cron.linhas[:LIMITE_PADRAO]
    for l in linhas:
        escritor.writerow([l.numero, l.vencimento.isoformat(), l.parcela, l.juros, l.amortizacao, l.saldo])
    return saida.getvalue()


def montar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m fluxo_dsl",
        description="Gera o cronograma de pagamentos a partir de um arquivo .fluxo",
    )
    parser.add_argument("arquivo", help="caminho do arquivo .fluxo")
    parser.add_argument("--formato", choices=("texto", "csv"), default="texto")
    parser.add_argument("--tudo", action="store_true",
                        help=f"mostra todas as linhas (padrão: {LIMITE_PADRAO})")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = montar_parser().parse_args(argv)
    try:
        with open(args.arquivo, encoding="utf-8") as f:
            texto = f.read()
    except OSError as e:
        print(f"erro: não consegui ler '{args.arquivo}': {e.strerror}", file=sys.stderr)
        return 2
    try:
        cron = executar(texto)
    except ErroFluxo as e:
        print(f"erro: {e}", file=sys.stderr)
        return 1
    formatador = formatar_csv if args.formato == "csv" else formatar_texto
    sys.stdout.write(formatador(cron, args.tudo))
    return 0
