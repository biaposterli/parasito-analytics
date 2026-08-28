from io import BytesIO
import matplotlib.pyplot as plt

def _save(fig):
    buf = BytesIO()
    fig.savefig(buf, format="png", dpi=160, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()

def make_plots(results):
    out = {}

    especies = results["resumo_especies"]
    if len(especies):
        fig, ax = plt.subplots(figsize=(9, 5))
        s = especies["prevalencia_%"].sort_values()
        ax.barh(s.index.astype(str), s.values)
        ax.set_xlabel("Prevalência (%) — proporção de crianças")
        ax.set_title("Prevalência por espécie")
        for i, v in enumerate(s.values):
            ax.text(v, i, f" {v:.1f}%", va="center")
        fig.tight_layout()
        out["prevalencia_especies"] = _save(fig)

    poli = results["resumo_poli"]
    if len(poli):
        fig, ax = plt.subplots(figsize=(7, 5))
        ax.pie(
            poli["n"],
            labels=poli["categoria"],
            autopct="%1.1f%%",
            startangle=90,
        )
        ax.set_title("Negativo / monoparasitismo / poliparasitismo")
        fig.tight_layout()
        out["poliparasitismo"] = _save(fig)

    met = results["resumo_metodos"]
    if len(met):
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.bar(met["metodo"], met["%_prevalencia_detectada"])
        ax.set_ylabel("% de crianças positivas")
        ax.set_title("Prevalência detectada por método")
        ax.tick_params(axis="x", rotation=20)
        fig.tight_layout()
        out["metodos"] = _save(fig)

    col = results["prev_por_n_coletas"]
    if len(col):
        fig, ax = plt.subplots(figsize=(7, 5))
        ax.bar(col.index.astype(str), col["prevalencia_%"])
        ax.set_xlabel("Nº de potes de fezes entregues")
        ax.set_ylabel("% de crianças positivas")
        ax.set_title("Prevalência por número de coletas fecais")
        fig.tight_layout()
        out["coletas"] = _save(fig)

    return out
