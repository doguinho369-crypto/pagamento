# fluxo-dsl

Mini linguagem para descrever um financiamento em um arquivo de texto e gerar
o cronograma de pagamentos (tabela Price ou SAC), com carência, tarifa e CET.

Só Python 3.10+ e biblioteca padrão. Lexer e parser escritos à mão, sem
bibliotecas de parsing. Todo cálculo de dinheiro usa `Decimal`.

## Como usar

Da raiz do repositório, sem instalar nada:

```
python -m fluxo_dsl exemplos/price_simples.fluxo
python -m fluxo_dsl exemplos/sac_simples.fluxo --tudo
python -m fluxo_dsl exemplos/sac_simples.fluxo --formato csv --tudo
```

Opções:

- `--formato texto` (padrão) ou `--formato csv`
- `--tudo` mostra todas as linhas; por padrão aparecem no máximo 10

Para usar de qualquer pasta: `pip install -e .`

Testes: `pip install pytest` e depois `python -m pytest`

## A linguagem

Um arquivo `.fluxo` tem uma declaração por linha. Comentários começam com
`#` e linhas em branco são ignoradas. Números aceitam ponto ou vírgula
decimal (`12.68%` ou `12,68%`).

```
principal 10000
juros 2% ao mes
parcelas 10 sistema price
carencia 2 meses
tarifa 150 na contratacao
primeiro_vencimento 2026-12-10
```

Obrigatórios: `principal`, `juros`, `parcelas`, `primeiro_vencimento`.
Opcionais: `carencia` (com ou sem `capitalizada`) e `tarifa`.
Cada declaração só pode aparecer uma vez.

### Gramática

```
programa      := { declaracao QUEBRA } FIM
declaracao    := principal | juros | parcelas | carencia | tarifa | vencimento
principal     := "principal" NUMERO
juros         := "juros" PERCENTUAL "ao" ("mes" | "ano")
parcelas      := "parcelas" NUMERO "sistema" ("price" | "sac")
carencia      := "carencia" NUMERO ("meses" | "mes") ["capitalizada"]
tarifa        := "tarifa" NUMERO "na" "contratacao"
vencimento    := "primeiro_vencimento" DATA

NUMERO        := digitos [("." | ",") digitos]
PERCENTUAL    := NUMERO "%"
DATA          := AAAA "-" MM "-" DD
```

Tokens: `PALAVRA`, `NUMERO`, `PERCENTUAL`, `DATA`, `QUEBRA`, `FIM`.
Cada token guarda linha e coluna, usadas nas mensagens de erro.

### Semântica

- **price**: parcela fixa calculada pela fórmula PMT; os juros caem e a
  amortização sobe a cada mês.
- **sac**: amortização constante (saldo / parcelas); a parcela cai a cada mês.
- **juros ao ano**: convertidos para o mês pela taxa equivalente
  `(1 + i_ano)^(1/12) - 1`.
- **carencia N meses**: as N primeiras linhas pagam só os juros; a amortização
  começa na linha N+1. Com `capitalizada`, nada é pago na carência e os juros
  são somados ao saldo devedor.
- **tarifa**: não entra no cronograma; reduz o valor líquido recebido e por
  isso aumenta o CET.
- **CET**: taxa mensal (e anual equivalente) que iguala o valor presente de
  todas as parcelas ao valor líquido recebido (principal − tarifa). Calculado
  por bisseção.
- **vencimentos**: mensais, mantendo o dia do primeiro vencimento. Se o mês
  não tiver esse dia (31 em fevereiro), usa o último dia do mês. O dia
  original volta a valer nos meses seguintes.
- **arredondamento**: cada linha é arredondada a centavos (meio para cima);
  a última parcela absorve a diferença para o saldo fechar exatamente em zero.

## Exemplo de saída real

`python -m fluxo_dsl exemplos/com_tarifa.fluxo`:

