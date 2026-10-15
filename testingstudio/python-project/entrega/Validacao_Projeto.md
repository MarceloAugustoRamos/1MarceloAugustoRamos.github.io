# Validação do projeto Python

Data: 05/10/2026. Ambiente: Linux, Python 3.12.14.

## Testes automatizados

Comando: `python -m unittest discover -s tests -v`.

Resultado da versão corrigida: **29 testes passaram**, sem falhas.

| Grupo | Quantidade | O que foi verificado |
| --- | --- | --- |
| Oráculo, casos e arquivos | 12 | Fonte original e SHA-256, cálculo Decimal, negativos, zero, centavo, NULL, cobertura, entradas inválidas, exportação e bloqueio da réplica para fonte modificado |
| Interface Streamlit | 7 | Renderização inicial, fonte visível, abas, ausência de chave, persistência da resposta, limpeza, mudança da hipótese de NULL, falha da API, arquivo ausente e validação da calculadora |
| Adaptador Gemini | 6 | Prompt com fonte completo, parâmetros do SDK, tratamento do texto, falta de chave, resposta vazia, truncamento e sanitização de erros |
| Instalador Python | 4 | Instalação apenas de wheels, nova tentativa após falha, reutilização de instalação concluída e atualização quando as dependências mudam |

Os 24 casos planejados são dados da auditoria, distintos dos 29 testes automatizados do app.
Na hipótese NULL → zero, a réplica apresenta **8 divergências numéricas** em relação ao oráculo.
Na hipótese de rejeição de NULL, apresenta **12 divergências**.

## Execução do servidor

Foi iniciado um servidor Streamlit real em endereço local temporário.
O endpoint de saúde retornou HTTP 200 com `ok`, e a página inicial retornou HTTP 200.

## Correção da instalação no Python 3.14

A versão anterior fixava pandas 2.2.3. No Python 3.14, essa versão levou o pip
a tentar compilar o pacote, e a máquina de apresentação recusou o subprocesso Meson.
O pacote atualizado usa **pandas 2.3.3**, e o instalador exige distribuições prontas
com `--only-binary=:all:`. Também atualiza o pip e reconhece mudanças em requirements.txt.

Verificação de resolução de dependências, sem execução nativa do Windows:

`python -m pip install --dry-run --ignore-installed --only-binary=:all: --platform win_amd64 --python-version 3.14 --implementation cp --abi cp314 -r requirements.txt`

Resultado: **55 pacotes resolvidos, todos em formato wheel**, incluindo pandas 2.3.3,
NumPy 2.5.3 e PyArrow 25.0.1. Os testes do app foram repetidos com pandas 2.3.3 instalado.

Referência oficial: https://pandas.pydata.org/pandas-docs/version/2.3/whatsnew/v2.3.3.html

## Limites da validação

- Os testes de Gemini usaram dublês; não houve chamada autenticada à API nesta validação.
  A equipe deve usar sua chave para demonstrar a integração real.
- A interface foi exercitada pelo AppTest do Streamlit. Não foram obtidas capturas de
  um navegador real neste ambiente; faça as capturas na máquina de apresentação.
- Os iniciadores Windows foram preparados, mas não executados em uma máquina Windows
  durante esta validação. O aplicativo foi testado no ambiente Python descrito acima.
- Não foi executado Informix-4GL nem banco Logix. As comparações do CAD0001 são simulações
  identificadas, não resultados observados no sistema alvo.

## Integridade da entrega

O TXT original foi preservado byte a byte.
SHA-256: `ce12d94b9666f87e23fadd5218705e4c0146616f5eb831e6bf832bb3cd42f070`.

O pacote não contém chave de API, ambiente virtual ou arquivos de cache.
