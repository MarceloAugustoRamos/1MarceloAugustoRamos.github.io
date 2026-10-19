# Sprint · Derivação de casos de teste e RTM

Referência: Aula_Teste_I_14102026.pdf, Professor Frank Piffer.

| Páginas | Conteúdo da aula | Entrega implementada |
| --- | --- | --- |
| 1–2 | Transição do código isolado para engenharia de requisitos | Novo módulo Requisitos e RTM, separado das métricas de código |
| 3 | Caso de uso: intenção, fluxo principal, alternativo e exceção | Atores, pré-condições e fluxos tipados no cenário estruturado |
| 4 | REQ01–REQ05 da biblioteca universitária | Backlog com os cinco enunciados preservados |
| 5 | CT01 feliz, CT02 bloqueio, CT03 limite/multa | Rastreio preservado; passos, dados e saídas esperadas detalhados |
| 6 | Cobertura bidirecional requisito ↔ caso de teste | Matriz cruzada e reversa, percentuais, lacunas e CTs sem requisito |
| 7 | Aplicar derivação em cenário livre no TestingStudio | Editor/importador JSON, derivação Python e exportação reutilizável |
| 8 | Encerramento | Não estabelece outra funcionalidade |

## Como demonstrar

1. Abra Requisitos e RTM no site publicado.
2. Confira os cinco requisitos e os três tipos de fluxo.
3. Clique em Derivar CTs e RTM em Python. O selo muda para Python executado.
4. Em Casos derivados, abra CT01, CT02 e CT03. Confira rastreio e valores da multa.
5. Abra Matriz RTM e confira a cobertura nos dois sentidos.
6. Para demonstrar uma lacuna, edite o JSON e acrescente um requisito REQ06 sem fluxo.
   Recalcule: a cobertura cai a 83,3%, e REQ06 aparece sem CT.
7. Registre resultados apenas após executar um caso no sistema sob teste, com evidência.
8. Exporte Markdown, CSV e projeto JSON; o último permite restaurar cenário e registros.

## Escopo e revisão

O PDF apresenta um exercício de derivação, não uma especificação completa de biblioteca.
CT04 (busca por categoria) e CT05 (usuário sem pendências) complementam os três CTs
exemplificados e estão marcados como propostas. As premissas e lacunas de negócio
permanecem visíveis. Nenhuma execução de biblioteca ou envio de e-mail é simulado como real.
A geração é determinística, a partir de fluxos estruturados, e funciona sem Gemini.

Cobertura RTM mede vínculos de planejamento. Todos os casos começam Não executado.
A aprovação de um requisito exige que todos os CTs vinculados sejam marcados Aprovado,
com evidência manual; isso não é garantia de completude ou correção do software.
Mudanças no cenário iniciam nova rodada para evitar resultados desatualizados.

## Arquivos

- traceability.py: validação, derivação, matriz, métricas e exportações, somente stdlib.
- traceability_ui.py: interface Streamlit.
- docs/assets/traceability.js: interface web; cálculo no mesmo Python via Worker.
- tests/test_traceability.py: rastreio da aula, lacunas, execução, importação e validação.
- cenario_biblioteca.json: exemplo editável.
- RTM_Biblioteca.md: relatório de planejamento, sem execuções inventadas.
