# Validação · TestingStudio Web v2.0

Foram aprovados **45 testes automatizados** em Python 3.12.14, Linux:

- 12 testes das regras e arquivos CAD0001.
- 9 testes da interface Streamlit integrada.
- 14 testes do motor dos três módulos (grafo, McCabe, épsilon, Def-Uso, mutação e recusa de fonte não suportado).
- 6 testes do adaptador Gemini com dublês.
- 4 testes do instalador.

Comando: `python -m unittest discover -s tests -v`.

O motor também foi executado no runtime real **Pyodide 0.27.7**, usando Node para carregar
Python/WASM. Os exemplos repetiram os resultados nativos:

| Unidade | Casos | Divergências do oráculo | V(G) | Mutantes |
| --- | --- | --- | --- | --- |
| CAD0001 original | 24 | 8 | 4 | 9 |
| Exemplo corrigido | 24 | 0 | 7 | 17 |

O teste WASM confirmou também a recusa de uma unidade com chamada/import não permitidos.
Os arquivos JavaScript foram verificados por `node --check`. Os arquivos Python expostos na
página são cópias geradas do mesmo motor usado pelo Streamlit.

Não houve chamada autenticada ao Gemini nesta validação; os testes de integração usam dublês.
Não foi executado Informix-4GL ou Logix. As métricas se referem à função traduzida/interpretada
no subconjunto documentado. Validação de dependências prontas para Windows/Python 3.14 foi
feita na correção anterior; esta versão acrescenta lógica Python da biblioteca padrão.

Mutation Score é diferencial: 100% não prova conformidade do fonte. O original continua
apresentando as 8 divergências funcionais registradas no relatório.
