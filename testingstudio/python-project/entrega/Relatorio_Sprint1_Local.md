# TestingStudio Web - Relatório da Sprint 1

Disciplina: Teste de Software I (62371) | Professor: Frank Piffer | 2026.2

## 1. Escopo e rastreabilidade

Objeto de estudo: `cad0001_item_calculo.txt`, função `cad0001_calcula_valor`.
Fonte lido do arquivo real, preservado sem correções. SHA-256: `ce12d94b9666f87e23fadd5218705e4c0146616f5eb831e6bf832bb3cd42f070`.
Técnicas: Particionamento em Classes de Equivalência (PCE) e Análise do Valor Limite (AVL).
O oráculo usa a regra do manual: entradas negativas devem retornar -1; demais entradas calculam `(p1 * p2) + p3`.
Os casos de caixa-preta derivam dessa regra, não dos caminhos internos do programa.
A comparação com o TXT é uma inspeção estática complementar e uma simulação didática em Python.

## 2. Ambiguidades e defeitos identificados

**D01 - Ausência de validação de negativos no TXT original.** O exemplo do PDF rejeita
qualquer parâmetro negativo, mas a função do TXT apenas normaliza NULL e aplica a fórmula.
Exemplo: (-0,01; 10,00; 5,00) deveria retornar -1,00; a réplica do TXT retorna 4,90.
Dois negativos podem produzir um resultado positivo: (-2,00; -3,00; 4,00) resulta em 10,00
na réplica, apesar de a regra exigir -1,00.

**A01 - NULL tem requisito contraditório.** A fundamentação do PDF o chama de inválido,
mas tanto seu exemplo de função quanto o TXT convertem NULL para zero.
Hipótese selecionada para este relatório: **Normalizar NULL para zero**.
A decisão precisa ser confirmada com o professor. NULL é uma classe especial, não um ponto AVL.

Essas conclusões estáticas se referem ao TXT original fornecido. Se o arquivo foi alterado,
refaça a inspeção; a aplicação desativa sua réplica para não atribuir resultados ao novo fonte.

## 3. Particionamento em Classes de Equivalência

| ID | Parâmetro | Classe | Domínio | Representante | Esperado |
| --- | --- | --- | --- | --- | --- |
| P1-V | val_param1 | Válida | Numérico ≥ 0,00 (dentro de DECIMAL(12,2)) | 100,00 | Calcular (p1 × p2) + p3 |
| P1-I | val_param1 | Inválida | Numérico < 0,00 | -100,00 | Erro: -1 |
| P1-N | val_param1 | NULL: requisito ambíguo | Ausência de valor; não é uma fronteira numérica | NULL | Normalizar para 0,00 e calcular |
| P2-V | val_param2 | Válida | Numérico ≥ 0,00 (dentro de DECIMAL(12,2)) | 100,00 | Calcular (p1 × p2) + p3 |
| P2-I | val_param2 | Inválida | Numérico < 0,00 | -100,00 | Erro: -1 |
| P2-N | val_param2 | NULL: requisito ambíguo | Ausência de valor; não é uma fronteira numérica | NULL | Normalizar para 0,00 e calcular |
| P3-V | val_param3 | Válida | Numérico ≥ 0,00 (dentro de DECIMAL(12,2)) | 100,00 | Calcular (p1 × p2) + p3 |
| P3-I | val_param3 | Inválida | Numérico < 0,00 | -100,00 | Erro: -1 |
| P3-N | val_param3 | NULL: requisito ambíguo | Ausência de valor; não é uma fronteira numérica | NULL | Normalizar para 0,00 e calcular |

Os parâmetros variam isoladamente, mantendo os demais em classes válidas, para evitar
que uma entrada inválida mascare outra. As classes são limitadas ao domínio de DECIMAL(12,2).
Texto arbitrário não pertence ao tipo de entrada da função e não é tratado como valor monetário.

## 4. AVL e justificativa de épsilon

DECIMAL(12,2) representa duas casas decimais; portanto, ε = 10^(-2) = **0,01**.
A fronteira inferior válida é 0,00. O primeiro valor inválido é 0,00 - ε = -0,01.
Incluímos 0,01 como vizinho válido complementar, além dos quatro pontos pedidos no manual.

| Ponto | Valor decimal | Condição | Esperado |
| --- | --- | --- | --- |
| Exterior | -100,00 | Região inválida | Erro: -1 |
| Off-Point | -0,01 | 0,00 − ε | Erro: -1 |
| On-Point | 0,00 | Fronteira válida | Sucesso: calcular |
| Vizinho válido | 0,01 | 0,00 + ε (complementar) | Sucesso: calcular |
| Interior | 100,00 | Região válida | Sucesso: calcular |

O gráfico completo cobre -100,00 a 100,00. Um segundo gráfico amplia -0,01 a 0,01,
pois o centavo ficaria visualmente comprimido na escala completa.

## 5. Casos de teste e comparação

