# Roteiro de apresentação · TestingStudio Web v2.0

1. Abra a página do laboratório e destaque que o motor é Python, executado no navegador.
2. Explique que os exemplos iniciais são pré-calculados e clique em Analisar em Python.
3. Mostre PCE e AVL. O épsilon é calculado como 10^(-casas decimais), não fixado no gráfico.
4. No CAD0001 original, mostre CT02: esperado -1,00; saída do interpretador 4,90.
5. Abra Caixa-branca: confira N=10, E=12, P=1 e V(G)=4 para o original traduzido.
6. Mostre Def-Uso: definição inicial, normalização de NULL, usos e redefinições.
7. Mostre um mutante, os casos que o mataram e a fórmula do MS. Explique por que um
   score alto pode coexistir com defeito funcional na própria referência.
8. Carregue o exemplo corrigido e reanalise: 24 casos conformes e V(G)=7 com curto-circuito.
9. Adicione um caso pelo editor e exporte Markdown, CSV, SVG ou JSON.
10. Para demonstrar NLP/Gemini, abra o app Streamlit hospedado, forneça a chave por sessão
    e envie requisitos em linguagem natural. O site público não contém chave embutida.
11. Finalize com a rastreabilidade do kickoff, os protocolos do laboratório e o código no GitHub.

Revise as limitações do interpretador e as hipóteses do oráculo. Não apresente simulação como
execução em Informix, nem caminhos estruturais como prova de viabilidade ou sobrevivência
como prova de equivalência.
