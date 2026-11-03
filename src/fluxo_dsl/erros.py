"""Erro único da linguagem, sempre com número de linha."""


class ErroFluxo(Exception):
    """Erro de léxico, sintaxe, validação ou cálculo.

    A mensagem final tem sempre o formato "linha N: ...".
    """

    def __init__(self, linha: int, mensagem: str):
        self.linha = linha
        self.mensagem = mensagem
        super().__init__(f"linha {linha}: {mensagem}")
