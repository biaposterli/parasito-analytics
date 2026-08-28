import numpy as np
import pandas as pd
from itertools import combinations

METODOS = [
    "metodo_graham",
    "metodo_baermann_picanco",
    "metodo_hpj",
    "metodo_willis",
]
NOMES_METODOS = [
    "Graham",
    "Baermann-Picanço",
    "HPJ",
    "Willis",
]

PATOGENICOS = {
    "Enterobius vermicularis",
    "Giardia lamblia",
    "Balantidium coli",
}

COMENSAIS = {
    "Endolimax nana",
    "Entamoeba histolytica/dispar",
    "Iodamoeba butschlii",
}

def parse_metodo_positivo(col):
    return ~col.isin(["Negativo", "Amostra insuficiente"]) & col.notna()

def _agrega_crianca(g):
    especies = set()

    for s in g["especies_detectadas_str"].dropna():
        especies.update(
            e.strip()
            for e in str(s).split(";")
            if e.strip()
        )

    n_pote = (g["status_amostra"] == "Entregue").sum()
    n_lamina = (g["status_lamina"] == "Entregue").sum()

    if n_pote > 0 and n_lamina > 0:
        categoria = "Fezes e lâmina"
    elif n_pote > 0:
        categoria = "Apenas fezes (sem lâmina)"
    elif n_lamina > 0:
        categoria = "Apenas lâmina (sem fezes)"
    else:
        categoria = "Nenhum material"

    resultado = {
        "n_coletas_registradas": len(g),
        "n_coletas_pote_entregue": int(n_pote),
        "n_coletas_lamina_entregue": int(n_lamina),
        "categoria_amostragem": categoria,
        "participou_estudo": (n_pote > 0) or (n_lamina > 0),
        "positivo_algum_metodo": len(especies) > 0,
        "n_especies_distintas": len(especies),
        "poliparasitado": len(especies) > 1,
        "especies": "; ".join(sorted(especies)) if especies else "",
    }

    for col, nome in zip(METODOS, NOMES_METODOS):
        resultado[f"positivo_{nome}"] = bool(g[f"_pos_{col}"].any())

    return pd.Series(resultado)

