# TestingStudio Web · Auditoria integrada

Função: calcula_item
Fonte SHA-256: d2ba46a1f4be7d12ed86a6ddd9c1c506584cf67bfe582ff318eb4e8450a1e4d0
Linguagem: Python restrito
Oráculo: CAD0001 / manual; hipótese NULL: zero

## Módulo 1 · Caixa-preta
ε = 10^(-2) = 0.01
Casos: 24; conformes: 24; divergentes: 0; erros: 0

| Caso | Entradas | Esperado | Saída do interpretador | Situação |
| --- | --- | --- | --- | --- |
| CT01 · On-Point | 0,00; 10,00; 5,00 | 5,00 | 5,00 | Conforme |
| CT02 · Off-Point | -0,01; 10,00; 5,00 | -1,00 | -1,00 | Conforme |
| CT03 · Interior | 100,00; 10,00; 5,00 | 1005,00 | 1005,00 | Conforme |
| CT04 · Exterior | -100,00; 10,00; 5,00 | -1,00 | -1,00 | Conforme |
| CT05 · Vizinho válido | 0,01; 10,00; 5,00 | 5,10 | 5,10 | Conforme |
| CT06 · On-Point | 1,00; 0,00; 5,00 | 5,00 | 5,00 | Conforme |
| CT07 · Off-Point | 1,00; -0,01; 5,00 | -1,00 | -1,00 | Conforme |
| CT08 · Interior | 1,00; 100,00; 5,00 | 105,00 | 105,00 | Conforme |
| CT09 · Exterior | 1,00; -100,00; 5,00 | -1,00 | -1,00 | Conforme |
| CT10 · Vizinho válido | 1,00; 0,01; 5,00 | 5,01 | 5,01 | Conforme |
| CT11 · On-Point | 1,00; 10,00; 0,00 | 10,00 | 10,00 | Conforme |
| CT12 · Off-Point | 1,00; 10,00; -0,01 | -1,00 | -1,00 | Conforme |
| CT13 · Interior | 1,00; 10,00; 100,00 | 110,00 | 110,00 | Conforme |
| CT14 · Exterior | 1,00; 10,00; -100,00 | -1,00 | -1,00 | Conforme |
| CT15 · Vizinho válido | 1,00; 10,00; 0,01 | 10,01 | 10,01 | Conforme |
| CT16 · NULL isolado | NULL; 10,00; 5,00 | 5,00 | 5,00 | Conforme |
| CT17 · NULL isolado | 1,00; NULL; 5,00 | 5,00 | 5,00 | Conforme |
| CT18 · NULL isolado | 1,00; 10,00; NULL | 10,00 | 10,00 | Conforme |
| CT19 · Fórmula | 2,00; 3,00; 4,00 | 10,00 | 10,00 | Conforme |
| CT20 · Todos zero | 0,00; 0,00; 0,00 | 0,00 | 0,00 | Conforme |
| CT21 · Todos NULL | NULL; NULL; NULL | 0,00 | 0,00 | Conforme |
| CT22 · Dois negativos | -2,00; -3,00; 4,00 | -1,00 | -1,00 | Conforme |
| CT23 · Negativo com multiplicador zero | -2,00; 0,00; 4,00 | -1,00 | -1,00 | Conforme |
| CT24 · Decimais exatos | 1,25; 2,00; 0,50 | 3,00 | 3,00 | Conforme |

## Módulo 2 · Caixa-branca
V(G) = E − N + 2P = 19 − 14 + 2 × 1 = 7
Grafo conectado, entrada/saída únicas; and/or decompostos por curto-circuito. Caminhos listados são estruturais, sem prova de viabilidade.
Verificação: predicados + 1 = 7
Caminhos estruturais listados: 32; limite de listagem: 128.
V(G) mede caminhos linearmente independentes, não o número de todos os caminhos nem uma prova de viabilidade.

## Módulo 3 · Def-Uso
Pares cobertos: 16/16.

