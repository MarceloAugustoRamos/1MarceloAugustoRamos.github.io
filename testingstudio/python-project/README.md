# TestingStudio Web · v3.0

Laboratório de Teste de Software I (Ementa 62371), Prof. Frank Piffer, 2026.2.
Tema automático, motor Python, os três módulos do kickoff e a nova Sprint de requisitos e RTM.

## Aparência do dispositivo

O modo **Sistema** acompanha a preferência de tema claro/escuro do dispositivo. No
GitHub Pages, o seletor **Tema** no topo oferece Sistema, Claro e Escuro e salva somente
essa preferência no navegador. Alterações do dispositivo são aplicadas automaticamente
enquanto Sistema estiver selecionado.

No Streamlit, abra **⋮ → Theme** e escolha **System**, **Light** ou **Dark**. Os dois
temas são configurados em `.streamlit/config.toml`; o modo automático é o padrão para
visitantes sem uma escolha anterior. A configuração é individual por navegador.
Barra lateral, campos, tabelas e visualizações acompanham o tema ativo.

## Acesso pela web

A pasta `docs/` contém a versão para GitHub Pages. O motor Python roda no navegador
com Pyodide 0.27.7, em um Web Worker. O computador de quem acessa não precisa instalar
Python, Streamlit ou pacotes. Use navegador moderno com JavaScript e WebAssembly,
acesso HTTPS e internet para o primeiro carregamento do runtime.

Os exemplos iniciais são **pré-calculados pelo mesmo motor**, identificados na interface.
Clique em **Analisar em Python** para executar a unidade atual no navegador. O carregamento
inicial depende do CDN do Pyodide. Depois, o runtime é reutilizado na sessão.
O código digitado não é enviado ao GitHub. A análise determinística acontece na aba.

## O que foi implementado

| Módulo | Funcionalidade |
| --- | --- |
| 1 · Caixa-preta | PCE por parâmetro, classes válidas/inválidas/NULL, AVL, fronteira configurável e ε = 10^(-casas decimais) |
| 2 · Caixa-branca | GFC da AST, decomposição de and/or por curto-circuito, E/N/P, V(G)=E-N+2P, conferência por predicados+1 e caminhos estruturais |
| 3 · Def-Uso e mutação | Definições alcançantes, p-use/c-use, cobertura dinâmica, mutação AOR/ROR/LCR/CRP/RVR, mortos/sobreviventes/equivalentes declarados e MS calculado |
| Integração | Python + Streamlit + Gemini, editor de fonte, requisitos em linguagem natural, chave por sessão e revisão dos três módulos |
| Entrega | Relatório Markdown, CSV, SVG, JSON, rastreabilidade do kickoff, protocolos e workflows para repositório dedicado |

O PDF apresenta os módulos 2 e 3 como evolução do produto. Eles já estão disponíveis
nesta versão, dentro do subconjunto de linguagem descrito abaixo. A página final de
agradecimento não cria um requisito de software adicional.

## Nova Sprint · Derivação de CTs e RTM (14/10/2026)

Abra **Requisitos e RTM** no menu da página ou do app Streamlit. O exemplo contém os
cinco requisitos da biblioteca universitária do PDF, três casos de uso, fluxos principal,
alternativo e de exceção, passos, pré-condições, dados e resultados esperados.

O rastreio da aula foi preservado: CT01 → REQ01/REQ04/REQ05; CT02 → REQ02;
CT03 → REQ03. CT04 (categoria) e CT05 (sem pendências) são extensões propostas.
A multa tem exemplos de 0, 1 e 2 dias: R$ 0,00, R$ 2,00 e R$ 4,00. Regras não
especificadas, como dias parciais, validação de ISBN e falha do e-mail, estão sinalizadas
para refinamento; não foram inventadas como exigências da aula.

Edite ou importe o cenário em JSON e clique em **Derivar CTs e RTM em Python**.
O motor deriva um CT de cada fluxo estruturado. Não interpreta texto livre automaticamente.
A matriz mostra requisito → CT e CT → requisito, requisitos sem cobertura e CTs órfãos.
IDs duplicados e vínculos inexistentes são recusados.

**Cobertura planejada de 100% não significa testes executados.** Todos começam como
Não executado. Registre Aprovado, Reprovado ou Bloqueado com evidência/justificativa
após testar o sistema sob teste. Bloqueados não contam como executados. O laboratório
não implementa a biblioteca nem envia e-mails. A edição do cenário reinicia a rodada
para evitar reutilizar resultados de outra especificação.

Exporte relatório Markdown, matriz CSV ou projeto JSON com os registros para continuar
outra sessão. Os dados permanecem na aba/sessão até a exportação; não há banco remoto.
O módulo é Python puro (`traceability.py`), compartilhado entre Streamlit e Pyodide.
Veja `entrega/SPRINT_RTM.md` e `entrega/cenario_biblioteca.json`.

## Python e Gemini no servidor

