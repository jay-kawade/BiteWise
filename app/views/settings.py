"""
settings.py -- "About & model"

What BiteWise is, what it won't do, how the ML model scored on held-out
data, and a quick system status check. Metrics are read straight from the
metadata written by src/ml/train.py -- nothing is typed in by hand.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.components.cards import page_header, section, stat
from app.components.disclaimers import ALLERGEN_DISCLAIMER, HEALTH_DISCLAIMER
from app.components.styles import BASIL, LEAF, SAND, render_source_badge
from src.database import repositories as repo
from src.ml.predict import get_model_metadata, is_model_available
from src.scanner.ocr import is_real_ocr_available
from src.utils import config

page_header("About BiteWise", "How it works, what it won't do, and how well the model actually performs.")

tab_about, tab_model, tab_status = st.tabs(["About", "Model", "Status"])

with tab_about:
    left, right = st.columns([1.4, 1], gap="large")
    with left:
        st.markdown("""
BiteWise is our final-year project: a nutrition tracker that tries to be
honest about where every number comes from.

- **Targets** are calculated from published formulas (Mifflin-St Jeor, ISSN, IOM).
- **Suggestions and meal plans** come from a weighted scoring system you can read
  in `src/recommendation/ranking.py`. Every suggestion lists its reasons.
- **The scanner** cleans up a label photo with OpenCV, reads it with Tesseract,
  and parses out nutrients and ingredients.
- **One ML model** guesses a food's likely meal from its nutrients. It's always
  labelled as a prediction.
- **The assistant** answers from your own data, either through an LLM with tools
  or a simple offline router.

Architecture, methods and limitations are written up in `README.md` and `docs/`.
""")
        st.markdown("**Where numbers come from**")
        st.markdown(":green-badge[:material/calculate: Calculated] &nbsp; :orange-badge[:material/rule: Rule-based] "
                    "&nbsp; :violet-badge[:material/model_training: ML prediction]")

    with right:
        with st.container(border=True):
            st.markdown("**What BiteWise doesn't do**")
            st.markdown(
                "- Diagnose, treat or manage any medical condition\n"
                "- Replace a doctor or registered dietitian\n"
                "- Guarantee a product is free of allergens or cross-contamination\n"
                "- Give medication or treatment advice"
            )
        st.caption(HEALTH_DISCLAIMER)
        st.caption(ALLERGEN_DISCLAIMER)

with tab_model:
    if not is_model_available():
        st.warning("No trained model yet. Run `python -m src.ml.train`, then reload.", icon=":material/warning:")
    else:
        meta = get_model_metadata()
        results = meta.get("results_by_model", {})
        best = meta.get("selected_model")
        best_metrics = results.get(best, {}).get("metrics", {})

        st.markdown(f"**Task:** {meta.get('task')}")
        render_source_badge("ml")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            stat("Selected model", str(best).replace("_", " ").title(), note="best macro-F1 on test split")
        with c2:
            stat("Macro F1", f"{best_metrics.get('f1_macro', 0):.3f}", colour=BASIL)
        with c3:
            stat("Accuracy", f"{best_metrics.get('accuracy', 0):.1%}")
        with c4:
            stat("Test set", f"{meta.get('dataset_size_test')}", "foods", note=f"of {meta.get('dataset_size_total')} total")
        if meta.get("dataset_note"):
            st.caption(meta["dataset_note"])

        section("All candidates", "held-out test set")
        rows = [{"model": name, **r["metrics"]} for name, r in results.items()]
        df = pd.DataFrame(rows).set_index("model")
        st.dataframe(df.style.format(precision=3).highlight_max(axis=0, color="#E3ECE2"), width="stretch")

        left, right = st.columns(2, gap="large")
        with left:
            section("Confusion matrix", str(best))
            # stored as {predicted_x: {actual_y: count}} -> rows = actual, columns = predicted
            cm = pd.DataFrame(results[best]["confusion_matrix"])
            z = cm.values
            fig = go.Figure(go.Heatmap(
                z=z,
                x=[c.replace("predicted_", "") for c in cm.columns],
                y=[i.replace("actual_", "") for i in cm.index], colorscale=[[0, SAND], [1, BASIL]], showscale=False,
                text=z, texttemplate="%{text}", hovertemplate="true %{y} → predicted %{x}: %{z}<extra></extra>",
            ))
            fig.update_layout(height=320, yaxis=dict(autorange="reversed", gridcolor="rgba(0,0,0,0)", title="actual"),
                              xaxis=dict(title="predicted"), margin=dict(l=8, r=8, t=8, b=40))
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
        with right:
            fi = meta.get("feature_importance", {})
            if fi:
                section("Feature importance")
                s = pd.Series(fi).sort_values()
                fig = go.Figure(go.Bar(x=s.values, y=[i.replace("_", " ") for i in s.index], orientation="h",
                                       marker=dict(color=LEAF, cornerradius=4),
                                       hovertemplate="%{y}: %{x:.3f}<extra></extra>"))
                fig.update_layout(height=320, xaxis=dict(gridcolor=SAND), yaxis=dict(gridcolor="rgba(0,0,0,0)"))
                st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
                st.caption("Describes how the model behaves, not why a food is good or bad for you.")

        section("Not evaluated")
        st.markdown(
            "- **Recommendations & meal plans** are deterministic scoring, so there's no accuracy number to "
            "report. Precision@k would need labelled user-preference data, which we don't have.\n"
            "- **OCR parsing** hasn't been benchmarked against a labelled set of real label photos. "
            "The sample labels are only there to demo the pipeline."
        )

with tab_status:
    c1, c2, c3 = st.columns(3)
    with c1:
        stat("Foods in database", f"{repo.count_foods()}")
    with c2:
        stat("Profiles", f"{len(repo.list_users())}")
    with c3:
        stat("Mode", "Demo" if config.DEMO_MODE else "Live")

    st.write("")
    checks = [
        ("ML model trained", is_model_available()),
        ("Tesseract OCR installed", is_real_ocr_available()),
        ("LLM assistant configured", config.LLM_ASSISTANT_ENABLED),
    ]
    for label, ok in checks:
        st.markdown(f":material/{'check_circle' if ok else 'radio_button_unchecked'}: {label}"
                    f"{'' if ok else ' — :gray[not available, using fallback]'}")
    st.caption(f"Database: `{config.DATABASE_PATH}`")
