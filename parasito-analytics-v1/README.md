# Parasito Analytics — V1

Aplicação Streamlit para análise epidemiológica de parasitoses intestinais.

## O que a V1 faz

- recebe uma planilha `.xlsx`;
- valida a estrutura;
- consolida os dados em nível de criança;
- calcula participação;
- classifica a categoria de amostragem;
- calcula prevalência geral;
- calcula prevalência por espécie;
- separa patogênicos/comensais conforme a lista do notebook;
- calcula poliparasitismo;
- compara Graham, Baermann-Picanço, HPJ e Willis;
- cria tabela espécie × método;
- avalia prevalência por número de coletas fecais;
- gera Excel;
- gera PDF.

## Estrutura

```text
parasito-analytics/
├── app.py
├── requirements.txt
├── README.md
├── .streamlit/
│   └── config.toml
├── engine/
│   ├── __init__.py
│   ├── validation.py
│   ├── analysis.py
│   ├── plots.py
│   ├── export_excel.py
│   └── report_pdf.py
└── assets/
    └── Modelo_Analise_Parasitologica.xlsx
```

## Rodar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

Execute o comando a partir da raiz do repositório.

## Deploy

No Streamlit Community Cloud:

- Repository: `SEU_USUARIO/parasito-analytics`
- Branch: `main`
- Main file path: `app.py`

## Segurança

A V1 foi pensada para testes com dados anonimizados. Não publique dados pessoais identificáveis de pacientes no GitHub. Para uso institucional, implemente autenticação, política de retenção/exclusão e armazenamento/processamento compatível com os requisitos aplicáveis antes de usar dados reais.