O GitHub Pages não hospeda um servidor Python. Nesta solução ele entrega os arquivos,
e o Python é executado no navegador por WebAssembly. **A API Gemini permanece no app
Streamlit no servidor**, para não colocar uma chave compartilhada no site público.
A página tem uma área para abrir a URL do seu app em `*.streamlit.app` quando ele for hospedado.

Para hospedar a versão Python com Gemini:

1. Abra https://share.streamlit.io/ e conecte seu GitHub.
2. Crie um app a partir do repositório que contém este projeto.
3. Informe a branch `main` e o caminho completo de `app.py` no repositório.
4. Escolha Python 3.12 nas configurações avançadas e publique.
5. Copie a URL emitida pelo Streamlit para a área Assistente Gemini da página.
6. No app Streamlit, insira sua chave na barra lateral, escreva os requisitos e execute a auditoria.

Não há chave neste repositório. A chave do visitante é usada apenas na sessão do servidor.
A versão GitHub Pages não solicita nem armazena chave Gemini. A chamada real exige chave
válida, modelo habilitado e cota disponível; as análises locais funcionam independentemente da API.

## Guardar a chave Gemini no Streamlit

Em share.streamlit.io, abra o menu do app → Settings → Secrets. Configure uma vez:

```toml
GEMINI_API_KEY = "COLE_SUA_CHAVE_AQUI"
```

Substitua o exemplo pela chave real, mantendo as aspas. A entrada deve ficar na raiz do
TOML, antes de qualquer cabeçalho de seção. Preserve outros Secrets existentes. Salve
no painel do Streamlit, nunca no GitHub nem no chat. Se necessário, use Reboot no
painel do app para recarregar a configuração no servidor.

A opção **Chave salva no app** fica disponível sem senha, inclusive para a avaliação
do professor em outro computador. A chave permanece no servidor: não é preenchida em
widget do navegador nem incluída nos relatórios. Qualquer visitante pode usar a
integração e consumir a cota do projeto. O campo antigo `GEMINI_ACCESS_PASSWORD`, caso
continue nos Secrets, não é lido nem exigido. A opção **Informar minha chave** permite
usar uma chave própria somente na sessão.

**Verificar chave e modelo** consulta os metadados do modelo sem gerar uma auditoria.
Esse resultado não garante cota para gerar conteúdo. Abrir a página não faz uma chamada
Gemini automaticamente. Cada ação faz uma tentativa, sem repetições automáticas do SDK.

Se aparecer **HTTP 401**, compare o valor de `GEMINI_API_KEY` com a chave que funciona
na opção manual. Atualize os Secrets, salve e reinicie o app. Se também falhar
manualmente, confira no AI Studio se a chave está ativa. **HTTP 429** indica limite ou
cota: consulte os limites do projeto no AI Studio. Outra chave do mesmo projeto não
renova a cota. O motor Python continua disponível sem Gemini.

Para execução local, configure `.streamlit/secrets.toml` no diretório de execução;
esse arquivo é ignorado pelo Git. Os Secrets do Community Cloud permanecem no painel.

## Fontes e referências

A seção **Fontes e referências** está disponível no GitHub Pages e no Streamlit, com
materiais da disciplina, referências acadêmicas de apoio e documentação técnica. Cada
módulo indica os identificadores das fontes correspondentes. Os relatórios Markdown
de análise e RTM incluem a bibliografia; a lista também pode ser baixada separadamente.
O catálogo central fica em `bibliography.py`. Materiais efetivamente usados nos
exercícios são diferenciados das referências complementares verificadas nesta revisão.
Os PDFs de aula são identificados por nome e páginas, sem redistribuição automática.

## Executar localmente no Windows

1. Tenha Python 3.10+ instalado (testado em Python 3.12; dependências prontas verificadas
   também para Python 3.14/Windows x64 na correção anterior).
2. Extraia o projeto inteiro e abra `iniciar.bat`.
3. Na primeira vez, aguarde o ambiente virtual e as dependências; é necessária internet.
4. Acesse http://localhost:8501 e mantenha o terminal aberto.
5. Para encerrar, pressione Ctrl+C. `instalar.bat` repete ou repara a instalação.

O instalador usa pandas 2.3.3 e somente wheels, evitando compilação no laboratório.
Alternativa: `py -3 launcher.py start`. Em Linux/macOS: `python3 launcher.py start`.
O ponto de entrada recomendado é `app.py`. Para compatibilidade com uma publicação existente, executar `analysis.py` diretamente também abre a interface; importar esse módulo mantém apenas as funções de análise. A interface antiga da Sprint 1 foi preservada em `legacy_sprint1.py`.

Para testar a página web localmente, na raiz do projeto execute:

```bash
python scripts/build_pages.py
python -m http.server 8000 --directory docs
```

Abra http://localhost:8000. Abrir index.html diretamente com file:// não permite carregar o Worker.

## Domínio suportado e método

