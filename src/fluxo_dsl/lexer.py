"""Lexer escrito à mão: transforma o texto .fluxo em tokens.

Tipos de token:
  PALAVRA    identificadores e palavras-chave (ex.: principal, price, ao)
  NUMERO     número inteiro ou decimal (ex.: 10000, 2.5, 1,5)
  PERCENTUAL número seguido de % (ex.: 2%, 12,68%)
  DATA       data ISO AAAA-MM-DD
  QUEBRA     fim de linha (só emitido para linhas com conteúdo)
  FIM        fim do arquivo
"""

from dataclasses import dataclass
from decimal import Decimal

from .erros import ErroFluxo


@dataclass(frozen=True)
class Token:
    tipo: str
    valor: str | Decimal
    linha: int
    coluna: int

    def __repr__(self) -> str:
        return f"Token({self.tipo}, {self.valor!r}, {self.linha}:{self.coluna})"


def _eh_letra(c: str) -> bool:
    return c.isalpha() or c == "_"


def _eh_digito(c: str) -> bool:
    return "0" <= c <= "9"


def tokenizar(texto: str) -> list[Token]:
    """Converte o texto em lista de tokens. Levanta ErroFluxo em caractere inválido."""
    tokens: list[Token] = []
    for numero_linha, linha in enumerate(texto.splitlines(), start=1):
        # comentário: tudo após '#'
        pos_comentario = linha.find("#")
        if pos_comentario != -1:
            linha = linha[:pos_comentario]
        if not linha.strip():
            continue  # linha em branco ou só comentário

        i = 0
        n = len(linha)
        inicio_linha = len(tokens)
        while i < n:
            c = linha[i]
            coluna = i + 1
            if c in " \t\r":
                i += 1
                continue

            if _eh_letra(c):
                j = i
                while j < n and (_eh_letra(linha[j]) or _eh_digito(linha[j])):
                    j += 1
                tokens.append(Token("PALAVRA", linha[i:j], numero_linha, coluna))
                i = j
                continue

            if _eh_digito(c):
                j = i
                while j < n and _eh_digito(linha[j]):
                    j += 1
                # data AAAA-MM-DD
                if (j - i == 4 and linha[j:j + 1] == "-"
                        and linha[j + 1:j + 3].isdigit() and linha[j + 3:j + 4] == "-"
                        and linha[j + 4:j + 6].isdigit()):
                    fim = j + 6
                    if fim < n and (_eh_letra(linha[fim]) or _eh_digito(linha[fim])):
                        raise ErroFluxo(numero_linha, f"data mal formada na coluna {coluna}")
                    tokens.append(Token("DATA", linha[i:fim], numero_linha, coluna))
                    i = fim
                    continue
                # parte decimal, aceita ponto ou vírgula
                if j < n and linha[j] in ".," and j + 1 < n and _eh_digito(linha[j + 1]):
                    j += 1
                    while j < n and _eh_digito(linha[j]):
                        j += 1
                texto_numero = linha[i:j].replace(",", ".")
                if j < n and linha[j] == "%":
                    tokens.append(Token("PERCENTUAL", Decimal(texto_numero), numero_linha, coluna))
                    j += 1
                else:
                    tokens.append(Token("NUMERO", Decimal(texto_numero), numero_linha, coluna))
                if j < n and (_eh_letra(linha[j]) or _eh_digito(linha[j])):
                    raise ErroFluxo(numero_linha, f"número mal formado na coluna {coluna}")
                i = j
                continue

            raise ErroFluxo(numero_linha, f"caractere inesperado '{c}' na coluna {coluna}")

        if len(tokens) > inicio_linha:
            tokens.append(Token("QUEBRA", "\n", numero_linha, n + 1))

    ultima = tokens[-1].linha if tokens else 1
    tokens.append(Token("FIM", "", ultima, 1))
    return tokens