def run_analysis(df):
    df = df.copy()

    # Normalização mínima
    for col in ["status_amostra", "status_lamina", "coleta"]:
        df[col] = df[col].where(df[col].isna(), df[col].astype(str).str.strip())

    for col in METODOS:
        df[f"_pos_{col}"] = parse_metodo_positivo(df[col])

    por_crianca = (
        df.groupby(["fonte", "id_paciente", "nome_crianca"], dropna=False)
        .apply(_agrega_crianca, include_groups=False)
        .reset_index()
    )

    resumo_participacao = pd.DataFrame(
        {
            "n": [
                (por_crianca["n_coletas_pote_entregue"] == 0).sum(),
                (
                    (por_crianca["n_coletas_pote_entregue"] > 0)
                    & (
                        por_crianca["n_coletas_pote_entregue"]
                        < por_crianca["n_coletas_registradas"]
                    )
                ).sum(),
                (
                    por_crianca["n_coletas_pote_entregue"]
                    == por_crianca["n_coletas_registradas"]
                ).sum(),
            ]
        },
        index=[
            "Nenhum pote entregue",
            "Entrega parcial de potes",
            "Todos os potes entregues",
        ],
    )
    resumo_participacao["%"] = (
        resumo_participacao["n"] / len(por_crianca) * 100
    ).round(1)

    resumo_participacao_lamina = pd.DataFrame(
        {
            "n": [
                (por_crianca["n_coletas_lamina_entregue"] == 0).sum(),
                (
                    (por_crianca["n_coletas_lamina_entregue"] > 0)
                    & (
                        por_crianca["n_coletas_lamina_entregue"]
                        < por_crianca["n_coletas_registradas"]
                    )
                ).sum(),
                (
                    por_crianca["n_coletas_lamina_entregue"]
                    == por_crianca["n_coletas_registradas"]
                ).sum(),
            ]
        },
        index=[
            "Nenhuma lâmina entregue",
            "Entrega parcial de lâminas",
            "Todas as lâminas entregues",
        ],
    )
    resumo_participacao_lamina["%"] = (
        resumo_participacao_lamina["n"] / len(por_crianca) * 100
    ).round(1)

    resumo_categoria = (
        por_crianca["categoria_amostragem"]
        .value_counts()
        .reindex(
            [
                "Fezes e lâmina",
                "Apenas fezes (sem lâmina)",
                "Apenas lâmina (sem fezes)",
                "Nenhum material",
            ],
            fill_value=0,
        )
        .to_frame("n")
    )
    resumo_categoria["%"] = (
        resumo_categoria["n"] / len(por_crianca) * 100
    ).round(1)

    crianca_analisavel = por_crianca[por_crianca["participou_estudo"]].copy()
    crianca_fecal_analisada = crianca_analisavel[
        crianca_analisavel["n_coletas_pote_entregue"] > 0
    ].copy()
    crianca_apenas_lamina = crianca_analisavel[
        crianca_analisavel["n_coletas_pote_entregue"] == 0
    ].copy()

    prevalencia_fecal = (
        crianca_fecal_analisada["positivo_algum_metodo"].mean() * 100
        if len(crianca_fecal_analisada)
        else np.nan
    )

    prevalencia_lamina = (
        crianca_apenas_lamina["positivo_algum_metodo"].mean() * 100
        if len(crianca_apenas_lamina)
        else np.nan
    )

    prevalencia_combinada = (
        crianca_analisavel["positivo_algum_metodo"].mean() * 100
        if len(crianca_analisavel)
        else np.nan
    )

    especies_lista = []
    for s in crianca_fecal_analisada["especies"]:
        especies_lista.extend(
            [e.strip() for e in str(s).split(";") if e.strip()]
        )

    if especies_lista:
        freq_especies = pd.Series(especies_lista).value_counts()
        resumo_especies = pd.DataFrame(
            {
                "n_criancas_positivas": freq_especies,
                "prevalencia_%": (
                    freq_especies / len(crianca_fecal_analisada) * 100
                ).round(1),
            }
        ).sort_values("n_criancas_positivas", ascending=False)
        resumo_especies["categoria"] = resumo_especies.index.map(
            lambda x: (
                "Patogênico"
                if x in PATOGENICOS
                else ("Comensal" if x in COMENSAIS else "Não classificado")
            )
        )
    else:
        resumo_especies = pd.DataFrame(
            columns=[
                "n_criancas_positivas",
                "prevalencia_%",
                "categoria",
            ]
        )

    if len(crianca_fecal_analisada):
        crianca_fecal_analisada["tem_patogenico"] = (
            crianca_fecal_analisada["especies"].apply(
                lambda s: any(
                    e.strip() in PATOGENICOS
                    for e in str(s).split(";")
                    if e.strip()
                )
            )
        )
        crianca_fecal_analisada["tem_comensal"] = (
            crianca_fecal_analisada["especies"].apply(
                lambda s: any(
                    e.strip() in COMENSAIS
                    for e in str(s).split(";")
                    if e.strip()
                )
            )
        )
        patogenicos_pct = (
            crianca_fecal_analisada["tem_patogenico"].mean() * 100
        )
        comensais_pct = (
            crianca_fecal_analisada["tem_comensal"].mean() * 100
        )
    else:
        patogenicos_pct = np.nan
        comensais_pct = np.nan

    if len(crianca_fecal_analisada):
        poli = int(crianca_fecal_analisada["poliparasitado"].sum())
        mono = int(
            (crianca_fecal_analisada["n_especies_distintas"] == 1).sum()
        )
        neg = int(
            (crianca_fecal_analisada["n_especies_distintas"] == 0).sum()
        )
    else:
        poli = mono = neg = 0

    resumo_poli = pd.DataFrame(
        {
            "categoria": [
                "Negativo",
                "Monoparasitismo (1 espécie)",
                "Poliparasitismo (>1 espécie)",
            ],
            "n": [neg, mono, poli],
        }
    )
    resumo_poli["%"] = (
        resumo_poli["n"] / len(crianca_fecal_analisada) * 100
        if len(crianca_fecal_analisada)
        else np.nan
    )
    resumo_poli["%"] = resumo_poli["%"].round(1)

    combos = (
        crianca_fecal_analisada.loc[
            crianca_fecal_analisada["poliparasitado"], "especies"
        ]
        .apply(
            lambda s: " + ".join(
                sorted(e.strip() for e in str(s).split(";") if e.strip())
            )
        )
        .value_counts()
        .rename_axis("combinação")
        .reset_index(name="n_crianças")
    )

    linhas = []
    for col, nome in zip(METODOS, NOMES_METODOS):
        status_col = (
            "status_lamina" if col == "metodo_graham" else "status_amostra"
        )
        n_coletas_col = (
            "n_coletas_lamina_entregue"
            if col == "metodo_graham"
            else "n_coletas_pote_entregue"
        )

        n_realizados_coletas = int((df[status_col] == "Entregue").sum())
        criancas_testaveis = crianca_analisavel[
            crianca_analisavel[n_coletas_col] > 0
        ]
        positivos = int(criancas_testaveis[f"positivo_{nome}"].sum())

        linhas.append(
            {
                "metodo": nome,
                "amostra_biologica": (
                    "Lâmina" if col == "metodo_graham" else "Pote de fezes"
                ),
                "n_coletas_realizadas": n_realizados_coletas,
                "n_criancas_testaveis": len(criancas_testaveis),
                "n_criancas_positivas": positivos,
                "%_prevalencia_detectada": (
                    round(positivos / len(criancas_testaveis) * 100, 1)
                    if len(criancas_testaveis)
                    else np.nan
                ),
            }
        )

    resumo_metodos = pd.DataFrame(linhas)

    registros = []
    for _, row in df.iterrows():
        for col, nome in zip(METODOS, NOMES_METODOS):
            val = row[col]
            if pd.isna(val) or val in ("Negativo", "Amostra insuficiente"):
                continue
            for especie in str(val).split(" + "):
                registros.append(
                    {
                        "id_paciente": row["id_paciente"],
                        "metodo": nome,
                        "especie": especie.strip(),
                    }
                )

    if registros:
        especie_metodo = pd.DataFrame(registros).drop_duplicates(
            subset=["id_paciente", "metodo", "especie"]
        )
        tabela_cruzada = pd.crosstab(
            especie_metodo["especie"], especie_metodo["metodo"]
        )
    else:
        tabela_cruzada = pd.DataFrame()

    prev_por_n_coletas = (
        crianca_fecal_analisada.groupby(
            "n_coletas_pote_entregue"
        )["positivo_algum_metodo"]
        .agg(["mean", "count"])
        .rename(
            columns={
                "mean": "prevalencia_%",
                "count": "n_criancas",
            }
        )
    )
    if len(prev_por_n_coletas):
        prev_por_n_coletas["prevalencia_%"] = (
            prev_por_n_coletas["prevalencia_%"] * 100
        ).round(1)

    return {
        "df": df,
        "por_crianca": por_crianca,
        "crianca_analisavel": crianca_analisavel,
        "crianca_fecal_analisada": crianca_fecal_analisada,
        "crianca_apenas_lamina": crianca_apenas_lamina,
        "resumo_categoria": resumo_categoria,
        "resumo_participacao": resumo_participacao,
        "resumo_participacao_lamina": resumo_participacao_lamina,
        "resumo_especies": resumo_especies,
        "resumo_poli": resumo_poli,
        "combos": combos,
        "resumo_metodos": resumo_metodos,
        "tabela_cruzada": tabela_cruzada,
        "prev_por_n_coletas": prev_por_n_coletas,
        "n_criancas_total": len(por_crianca),
        "n_criancas_analisaveis": len(crianca_analisavel),
        "n_coletas_total": len(df),
        "prevalencia_fecal": prevalencia_fecal,
        "prevalencia_lamina": prevalencia_lamina,
        "prevalencia_combinada": prevalencia_combinada,
        "poliparasitismo_pct": (
            poli / len(crianca_fecal_analisada) * 100
            if len(crianca_fecal_analisada)
            else np.nan
        ),
        "patogenicos_pct": patogenicos_pct,
        "comensais_pct": comensais_pct,
    }
