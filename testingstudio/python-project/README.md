# TestingStudio Web · v2.0

Laboratório de Teste de Software I (Ementa 62371), Prof. Frank Piffer, 2026.2.
Tema preto, motor Python e os três módulos do kickoff.

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

## Executar localmente no Windows

1. Tenha Python 3.10+ instalado (testado em Python 3.12; dependências prontas verificadas
   também para Python 3.14/Windows x64 na correção anterior).
2. Extraia o projeto inteiro e abra `iniciar.bat`.
3. Na primeira vez, aguarde o ambiente virtual e as dependências; é necessária internet.
4. Acesse http://localhost:8501 e mantenha o terminal aberto.
5. Para encerrar, pressione Ctrl+C. `instalar.bat` repete ou repara a instalação.

O instalador usa pandas 2.3.3 e somente wheels, evitando compilação no laboratório.
Alternativa: `py -3 launcher.py start`. Em Linux/macOS: `python3 launcher.py start`.
O ponto de entrada é `app.py`. A interface antiga da Sprint 1 foi preservada em `legacy_sprint1.py`.

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
- `project_guide.py`: rastreabilidade do kickoff e protocolos do laboratório.
- `docs/`: página GitHub Pages, worker e cópias geradas do motor.
- `scripts/`: build da página e teste WASM.
- `tests/`: testes de regras, interface, SDK, instalador e motor integrado.
- `.github/workflows/`: testes e publicação para uso na raiz de um repositório dedicado.

Documentação oficial: https://docs.github.com/en/pages ; https://pyodide.org/en/0.27.7/usage/quickstart.html ;
https://docs.streamlit.io/deploy/streamlit-community-cloud ; https://ai.google.dev/gemini-api/docs/api-key