| Variável | Definição | Uso | Tipo | Coberto |
| --- | --- | --- | --- | --- |
| resultado | N2 | N1 | c-use | Sim |
| p1 | N11 | N2 | c-use | Sim |
| p1 | N13 | N2 | c-use | Sim |
| p2 | N13 | N2 | c-use | Sim |
| p2 | N9 | N2 | c-use | Sim |
| p3 | N13 | N2 | c-use | Sim |
| p3 | N7 | N2 | c-use | Sim |
| p3 | N13 | N4 | p-use | Sim |
| p3 | N7 | N4 | p-use | Sim |
| p2 | N13 | N5 | p-use | Sim |
| p2 | N9 | N5 | p-use | Sim |
| p1 | N11 | N6 | p-use | Sim |
| p1 | N13 | N6 | p-use | Sim |
| p3 | N13 | N8 | p-use | Sim |
| p2 | N13 | N10 | p-use | Sim |
| p1 | N13 | N12 | p-use | Sim |

## Teste de mutação
MS = mortos / (gerados − equivalentes declarados) × 100 = 17/(17−0) × 100
MS: 100.0%.
Comparação diferencial com a execução da unidade de referência no interpretador restrito. Sobreviventes não são automaticamente equivalentes; o score não prova correção da referência.
Casos excluídos por erro na referência: 0

| Mutante | Operador | Linha | Situação | Casos que o mataram |
| --- | --- | --- | --- | --- |
| M01 | RVR | 11 | Morto | CT01, CT03, CT05, CT06, CT08, CT10, CT11, CT13, CT15, CT16, CT17, CT18, CT19, CT24 |
| M02 | ROR | 2 | Morto | CT02, CT03, CT04, CT05, CT08, CT10, CT11, CT13, CT15, CT16, CT18, CT19, CT21, CT23, CT24 |
| M03 | ROR | 4 | Morto | CT03, CT05, CT07, CT08, CT09, CT10, CT11, CT13, CT15, CT17, CT18, CT19, CT21, CT24 |
| M04 | ROR | 6 | Morto | CT01, CT03, CT05, CT06, CT08, CT10, CT12, CT13, CT14, CT15, CT16, CT17, CT18, CT19, CT21, CT24 |
| M05 | LCR | 8 | Morto | CT02, CT04, CT07, CT09, CT12, CT14, CT22, CT23 |
| M06 | RVR | 9 | Morto | CT02, CT04, CT07, CT09, CT12, CT14, CT22, CT23 |
| M07 | AOR | 10 | Morto | CT01, CT03, CT05, CT06, CT08, CT10, CT13, CT15, CT16, CT17, CT19, CT24 |
| M08 | CRP | 3 | Morto | CT16 |
| M09 | CRP | 5 | Morto | CT17 |
| M10 | CRP | 7 | Morto | CT18, CT21 |
| M11 | ROR | 8 | Morto | CT01, CT16, CT20, CT21 |
| M12 | ROR | 8 | Morto | CT06, CT17, CT20, CT21 |
| M13 | ROR | 8 | Morto | CT11, CT18, CT20, CT21 |
| M14 | AOR | 10 | Morto | CT01, CT03, CT05, CT06, CT08, CT10, CT11, CT13, CT15, CT16, CT17, CT18, CT19, CT24 |
| M15 | CRP | 8 | Morto | CT01, CT16, CT20, CT21 |
| M16 | CRP | 8 | Morto | CT06, CT17, CT20, CT21 |
| M17 | CRP | 8 | Morto | CT11, CT18, CT20, CT21 |

## Limites e revisão
- A execução é feita por um interpretador numérico restrito; não executa Informix/Logix, imports, chamadas ou loops.
- O domínio numérico e o limite inferior são requisitos configurados, não inferidos automaticamente de linguagem natural.
- A identificação de equivalência de mutantes exige revisão humana; sobrevivência não prova equivalência.
- Def-Uso: análise estática por definições alcançantes; cobertura dinâmica restrita à suíte selecionada. Pares potencialmente inviáveis permanecem no denominador.
