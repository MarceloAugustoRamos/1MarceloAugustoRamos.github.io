# Roteiro de entrega - Sprint 1

Preencha os dados da equipe na identificação solicitada pelo professor:

- Integrantes: ______________________________________________
- Turma: ___________________
- Data: ____________________

## Antes de apresentar

1. Extraia e execute o projeto; confira http://localhost:8501.
2. Insira sua chave do Google AI Studio e execute a auditoria com Gemini.
3. Confira se a resposta aparece na aba Relatório e se o checklist registra a resposta recebida.
4. Baixe o relatório completo e o CSV. O relatório local incluído no ZIP não contém resposta real do Gemini.
5. Faça as capturas solicitadas pela instituição. Mantenha a chave fora da captura.

## Demonstração sugerida (3 a 5 minutos)

**1. Fonte real.** Mostre o TXT carregado do arquivo, incluindo a função de cálculo.
Explique que o original não foi corrigido, pois é o objeto de estudo da auditoria.

**2. PCE.** Para cada parâmetro, mostre os valores não negativos válidos, os negativos
inválidos e a ambiguidade de NULL. Os demais parâmetros ficam válidos enquanto um varia.

**3. AVL.** DECIMAL(12,2) significa centavos: ε = 0,01. Explique On = 0,00,
Off = -0,01, Interior = 100,00, Exterior = -100,00. O 0,01 é um caso complementar.
Mostre a ampliação para tornar os pontos próximos da fronteira legíveis.

**4. Divergência.** Mostre CT02: p1 = -0,01, p2 = 10,00, p3 = 5,00.
O oráculo espera -1,00, mas a réplica do TXT calcula 4,90. O TXT não valida negativos.
Mostre também o caso de dois negativos, que pode gerar resultado positivo.

**5. IA e evidências.** Mostre a resposta recebida do Gemini, a exportação do relatório
e o CSV. A integração usa o SDK google-genai e envia o fonte completo para análise.

## Perguntas que podem surgir

**Por que usar o fonte em uma atividade de caixa-preta?** O manual exige a leitura.
As classes e limites derivam dos requisitos; a inspeção do fonte é complementar para
identificar diferença entre a especificação e a implementação. Não calculamos caminhos ou McCabe.

**NULL é válido ou inválido?** O manual se contradiz. A hipótese padrão segue seu
exemplo e o TXT: NULL vira zero. A decisão deve ser confirmada com o professor.
O app também permite selecionar rejeição para comparar os resultados.

**Os testes foram executados no Informix?** Não. Os resultados comparativos são de
uma réplica didática em Python, identificada como simulação. Os testes automatizados
validam o app Python; não validam o banco ou o ambiente Logix.

**Por que o modelo pode diferir do manual?** O nome é configurável para usar um modelo
disponível na conta atual. O fluxo de integração continua usando a API Gemini.

## O que entregar

- ZIP com todo o projeto, fonte original, dependências e instruções.
- Relatório exportado depois da chamada real ao Gemini, se o professor pedir evidências.
- CSV dos 24 casos e capturas das abas conforme a orientação da instituição.
- Identificação da equipe no local solicitado pelo professor.

Não inclua chaves, `.venv` ou arquivos temporários na entrega.
