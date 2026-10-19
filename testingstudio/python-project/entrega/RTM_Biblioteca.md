# TestingStudio · Requisitos e RTM · Biblioteca universitária

Fonte: Aula_Teste_I_14102026.pdf · páginas 3–6
Cenário SHA-256: e783a89d8ddeb3502741380ebcc0a93ddc68ded175da3d956e5bbe46c1b1b34f

## Cobertura de planejamento

100.0% dos requisitos possuem CT vinculado. 0/5 CTs executados (registros manuais).

Cobertura RTM mede requisitos com pelo menos um CT vinculado. Não comprova completude dos cenários, execução nem correção do produto. A derivação usa os fluxos estruturados informados; não interpreta automaticamente texto livre.

## Matriz bidirecional

| Requisito | Descrição | Caso de uso | CTs |
| --- | --- | --- | --- |
| REQ01 | Cadastro de novos livros informando ISBN, Título e Autor. | UC01 | CT01 |
| REQ02 | Validação de pendências financeiras do usuário antes de realizar o empréstimo. | UC02 | CT02, CT05 |
| REQ03 | Cálculo automático da multa de R$ 2,00 por dia de atraso na devolução. | UC03 | CT03 |
| REQ04 | Busca de livros por título ou categoria. | UC01 | CT01, CT04 |
| REQ05 | Emissão de comprovante digital de reserva por e-mail. | UC01 | CT01 |

Requisitos sem CT: Nenhum
CTs sem requisito: Nenhum

## Premissas e pontos de refinamento

- CT01, CT02 e CT03 seguem o rastreio do slide 5; CT04 e CT05 são extensões propostas para os fluxos alternativo e principal.
- O PDF não define formato/validação de ISBN, duplicidade, categoria no cadastro, prazo de devolução, arredondamento de dias, indisponibilidade de livros ou falha do serviço de e-mail. Esses pontos exigem refinamento.
- Na multa, os dados usam dias inteiros de atraso já determinados: 0, 1 e 2. Não se presume como datas e atrasos parciais são convertidos em dias.
- O comprovante por e-mail é resultado esperado de uma integração a testar. Este laboratório não envia mensagens nem implementa um sistema de biblioteca.

## CT01 · Cadastro, busca por título e comprovante
Rastreio: UC01 / FP01 (Principal) → REQ01, REQ04, REQ05

Ator: Bibliotecário e usuário

Pré-condições:
- Acesso ao cadastro e ao catálogo disponível.
- Usuário com e-mail de teste e livro disponível para reserva.

Passos:
1. Cadastrar livro com ISBN, título e autor de teste.
2. Buscar o título cadastrado.
3. Selecionar o livro e confirmar sua reserva.
4. Conferir o comprovante na caixa de e-mail de teste.

Dados: [{"ISBN": "9788535902778", "título": "Dom Casmurro", "autor": "Machado de Assis", "e-mail": "leitor@example.com"}]

Esperado: Livro cadastrado com os dados informados, encontrado pelo título e reservado; comprovante digital da reserva recebido no e-mail do usuário.

Situação: Não executado
Evidência: Não informada.

## CT02 · Bloquear usuário com dívida
Rastreio: UC02 / FE01 (Exceção) → REQ02

Ator: Usuário e atendente

Pré-condições:
- Usuário identificado e livro disponível para empréstimo.

Passos:
1. Preparar usuário com pendência financeira.
2. Solicitar o empréstimo do livro.
3. Conferir a negativa e a ausência de registro do empréstimo.

Dados: [{"pendência financeira": "R$ 10,00"}]

Esperado: O sistema valida a pendência antes da operação e bloqueia o empréstimo; nenhum empréstimo é registrado.

Situação: Não executado
Evidência: Não informada.

## CT03 · Fronteira entre devolução no prazo e com atraso
Rastreio: UC03 / FA02 (Alternativo) → REQ03

Ator: Usuário e atendente

Pré-condições:
- Empréstimo existente; dias inteiros de atraso conhecidos.

Passos:
1. Preparar uma devolução para cada quantidade de dias de atraso da tabela.
2. Registrar a devolução e consultar a multa calculada automaticamente.
3. Comparar cada valor com o resultado esperado de R$ 2,00 por dia.

Dados: [{"dias de atraso": 0, "multa esperada": "R$ 0,00"}, {"dias de atraso": 1, "multa esperada": "R$ 2,00"}, {"dias de atraso": 2, "multa esperada": "R$ 4,00"}]

Esperado: No prazo: R$ 0,00; 1 dia de atraso: R$ 2,00; 2 dias: R$ 4,00. Não há cobrança positiva quando os dias de atraso são zero.

Situação: Não executado
Evidência: Não informada.

## CT04 · Localizar livro por categoria
Rastreio: UC01 / FA01 (Alternativo) → REQ04

Ator: Bibliotecário e usuário

Pré-condições:
- Acesso ao cadastro e ao catálogo disponível.
- Usuário com e-mail de teste e livro disponível para reserva.

Passos:
1. Preparar catálogo com um livro associado a Literatura e outro a Computação.
2. Buscar pela categoria Literatura.

Dados: [{"categoria": "Literatura"}]

Esperado: A busca por categoria retorna o livro de Literatura e não inclui o de Computação.

Situação: Não executado
Evidência: Não informada.
Nota: Extensão proposta; a preparação das categorias depende de regra ainda não detalhada no PDF.

## CT05 · Validar usuário sem pendências
Rastreio: UC02 / FP02 (Principal) → REQ02

Ator: Usuário e atendente

Pré-condições:
- Usuário identificado e livro disponível para empréstimo.

Passos:
1. Preparar usuário sem pendências financeiras e com os demais critérios de empréstimo atendidos.
2. Solicitar o empréstimo.
3. Conferir a validação financeira anterior ao registro.

Dados: [{"pendência financeira": "R$ 0,00"}]

Esperado: A validação financeira é realizada e permite prosseguir, respeitadas as demais regras do empréstimo.

Situação: Não executado
Evidência: Não informada.
Nota: Extensão proposta para complementar o bloqueio de CT02.