Total: 24 casos. Divergências numéricas da réplica contra o oráculo: 8.
Simulação do TXT original disponível: sim.
**Não houve execução de Informix-4GL nem acesso à base Logix.**
"Simulado" designa apenas a réplica da função original em Python; não é resultado observado no sistema alvo.

| ID | Técnica | Alvo | Ponto | p1 | p2 | p3 | Esperado (oráculo) | Simulado (TXT original) | Comparação |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CT01 | AVL / PCE | val_param1 | On-Point | 0,00 | 10,00 | 5,00 | 5,00 | 5,00 | Conforme |
| CT02 | AVL / PCE | val_param1 | Off-Point | -0,01 | 10,00 | 5,00 | -1,00 | 4,90 | Divergente |
| CT03 | AVL / PCE | val_param1 | Interior | 100,00 | 10,00 | 5,00 | 1005,00 | 1005,00 | Conforme |
| CT04 | AVL / PCE | val_param1 | Exterior | -100,00 | 10,00 | 5,00 | -1,00 | -995,00 | Divergente |
| CT05 | AVL / PCE | val_param1 | Vizinho válido | 0,01 | 10,00 | 5,00 | 5,10 | 5,10 | Conforme |
| CT06 | AVL / PCE | val_param2 | On-Point | 1,00 | 0,00 | 5,00 | 5,00 | 5,00 | Conforme |
| CT07 | AVL / PCE | val_param2 | Off-Point | 1,00 | -0,01 | 5,00 | -1,00 | 4,99 | Divergente |
| CT08 | AVL / PCE | val_param2 | Interior | 1,00 | 100,00 | 5,00 | 105,00 | 105,00 | Conforme |
| CT09 | AVL / PCE | val_param2 | Exterior | 1,00 | -100,00 | 5,00 | -1,00 | -95,00 | Divergente |
| CT10 | AVL / PCE | val_param2 | Vizinho válido | 1,00 | 0,01 | 5,00 | 5,01 | 5,01 | Conforme |
| CT11 | AVL / PCE | val_param3 | On-Point | 1,00 | 10,00 | 0,00 | 10,00 | 10,00 | Conforme |
| CT12 | AVL / PCE | val_param3 | Off-Point | 1,00 | 10,00 | -0,01 | -1,00 | 9,99 | Divergente |
| CT13 | AVL / PCE | val_param3 | Interior | 1,00 | 10,00 | 100,00 | 110,00 | 110,00 | Conforme |
| CT14 | AVL / PCE | val_param3 | Exterior | 1,00 | 10,00 | -100,00 | -1,00 | -90,00 | Divergente |
| CT15 | AVL / PCE | val_param3 | Vizinho válido | 1,00 | 10,00 | 0,01 | 10,01 | 10,01 | Conforme |
| CT16 | PCE | val_param1 | NULL isolado | NULL | 10,00 | 5,00 | 5,00 | 5,00 | Conforme |
| CT17 | PCE | val_param2 | NULL isolado | 1,00 | NULL | 5,00 | 5,00 | 5,00 | Conforme |
| CT18 | PCE | val_param3 | NULL isolado | 1,00 | 10,00 | NULL | 10,00 | 10,00 | Conforme |
| CT19 | PCE / combinação | Conjunto | Fórmula | 2,00 | 3,00 | 4,00 | 10,00 | 10,00 | Conforme |
| CT20 | PCE / combinação | Conjunto | Todos zero | 0,00 | 0,00 | 0,00 | 0,00 | 0,00 | Conforme |
| CT21 | PCE / combinação | Conjunto | Todos NULL | NULL | NULL | NULL | 0,00 | 0,00 | Conforme |
| CT22 | PCE / combinação | Conjunto | Dois negativos | -2,00 | -3,00 | 4,00 | -1,00 | 10,00 | Divergente |
| CT23 | PCE / combinação | Conjunto | Negativo com multiplicador zero | -2,00 | 0,00 | 4,00 | -1,00 | 4,00 | Divergente |
| CT24 | PCE / combinação | Conjunto | Decimais exatos | 1,25 | 2,00 | 0,50 | 3,00 | 3,00 | Conforme |

## 6. Limites e próximos passos

A réplica usa Decimal e ROUND_HALF_UP para duas casas. Os casos fixos evitam resultados
com frações de centavo; a regra de arredondamento do ambiente Informix deve ser confirmada
para entradas adicionais. DECIMAL(12,2) permite até 9.999.999.999,99 em módulo, porém
limite superior, overflow de produto, transações e banco de dados não são cobertos nesta Sprint.
O sentinela -1 pode coincidir com o cálculo de uma entrada inválida; comparação apenas
numérica não prova que a validação foi executada.
Caixa-branca, grafo de fluxo e McCabe ficam para a próxima Sprint, conforme o manual.

## 7. Integração com Gemini

Este relatório contém a análise local. Nenhuma resposta real do Gemini está incluída.
Para completar a demonstração da integração, insira sua chave e execute a auditoria com Gemini.
