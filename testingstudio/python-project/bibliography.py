"""Fontes do laboratório, compartilhadas entre a interface e as exportações."""

REVIEW_DATE = "19 out. 2026"
GROUPS = ["Materiais da disciplina", "Referências de apoio", "Documentação técnica"]
SOURCE_NOTE = (
    "Os materiais da disciplina são a base direta dos exercícios. As referências de apoio "
    "complementam os conceitos e foram verificadas nesta revisão bibliográfica; sua inclusão "
    "não significa consulta integral de todas as obras. As decisões do interpretador e as "
    "extensões CT04/CT05 são adaptações do projeto, identificadas como tais."
)

SOURCES = [
    {"id": "M01", "group": GROUPS[0], "title": "Manual de laboratório — Sprint 1",
     "citation": "PIFFER, Frank. TestingStudio Web: auditoria de caixa-preta (PCE & AVL) — CAD0001. Manual de laboratório, Sprint 1. Teste de Software I, Ementa 62371, 2026.2. 2 p.",
     "scope": "Páginas 1–2: regras do CAD0001, PCE, AVL com épsilon e requisitos da primeira entrega. A divergência sobre NULL é mantida como hipótese explícita.",
     "location": "manual-testingstudio-sprint1.pdf · Material fornecido na disciplina.", "url": ""},
    {"id": "M02", "group": GROUPS[0], "title": "TestingStudio Web — Kickoff",
     "citation": "PIFFER, Frank. TestingStudio Web — Kickoff. Apresentação da disciplina Teste de Software I, 2026. 11 p.",
     "scope": "Páginas 4–8: backlog de caixa-preta, caixa-branca, Def-Uso, mutação e integração Python/Streamlit/Gemini.",
     "location": "TestingStudio_Web_Kickoff.pdf · Material fornecido na disciplina.", "url": ""},
    {"id": "M03", "group": GROUPS[0], "title": "Aula Teste I — 14/10/2026",
     "citation": "PIFFER, Frank. Aula Teste I — 14/10/2026. Material de aula sobre requisitos, casos de uso, derivação de casos de teste e rastreabilidade, 2026. 8 p.",
     "scope": "Páginas 3–7: fluxos principal, alternativo e de exceção; REQ01–REQ05 da biblioteca; CT01–CT03 e RTM bidirecional. CT04 e CT05 são extensões propostas pelo projeto.",
     "location": "Aula_Teste_I_14102026.pdf · Material fornecido na disciplina.", "url": ""},
    {"id": "M04", "group": GROUPS[0], "title": "Código original CAD0001",
     "citation": "CAD0001. cad0001_item_calculo.txt. Código-fonte Informix-4GL fornecido para o exercício da disciplina, 2026. Autoria individual não informada no arquivo.",
     "scope": "Unidade de estudo preservada. O projeto simula sua função de cálculo com um adaptador restrito; não executa o banco Informix/Logix.",
     "location": "Fonte original no repositório do projeto.",
     "url": "https://github.com/MarceloAugustoRamos/1MarceloAugustoRamos.github.io/blob/main/testingstudio/python-project/cad0001_item_calculo.txt"},
    {"id": "B01", "group": GROUPS[1], "title": "Introdução ao teste de software",
     "citation": "DELAMARO, Márcio Eduardo; MALDONADO, José Carlos; JINO, Mário (org.). Introdução ao teste de software. Rio de Janeiro: Elsevier, 2007. ISBN 9788535226348.",
     "scope": "Obra citada no kickoff. Dados bibliográficos conferidos no registro da USP; o texto integral do livro não foi consultado nesta revisão.",
     "location": "Registro bibliográfico do Repositório da USP.", "url": "https://repositorio.usp.br/item/001726007"},
    {"id": "B02", "group": GROUPS[1], "title": "ISTQB — Foundation Level Syllabus v4.0.1",
     "citation": "ISTQB. Certified Tester Foundation Level Syllabus. Version 4.0.1, 15 set. 2024.",
     "scope": "Seções 4.2.1 e 4.2.2: classes de equivalência e análise de valores limite. Seção 1.4.4: rastreabilidade entre base de teste e produtos de teste. Complementa o material da aula.",
     "location": "Documento oficial do ISTQB.", "url": "https://istqb.org/wp-content/uploads/2024/11/ISTQB_CTFL_Syllabus_v4.0.1.pdf"},
    {"id": "B03", "group": GROUPS[1], "title": "McCabe — A Complexity Measure",
     "citation": "MCCABE, Thomas J. A Complexity Measure. IEEE Transactions on Software Engineering, v. SE-2, n. 4, p. 308–320, 1976. DOI: 10.1109/TSE.1976.233837.",
     "scope": "Referência original da complexidade ciclomática. A implementação explicita V(G)=E−N+2P e a convenção de curto-circuito usada no grafo.",
     "location": "Artigo original identificado por DOI.", "url": "https://doi.org/10.1109/TSE.1976.233837"},
    {"id": "B04", "group": GROUPS[1], "title": "Rapps e Weyuker — testes baseados em fluxo de dados",
     "citation": "RAPPS, Sandra; WEYUKER, Elaine J. Selecting Software Test Data Using Data Flow Information. IEEE Transactions on Software Engineering, v. SE-11, n. 4, p. 367–375, 1985. DOI: 10.1109/TSE.1985.232226.",
     "scope": "Referência de apoio para critérios de teste que associam definições e usos de variáveis. A cobertura exibida no laboratório é limitada à suíte executada no interpretador.",
     "location": "Registro e resumo do artigo na IEEE.", "url": "https://doi.org/10.1109/TSE.1985.232226"},
    {"id": "B05", "group": GROUPS[1], "title": "DeMillo, Lipton e Sayward — teste de mutação",
     "citation": "DEMILLO, Richard A.; LIPTON, Richard J.; SAYWARD, Frederick G. Hints on Test Data Selection: Help for the Practicing Programmer. Computer, v. 11, n. 4, p. 34–41, 1978. DOI: 10.1109/C-M.1978.218136.",
     "scope": "Referência fundadora de teste de mutação. Os operadores e a fórmula diferencial apresentados no site seguem o escopo didático do projeto; sobrevivência não prova equivalência.",
     "location": "Artigo original identificado por DOI.", "url": "https://doi.org/10.1109/C-M.1978.218136"},
    {"id": "T01", "group": GROUPS[2], "title": "Python 3.12 — ast",
     "citation": "PYTHON SOFTWARE FOUNDATION. ast — Abstract syntax trees. Python 3.12 Documentation.",
     "scope": "Leitura da árvore sintática e identificação das construções aceitas pelo interpretador restrito.",
     "location": "Documentação oficial.", "url": "https://docs.python.org/3.12/library/ast.html"},
    {"id": "T02", "group": GROUPS[2], "title": "Python 3.12 — decimal",
     "citation": "PYTHON SOFTWARE FOUNDATION. decimal — Decimal fixed-point and floating-point arithmetic. Python 3.12 Documentation.",
     "scope": "Aritmética decimal, precisão e arredondamento usados no cálculo dos casos e do épsilon.",
     "location": "Documentação oficial.", "url": "https://docs.python.org/3.12/library/decimal.html"},
    {"id": "T03", "group": GROUPS[2], "title": "Streamlit — Secrets management",
     "citation": "STREAMLIT. Secrets management. Streamlit Documentation.",
     "scope": "Leitura da chave Gemini no servidor por st.secrets, sem expor o valor na interface. A chave do app fica disponível aos visitantes para a avaliação.",
     "location": "Documentação oficial.", "url": "https://docs.streamlit.io/develop/concepts/connections/secrets-management"},
    {"id": "T04", "group": GROUPS[2], "title": "Google — Gemini API",
     "citation": "GOOGLE. Gemini API Documentation. Google AI for Developers.",
     "scope": "Integração do assistente, modelos e chamadas à API. A revisão gerada por IA é apoio à análise e exige conferência humana.",
     "location": "Documentação oficial.", "url": "https://ai.google.dev/gemini-api/docs"},
    {"id": "T05", "group": GROUPS[2], "title": "Pyodide 0.27.7 — Getting started",
     "citation": "PYODIDE. Getting started. Pyodide Documentation, version 0.27.7.",
     "scope": "Execução de Python por WebAssembly no navegador, utilizada pela versão GitHub Pages.",
     "location": "Documentação da versão usada no site.", "url": "https://pyodide.org/en/0.27.7/usage/quickstart.html"},
    {"id": "T06", "group": GROUPS[2], "title": "GitHub Pages — documentação",
     "citation": "GITHUB. GitHub Pages documentation. GitHub Docs.",
     "scope": "Publicação dos arquivos estáticos do laboratório.",
     "location": "Documentação oficial.", "url": "https://docs.github.com/en/pages"},
    {"id": "T07", "group": GROUPS[2], "title": "Plotly — Python Graphing Library",
     "citation": "PLOTLY. Plotly Python Graphing Library. Plotly Documentation.",
     "scope": "Visualização dos pontos de fronteira na interface Streamlit.",
     "location": "Documentação oficial.", "url": "https://plotly.com/python/"},
]

MODULE_SOURCES = {
    "Caixa-preta": ["M01", "M02", "M04", "B01", "B02", "T02"],
    "Caixa-branca": ["M02", "B03", "T01"],
    "Def-Uso e mutação": ["M02", "B04", "B05"],
    "Requisitos e RTM": ["M03", "B02"],
    "Gemini": ["M01", "M02", "T03", "T04"],
}


def references_markdown():
    lines = ["## Fontes e referências", "", SOURCE_NOTE, "", "### Origem por módulo", ""]
    for module, ids in MODULE_SOURCES.items():
        lines.append(f"- {module}: {', '.join(ids)}.")
    for group in GROUPS:
        lines += ["", "### " + group, ""]
        for source in SOURCES:
            if source["group"] != group:
                continue
            lines += [f"**[{source['id']}] {source['title']}**", "", source["citation"], "",
                      source["scope"], "", source["location"]]
            if source["url"]:
                lines += [f"Disponível em: {source['url']}. Acesso em: {REVIEW_DATE}."]
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def public_catalog():
    return {"review_date": REVIEW_DATE, "note": SOURCE_NOTE, "groups": GROUPS,
            "sources": SOURCES, "modules": MODULE_SOURCES, "markdown": references_markdown()}
