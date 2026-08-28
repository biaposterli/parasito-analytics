from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
)

def _table_from_df(df, max_rows=25):
    if df is None or len(df) == 0:
        return None
    d = df.reset_index()
    d = d.head(max_rows)
    data = [list(d.columns)] + [
        [str(v) for v in row] for row in d.itertuples(index=False, name=None)
    ]
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#D9EAF7")),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("GRID", (0,0), (-1,-1), 0.4, colors.grey),
        ("FONTSIZE", (0,0), (-1,-1), 7),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
    ]))
    return table

def create_pdf(results, plots):
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(
        "Relatório de Análise Epidemiológica de Parasitoses",
        styles["Title"]
    ))
    story.append(Spacer(1, 10))

    story.append(Paragraph(
        "Baseado na lógica do notebook fornecido: unidade de análise = criança; "
        "até três coletas por criança; prevalência principal entre crianças com "
        "amostra fecal analisada.",
        styles["BodyText"]
    ))
    story.append(Spacer(1, 12))

    metrics = [
        ["Indicador", "Resultado"],
        ["Crianças cadastradas", str(results["n_criancas_total"])],
        ["Crianças analisáveis", str(results["n_criancas_analisaveis"])],
        ["Coletas registradas", str(results["n_coletas_total"])],
        ["Prevalência fecal", f"{results['prevalencia_fecal']:.1f}%"],
        ["Poliparasitismo", f"{results['poliparasitismo_pct']:.1f}%"],
    ]
    t = Table(metrics, colWidths=[260, 160])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#D9EAF7")),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
    ]))
    story.append(t)
    story.append(Spacer(1, 16))

    story.append(Paragraph("1. Categoria de amostragem", styles["Heading2"]))
    t = _table_from_df(results["resumo_categoria"])
    if t: story.append(t)
    story.append(Spacer(1, 12))

    story.append(Paragraph("2. Prevalência por espécie", styles["Heading2"]))
    t = _table_from_df(results["resumo_especies"])
    if t: story.append(t)

    if plots.get("prevalencia_especies"):
        story.append(Spacer(1, 10))
        story.append(Image(BytesIO(plots["prevalencia_especies"]), width=500, height=280))

    story.append(Spacer(1, 12))
    story.append(Paragraph("3. Poliparasitismo", styles["Heading2"]))
    t = _table_from_df(results["resumo_poli"])
    if t: story.append(t)

    if plots.get("poliparasitismo"):
        story.append(Spacer(1, 10))
        story.append(Image(BytesIO(plots["poliparasitismo"]), width=430, height=300))

    story.append(Spacer(1, 12))
    story.append(Paragraph("4. Comparação entre métodos", styles["Heading2"]))
    t = _table_from_df(results["resumo_metodos"])
    if t: story.append(t)

    if plots.get("metodos"):
        story.append(Spacer(1, 10))
        story.append(Image(BytesIO(plots["metodos"]), width=480, height=300))

    story.append(Spacer(1, 12))
    story.append(Paragraph("5. Prevalência por número de coletas fecais", styles["Heading2"]))
    t = _table_from_df(results["prev_por_n_coletas"])
    if t: story.append(t)

    story.append(Spacer(1, 16))
    story.append(Paragraph(
        "Observação: a comparação bruta entre métodos deve ser interpretada com "
        "cautela porque os métodos possuem alvos diagnósticos distintos. "
        "O grupo que entregou apenas lâmina é reportado separadamente, pois não "
        "teve amostra fecal analisada.",
        styles["BodyText"]
    ))

    doc.build(story)
    buf.seek(0)
    return buf.getvalue()
