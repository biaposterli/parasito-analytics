import pandas as pd

REQUIRED_COLUMNS = {
    "fonte": "Fonte/levantamento",
    "id_paciente": "Identificador do paciente",
    "nome_crianca": "Nome/identificação da criança",
    "coleta": "Momento da coleta (P1/P2/P3)",
    "status_amostra": "Status do pote de fezes",
    "status_lamina": "Status da lâmina/fita",
    "metodo_graham": "Resultado Graham",
    "metodo_baermann_picanco": "Resultado Baermann-Picanço",
    "metodo_hpj": "Resultado HPJ",
    "metodo_willis": "Resultado Willis",
    "especies_detectadas_str": "Espécies detectadas",
}

ALIASES = {
    "ID_PACIENTE": "id_paciente",
    "ID": "id_paciente",
    "PACIENTE": "id_paciente",
    "NOME": "nome_crianca",
    "NOME_CRIANCA": "nome_crianca",
    "COLETA": "coleta",
    "MOMENTO": "coleta",
    "STATUS_AMOSTRA": "status_amostra",
    "STATUS_LAMINA": "status_lamina",
    "GRAHAM": "metodo_graham",
    "METODO_GRAHAM": "metodo_graham",
    "BAERMANN": "metodo_baermann_picanco",
    "BAERMANN-PICANCO": "metodo_baermann_picanco",
    "BAERMANN_PICANCO": "metodo_baermann_picanco",
    "METODO_BAERMANN_PICANCO": "metodo_baermann_picanco",
    "HPJ": "metodo_hpj",
    "METODO_HPJ": "metodo_hpj",
    "WILLIS": "metodo_willis",
    "METODO_WILLIS": "metodo_willis",
    "ESPECIES": "especies_detectadas_str",
    "ESPECIES_DETECTADAS": "especies_detectadas_str",
    "ESPECIES_DETECTADAS_STR": "especies_detectadas_str",
}

def normalize_name(x):
    return (
        str(x).strip().upper()
        .replace(" ", "_")
        .replace("/", "_")
    )

def validate_dataframe(df):
    errors = []
    warnings = []
    original = list(df.columns)

    # V1: exact layout first, then simple aliases
    rename = {}
    normalized = {normalize_name(c): c for c in original}

    for alias, target in ALIASES.items():
        if target not in df.columns and alias in normalized:
            rename[normalized[alias]] = target

    if rename:
        df.rename(columns=rename, inplace=True)

    rows = []
    for col, desc in REQUIRED_COLUMNS.items():
        found = col in df.columns
        rows.append({
            "Campo": col,
            "Descrição": desc,
            "Status": "✓ Encontrado" if found else "✗ Ausente",
        })
        if not found:
            errors.append(f"Coluna obrigatória ausente: `{col}`.")

    if "coleta" in df.columns:
        valid_coletas = {"P1", "P2", "P3"}
        vals = set(df["coleta"].dropna().astype(str).str.strip().str.upper())
        extra = sorted(vals - valid_coletas)
        if extra:
            warnings.append(
                f"Valores de coleta fora do padrão P1/P2/P3 encontrados: {extra}"
            )

    if "id_paciente" in df.columns and "coleta" in df.columns:
        dup = df.duplicated(["id_paciente", "coleta"]).sum()
        if dup:
            errors.append(
                f"Foram encontradas {dup} linhas duplicadas para a chave "
                "`id_paciente + coleta`."
            )

    return len(errors) == 0, pd.DataFrame(rows), errors, warnings
