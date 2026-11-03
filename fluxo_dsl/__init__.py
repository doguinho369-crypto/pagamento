"""Atalho para rodar `python -m fluxo_dsl` direto da raiz do repositório,
sem instalar nada. O código real fica em src/fluxo_dsl: este pacote só
aponta o caminho de busca para lá.
"""

import os

__path__ = [os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src", "fluxo_dsl")]

from .erros import ErroFluxo  # noqa: E402

__all__ = ["ErroFluxo"]
