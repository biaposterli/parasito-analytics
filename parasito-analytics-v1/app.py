import streamlit as st
import pandas as pd
from io import BytesIO
from engine.validation import validate_dataframe
from engine.analysis import run_analysis
from engine.export_excel import create_excel
from engine.report_pdf import create_pdf
from engine.plots import make_plots

st.set_page_config(
    page_title="Parasito Analytics",
    page_icon="🦠",
    layout="wide",
)

st.title("🦠 Parasito Analytics")
st.caption("Análise epidemiológica automatizada de parasitoses intestinais")

st.info(
    "V1 baseada no notebook de análise fornecido. "
    "A unidade de análise é a criança; cada criança pode ter até três coletas. "
    "Use dados anonimizados nesta versão."
)

c1, c2 = st.columns(2)

with c1:
    st.subheader("1. Baixe o modelo")
    model_path = "assets/Modelo_Analise_Parasitologica.xlsx"
    with open(model_path, "rb") as f:
        st.download_button(
            "⬇️ Baixar modelo Excel",
            data=f.read(),
            file_name="Modelo_Analise_Parasitologica.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

with c2:
    st.subheader("2. Envie sua planilha")
    uploaded = st.file_uploader(
        "Arquivo .xlsx",
        type=["xlsx"],
        help="A V1 espera a aba 'Base_Consolidada' com o layout do modelo."
    )

if uploaded is not None:
    try:
        xls = pd.ExcelFile(uploaded)
        sheet = "Base_Consolidada" if "Base_Consolidada" in xls.sheet_names else xls.sheet_names[0]
        df = pd.read_excel(uploaded, sheet_name=sheet)
    except Exception as e:
        st.error(f"Não foi possível ler o Excel: {e}")
        st.stop()

    st.divider()
    st.subheader("🔎 Validação da planilha")

    ok, report, errors, warnings = validate_dataframe(df)

    if errors:
        for msg in errors:
            st.error(msg)

    if warnings:
        for msg in warnings:
            st.warning(msg)

    st.dataframe(report, use_container_width=True, hide_index=True)

    if not ok:
        st.stop()

    st.success(f"Estrutura reconhecida. {len(df):,} registros de coleta encontrados.")

    with st.expander("Prévia dos dados"):
        st.dataframe(df.head(20), use_container_width=True)

    if st.button("🚀 Executar análise", type="primary", use_container_width=True):
        with st.spinner("Executando análise epidemiológica..."):
            try:
                results = run_analysis(df)
                plots = make_plots(results)
                excel_bytes = create_excel(results)
                pdf_bytes = create_pdf(results, plots)
                st.session_state["results"] = results
                st.session_state["plots"] = plots
                st.session_state["excel"] = excel_bytes
                st.session_state["pdf"] = pdf_bytes
            except Exception as e:
                st.exception(e)
                st.stop()

    if "results" in st.session_state:
        results = st.session_state["results"]
        plots = st.session_state["plots"]

        st.divider()
        st.subheader("📊 Resultado da análise")

        a, b, c, d = st.columns(4)
        a.metric("Crianças cadastradas", f"{results['n_criancas_total']:,}")
        b.metric("Crianças analisáveis", f"{results['n_criancas_analisaveis']:,}")
        c.metric("Prevalência fecal", f"{results['prevalencia_fecal']:.1f}%")
        d.metric("Poliparasitismo", f"{results['poliparasitismo_pct']:.1f}%")

        st.caption(
            "A prevalência principal usa crianças com ao menos uma amostra fecal analisada, "
            "seguindo a lógica do notebook."
        )

        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "Resumo", "Prevalência", "Poliparasitismo",
            "Métodos", "Coletas"
        ])

        with tab1:
            st.subheader("Categoria de amostragem")
            st.dataframe(
                results["resumo_categoria"],
                use_container_width=True
            )
            st.subheader("Participação — pote de fezes")
            st.dataframe(
                results["resumo_participacao"],
                use_container_width=True
            )
            st.subheader("Participação — lâmina")
            st.dataframe(
                results["resumo_participacao_lamina"],
                use_container_width=True
            )

        with tab2:
            st.subheader("Prevalência por espécie")
            st.dataframe(
                results["resumo_especies"],
                use_container_width=True
            )
            if plots.get("prevalencia_especies"):
                st.image(plots["prevalencia_especies"], use_container_width=True)

            st.write(
                f"Patogênicos: **{results['patogenicos_pct']:.1f}%** | "
                f"Comensais: **{results['comensais_pct']:.1f}%**"
            )

        with tab3:
            st.dataframe(
                results["resumo_poli"],
                use_container_width=True,
                hide_index=True
            )
            if plots.get("poliparasitismo"):
                st.image(plots["poliparasitismo"], use_container_width=True)

            st.subheader("Combinações de espécies")
            st.dataframe(
                results["combos"],
                use_container_width=True,
                hide_index=True
            )

        with tab4:
            st.dataframe(
                results["resumo_metodos"],
                use_container_width=True,
                hide_index=True
            )
            if plots.get("metodos"):
                st.image(plots["metodos"], use_container_width=True)

            st.subheader("Espécie × método")
            st.dataframe(
                results["tabela_cruzada"],
                use_container_width=True
            )

        with tab5:
            st.dataframe(
                results["prev_por_n_coletas"],
                use_container_width=True
            )
            if plots.get("coletas"):
                st.image(plots["coletas"], use_container_width=True)

        st.divider()
        st.subheader("📥 Baixar resultados")

        d1, d2 = st.columns(2)
        with d1:
            st.download_button(
                "📊 Baixar Excel completo",
                data=st.session_state["excel"],
                file_name="Resumo_Analise_Epidemiologica.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        with d2:
            st.download_button(
                "📄 Baixar relatório PDF",
                data=st.session_state["pdf"],
                file_name="Relatorio_Epidemiologico.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