```
Principal:      R$ 10.000,00
Sistema:        PRICE, 10 parcelas
Juros:          2,00% ao mes
Tarifa:         R$ 150,00 na contratação
CET:            2,29% ao mês / 31,22% ao ano
Total pago:     R$ 11.132,65 (juros: R$ 1.132,65)

Nº  Vencimento   Parcela   Juros  Amortização     Saldo
--  ----------  --------  ------  -----------  --------
 1  10/12/2026  1.113,27  200,00       913,27  9.086,73
 2  10/01/2027  1.113,27  181,73       931,54  8.155,19
 3  10/02/2027  1.113,27  163,10       950,17  7.205,02
 4  10/03/2027  1.113,27  144,10       969,17  6.235,85
 5  10/04/2027  1.113,27  124,72       988,55  5.247,30
 6  10/05/2027  1.113,27  104,95     1.008,32  4.238,98
 7  10/06/2027  1.113,27   84,78     1.028,49  3.210,49
 8  10/07/2027  1.113,27   64,21     1.049,06  2.161,43
 9  10/08/2027  1.113,27   43,23     1.070,04  1.091,39
10  10/09/2027  1.113,22   21,83     1.091,39      0,00
```

Com erro, `python -m fluxo_dsl exemplos/erro_sistema.fluxo`:

```
erro: linha 4: 'sistema' precisa ser price ou sac
```

O programa sai com código 1 em erro de linguagem e 2 se não lê o arquivo.
Nunca mostra traceback do Python.

## Estrutura

```
src/fluxo_dsl/
  lexer.py          texto -> tokens (linha e coluna)
  parser.py         tokens -> AST (ast.py), erros de sintaxe
  validacao.py      AST -> Contrato validado, erros semânticos
  interpretador.py  Contrato -> Cronograma (price, sac, carência, datas, CET)
  cli.py            linha de comando, formatos texto e csv
  erros.py          ErroFluxo, sempre "linha N: mensagem"
exemplos/           4 arquivos válidos + 2 com erro de propósito
tests/              pytest, um arquivo por módulo
```

## Decisões técnicas

**Por que Decimal.** Float não representa 0,10 com exatidão; em dezenas de
linhas o erro acumula e o saldo final vira −0,01 ou 0,02. Decimal faz
aritmética decimal exata, com arredondamento explícito (ROUND_HALF_UP) só
onde a gente quer: na hora de gravar cada linha. Potências fracionárias
(taxa equivalente) também são feitas em Decimal com 28 dígitos.

**Por que taxa equivalente.** Dividir 12,68% a.a. por 12 daria 1,057% a.m.,
mas 1,057% composto por 12 meses rende 13,4% ao ano, não 12,68%. A taxa
equivalente `(1+i)^(1/12) − 1` é a que, capitalizada mês a mês, reproduz
exatamente a taxa anual informada — e é como o mercado brasileiro converte.

**Por que bisseção no CET.** A função valor presente é monótona na taxa,
então a bisseção converge sempre, sem derivada e sem risco de divergir como
Newton. 200 iterações com tolerância 1e-12 é mais que o bastante.

**Por que parser à mão.** A gramática é pequena e linear (uma declaração por
linha), então um descendente recursivo cabe em um arquivo e dá mensagens de
erro sob medida, com a linha certa.

## Limites conhecidos

- Só periodicidade mensal; não há parcelas quinzenais, anuais nem datas
  irregulares.
- O CET considera só a tarifa de contratação; não há IOF, seguros nem
  tarifas mensais.
- A taxa de juros é fixa; não há indexadores (TR, IPCA, CDI).
- Não há pagamento extraordinário, entrada nem balão.
- Carência capitalizada aparece no cronograma com parcela 0 e amortização 0,
  com o saldo crescendo (não como amortização negativa).
- O CET é por "mês cheio": não leva em conta o número real de dias entre
  vencimentos.
- O `--formato csv` também respeita o limite de 10 linhas; use `--tudo`
  para exportar tudo.
