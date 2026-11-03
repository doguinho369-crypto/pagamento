"""Parser descendente recursivo escrito à mão.

Gramática (uma declaração por linha):

  programa      := { declaracao QUEBRA } FIM
  declaracao    := principal | juros | parcelas | carencia | tarifa | vencimento
  principal     := "principal" NUMERO
  juros         := "juros" PERCENTUAL "ao" ("mes" | "ano")
  parcelas      := "parcelas" NUMERO "sistema" ("price" | "sac")
  carencia      := "carencia" NUMERO "meses" ["capitalizada"]
  tarifa        := "tarifa" NUMERO "na" "contratacao"
  vencimento    := "primeiro_vencimento" DATA
"""

from decimal import Decimal

from . import ast
from .erros import ErroFluxo
from .lexer import Token, tokenizar

COMANDOS = ("principal", "juros", "parcelas", "carencia", "tarifa", "primeiro_vencimento")


class _Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    # --- utilitários -----------------------------------------------------
    def atual(self) -> Token:
        return self.tokens[self.pos]

    def avancar(self) -> Token:
        tok = self.tokens[self.pos]
        self.pos += 1
        return tok

    def esperar_tipo(self, tipo: str, descricao: str) -> Token:
        tok = self.atual()
        if tok.tipo != tipo:
            raise ErroFluxo(tok.linha, f"esperava {descricao}, encontrei {_descrever(tok)}")
        return self.avancar()

    def esperar_palavra(self, palavra: str) -> Token:
        tok = self.atual()
        if tok.tipo != "PALAVRA" or tok.valor != palavra:
            raise ErroFluxo(tok.linha, f"esperava '{palavra}', encontrei {_descrever(tok)}")
        return self.avancar()

    def esperar_opcao(self, campo: str, opcoes: tuple[str, ...]) -> str:
        tok = self.atual()
        texto = " ou ".join(opcoes)
        if tok.tipo != "PALAVRA" or tok.valor not in opcoes:
            raise ErroFluxo(tok.linha, f"'{campo}' precisa ser {texto}")
        self.avancar()
        return str(tok.valor)

    def esperar_inteiro(self, campo: str) -> int:
        tok = self.esperar_tipo("NUMERO", f"um número em '{campo}'")
        valor: Decimal = tok.valor  # type: ignore[assignment]
        if valor != valor.to_integral_value():
            raise ErroFluxo(tok.linha, f"'{campo}' precisa ser um número inteiro")
        return int(valor)

    def fim_de_declaracao(self) -> None:
        tok = self.atual()
        if tok.tipo == "QUEBRA":
            self.avancar()
        elif tok.tipo != "FIM":
            raise ErroFluxo(tok.linha, f"texto inesperado no fim da linha: {_descrever(tok)}")

    # --- gramática -------------------------------------------------------
    def programa(self) -> ast.Programa:
        prog = ast.Programa()
        while self.atual().tipo != "FIM":
            decl = self.declaracao()
            self.fim_de_declaracao()
            self._registrar(prog, decl)
        return prog

    def _registrar(self, prog: ast.Programa, decl) -> None:
        nome = {
            ast.Principal: "principal",
            ast.Juros: "juros",
            ast.Parcelas: "parcelas",
            ast.Carencia: "carencia",
            ast.Tarifa: "tarifa",
            ast.PrimeiroVencimento: "primeiro_vencimento",
        }[type(decl)]
        if getattr(prog, nome) is not None:
            raise ErroFluxo(decl.linha, f"'{nome}' já foi declarado antes")
        setattr(prog, nome, decl)
        prog.declaracoes.append(decl)

    def declaracao(self):
        tok = self.atual()
        if tok.tipo != "PALAVRA":
            raise ErroFluxo(tok.linha, f"esperava um comando, encontrei {_descrever(tok)}")
        comando = str(tok.valor)
        if comando == "principal":
            return self.principal()
        if comando == "juros":
            return self.juros()
        if comando == "parcelas":
            return self.parcelas()
        if comando == "carencia":
            return self.carencia()
        if comando == "tarifa":
            return self.tarifa()
        if comando == "primeiro_vencimento":
            return self.primeiro_vencimento()
        raise ErroFluxo(
            tok.linha,
            f"comando desconhecido '{comando}'; use um de: {', '.join(COMANDOS)}",
        )

    def principal(self) -> ast.Principal:
        linha = self.avancar().linha
        tok = self.esperar_tipo("NUMERO", "um valor em 'principal'")
        return ast.Principal(tok.valor, linha)  # type: ignore[arg-type]

    def juros(self) -> ast.Juros:
        linha = self.avancar().linha
        tok = self.esperar_tipo("PERCENTUAL", "um percentual em 'juros' (ex.: 2%)")
        self.esperar_palavra("ao")
        periodo = self.esperar_opcao("juros", ("mes", "ano"))
        return ast.Juros(tok.valor, periodo, linha)  # type: ignore[arg-type]

    def parcelas(self) -> ast.Parcelas:
        linha = self.avancar().linha
        quantidade = self.esperar_inteiro("parcelas")
        self.esperar_palavra("sistema")
        sistema = self.esperar_opcao("sistema", ("price", "sac"))
        return ast.Parcelas(quantidade, sistema, linha)

    def carencia(self) -> ast.Carencia:
        linha = self.avancar().linha
        meses = self.esperar_inteiro("carencia")
        self.esperar_opcao("carencia", ("meses", "mes"))
        capitalizada = False
        tok = self.atual()
        if tok.tipo == "PALAVRA" and tok.valor == "capitalizada":
            self.avancar()
            capitalizada = True
        return ast.Carencia(meses, capitalizada, linha)

    def tarifa(self) -> ast.Tarifa:
        linha = self.avancar().linha
        tok = self.esperar_tipo("NUMERO", "um valor em 'tarifa'")
        self.esperar_palavra("na")
        self.esperar_palavra("contratacao")
        return ast.Tarifa(tok.valor, linha)  # type: ignore[arg-type]

    def primeiro_vencimento(self) -> ast.PrimeiroVencimento:
        linha = self.avancar().linha
        tok = self.esperar_tipo("DATA", "uma data AAAA-MM-DD em 'primeiro_vencimento'")
        return ast.PrimeiroVencimento(str(tok.valor), linha)


def _descrever(tok: Token) -> str:
    if tok.tipo == "QUEBRA":
        return "fim da linha"
    if tok.tipo == "FIM":
        return "fim do arquivo"
    if tok.tipo == "PERCENTUAL":
        return f"'{tok.valor}%'"
    return f"'{tok.valor}'"


def analisar(texto: str) -> ast.Programa:
    """Texto .fluxo -> Programa (AST). Não valida semântica, só sintaxe."""
    return _Parser(tokenizar(texto)).programa()