O motor recebe uma única função numérica com 1 a 6 parâmetros, atribuições simples,
`if/else`, comparações, operações aritméticas e `return`. Não executa imports, chamadas,
acesso a atributos, loops, arquivos, shell ou rede. **Não usa eval/exec no fonte do usuário**.
É um interpretador restrito para estudo, não um executor Python ou Informix de uso geral.

O adaptador Informix reconhece somente `cad0001_calcula_valor`, normalização de NULL,
IF/ELSE, LET e RETURN do exercício. Exibe a tradução Python. Linhas, GFC e Def-Uso referem-se
à tradução analisada; o banco Logix e operações CRUD não são executados.

Precisão: de 0 a 6 casas. No Informix, o padrão vem de DECIMAL(p,s); em Python, o padrão
é 2. A fronteira inferior vem da configuração de requisito. Não é inferida de texto livre.
A interpretação de linguagem natural é feita pelo Gemini no app Streamlit.

O oráculo CAD0001 aplica-se a 3 parâmetros, escala 2 e limite 0: negativos retornam -1;
a fórmula é (p1*p2)+p3. NULL segue a hipótese declarada. Para outra regra, use comparação
diferencial e forneça seus casos; não haverá declaração de conformidade sem oráculo externo.
Os cálculos usam Decimal e arredondamento ROUND_HALF_UP na saída da simulação.

O TXT original foi preservado. Ele não rejeita negativos, ao contrário do exemplo do manual.
O manual também contradiz o tratamento de NULL. Essas divergências não foram escondidas.

### McCabe

Grafo conectado e saída única: V(G)=E-N+2P, P=1. Predicados de curto-circuito são decompostos.
A listagem de caminhos é estrutural, limitada a 128. V(G) não é a contagem de todos os caminhos,
nem uma prova de que cada caminho é viável. Código inatingível após return não entra na métrica.

### Def-Uso

Análise estática por definições alcançantes: uma redefinição mata a definição anterior.
A cobertura é medida com as execuções da suíte no interpretador. Pares potencialmente
inviáveis não são automaticamente removidos do denominador.

### Mutation Score

Uma alteração por mutante: AOR (aritmética), ROR (relacional), LCR (lógica), CRP (constante)
e RVR (retorno). Limite de 60 mutantes. MS = mortos/(gerados-equivalentes declarados)*100.
Casos que já falham com erro de execução na referência não são usados para matar mutantes.
Sem caso de referência executável, o score fica não calculável.

A comparação é diferencial com a referência. Um score alto não prova que a referência
atende ao requisito. Sobreviventes não são automaticamente equivalentes. Equivalência
precisa de revisão humana; o sistema recusa excluir como equivalente um mutante já morto.

## Testes e geração da página

```bash
python -m pip install --only-binary=:all: -r requirements.txt
python -m unittest discover -s tests -v
python scripts/build_pages.py
```

Para testar o motor real no Python/WASM, em ambiente de desenvolvimento com Node:

```bash
npm install
npm test
```

`npm` não é necessário para visitantes nem para usar o app Streamlit. O frontend do Pages
usa arquivos estáticos e carrega Pyodide por CDN. Os testes Gemini usam dublês; não consomem API.

## Publicação num repositório dedicado

Coloque os arquivos desta pasta na raiz do repositório. Configure Settings → Pages →
GitHub Actions para usar `.github/workflows/pages.yml`. O workflow gera docs e publica o site;
`tests.yml` valida o Python. Alternativamente, publique a branch main com a pasta /docs.

Se o projeto estiver numa subpasta de um repositório Pages existente, mantenha a página
estática no caminho escolhido e o projeto Python em uma subpasta própria. Não altere a
página inicial nem os demais projetos para publicar este laboratório.

Edite `deployment.json` para registrar a URL do código e a URL Streamlit, quando disponível;
rode `python scripts/build_pages.py` para atualizar a página.

## Estrutura

- `app.py`, `studio_app.py`: app Streamlit com tema preto e Gemini no servidor.
- `studio_engine.py`: motor restrito de PCE/AVL, GFC, Def-Uso e mutação.
- `analysis.py`: regras e casos CAD0001, Decimal e exportações da Sprint 1.
- `gemini_service.py`: SDK e prompt integrado, sem credencial embutida.
- `traceability.py`, `traceability_ui.py`: derivação de CTs, RTM e registro manual de resultados.
- `project_guide.py`: rastreabilidade do kickoff e protocolos do laboratório.
- `docs/`: página GitHub Pages, worker e cópias geradas do motor.
- `scripts/`: build da página e teste WASM.
- `tests/`: testes de regras, interface, SDK, instalador e motor integrado.
- `.github/workflows/`: testes e publicação para uso na raiz de um repositório dedicado.

Documentação oficial: https://docs.github.com/en/pages ; https://pyodide.org/en/0.27.7/usage/quickstart.html ;
https://docs.streamlit.io/deploy/streamlit-community-cloud ; https://ai.google.dev/gemini-api/docs/api-key
