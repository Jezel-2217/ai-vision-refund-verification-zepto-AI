"""
Streamlit ops dashboard for Module 3 (Zepto Smart Commerce AI Platform).

Three tabs:
  1. Submit a claim   — pick a real delivered order, upload 1-3 photos,
                         run the full pipeline live, see the vision
                         report + decision.
  2. Claims           — table of every claim written to Postgres/SQLite,
                         filterable by decision, with the manual-review
                         queue called out.
  3. Thresholds       — the ops-configurable confidence thresholds
                         (auto_approve_min / manual_review_min), editable
                         here and read live by the rules engine — no
                         redeploy needed, exactly as the spec requires.

Run with:
    streamlit run dashboard.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pandas as pd
import streamlit as st

from src import db
from src.config import settings
from src.pipeline import submit_claim

st.set_page_config(page_title="AI Vision Refund Verification", page_icon="📦", layout="wide")

db.init_db()
db.load_real_data_if_needed()

st.title("📦 AI Vision Refund Verification — Ops Dashboard")
st.caption(
    f"Vision backend: **{settings.vision_backend}**  ·  "
    f"Storage backend: **{settings.storage_backend}**  ·  "
    f"Database: **{'PostgreSQL' if settings.database_url.startswith('postgres') else 'SQLite (local file)'}**"
)

tab_submit, tab_claims, tab_thresholds = st.tabs(["Submit a claim", "Claims", "Thresholds"])

# ---------------------------------------------------------------------
# Tab 1 — Submit a claim
# ---------------------------------------------------------------------
with tab_submit:
    st.subheader("Simulate a customer refund claim")
    st.write("A refund claim is filed against a real delivered order — pick one below, "
             "then upload 1–3 damage photos exactly as the customer app would send.")

    orders = db.list_orders(limit=50)
    if not orders:
        st.warning(
            "No orders loaded. This project no longer seeds synthetic demo data — "
            "it reads the real Zepto dataset from the `data/` folder (see README.md's "
            "\"Real data\" section). Make sure `data/processed/*.parquet` and "
            "`data/catalogue/*.csv` are present, then restart."
        )
    else:
        order_labels = {
            o["id"]: (
                f"{o['source_order_id']} · ₹{o['order_amount']:.2f} · {o['store_id']} · "
                f"{o['payment_status']} · delivered {o['delivered_at']}"
            )
            for o in orders
        }
        selected_order_id = st.selectbox(
            "Order", options=list(order_labels.keys()), format_func=lambda oid: order_labels[oid]
        )

        items = db.get_order_items(selected_order_id)
        if items:
            st.caption(
                "Real item(s) on this order: "
                + ", ".join(f"{i['product_name']} (₹{i['price']:.2f})" for i in items)
            )

        uploaded = st.file_uploader(
            "Damage photo(s) — a real photo, no sample/demo photos are bundled with this project",
            type=["jpg", "jpeg", "png"], accept_multiple_files=True,
        )

        run_col1, run_col2 = st.columns([1, 4])
        submit_clicked = run_col1.button("Analyse & decide", type="primary")

        if submit_clicked:
            photos: list[tuple[str, bytes]] = [(f.name, f.read()) for f in uploaded] if uploaded else []

            if not photos:
                st.warning("Upload at least one real photo first.")
            else:
                with st.spinner("Running vision analysis and business rules..."):
                    result = submit_claim(selected_order_id, photos)

                decision_colour = {
                    "auto_approved": "green", "manual_review": "orange", "rejected": "red",
                }.get(result.decision, "gray")

                st.markdown(f"### Decision: :{decision_colour}[{result.decision.replace('_', ' ').title()}]")
                st.write(result.message)
                st.caption(
                    f"Claim ID: `{result.claim_id}`  ·  Order: `{result.order_id}`  ·  "
                    f"Reason code: `{result.reason}`"
                )

                if result.vision_report:
                    r = result.vision_report
                    m1, m2, m3, m4 = st.columns(4)
                    m1.metric("Product", r.get("product_name", "—"))
                    m2.metric("Category", r.get("product_category", "—"))
                    m3.metric("Damage", r.get("damage_type", "—"))
                    m4.metric("Confidence", f"{r.get('confidence', 0):.1f}%")
                    st.info(r.get("reasoning", ""))
                    with st.expander("Raw vision response (JSON)"):
                        st.json(r)

                if result.refund_amount is not None:
                    st.metric("Refund amount", f"₹{result.refund_amount:.2f}")

                if result.warnings:
                    st.warning(" · ".join(result.warnings))
                if result.error:
                    st.error(result.error)

# ---------------------------------------------------------------------
# Tab 2 — Claims table
# ---------------------------------------------------------------------
with tab_claims:
    st.subheader("All refund claims")
    rows = db.list_claims(limit=500)

    if not rows:
        st.info("No claims yet — submit one in the first tab.")
    else:
        df = pd.DataFrame(rows)

        f1, f2 = st.columns(2)
        with f1:
            decision_filter = st.multiselect(
                "Decision", options=sorted(df["decision"].dropna().unique()), default=[]
            )
        with f2:
            show_manual_review_only = st.checkbox("Manual-review queue only", value=False)

        filtered = df.copy()
        if decision_filter:
            filtered = filtered[filtered["decision"].isin(decision_filter)]
        if show_manual_review_only:
            filtered = filtered[filtered["decision"] == "manual_review"]

        display_df = filtered.copy()
        display_df["vision_confidence_pct"] = (display_df["vision_confidence"].fillna(0) * 100).round(1)

        st.dataframe(
            display_df[[
                "id", "order_id", "product_name", "damage_type",
                "vision_confidence_pct", "decision", "refund_amount", "created_at",
            ]],
            use_container_width=True,
            hide_index=True,
        )

        c1, c2, c3 = st.columns(3)
        c1.metric("Total claims", len(df))
        c2.metric("Auto-approved", int((df["decision"] == "auto_approved").sum()))
        c3.metric("In manual review", int((df["decision"] == "manual_review").sum()))

# ---------------------------------------------------------------------
# Tab 3 — Thresholds
# ---------------------------------------------------------------------
with tab_thresholds:
    st.subheader("Configurable confidence thresholds")
    st.write(
        "These drive every decision the rules engine makes and are read from the "
        "database at decision time — tighten them here during a fraud spike, no "
        "redeploy required."
    )

    current = db.get_active_thresholds()
    c1, c2 = st.columns(2)
    with c1:
        auto_approve_min = st.slider(
            "Auto-approve above (%)", min_value=50.0, max_value=100.0,
            value=float(current.auto_approve_min), step=0.5,
        )
    with c2:
        manual_review_min = st.slider(
            "Manual review from (%)", min_value=0.0, max_value=100.0,
            value=float(current.manual_review_min), step=0.5,
        )

    st.caption(
        f"Below **{manual_review_min:.1f}%** → rejected.  "
        f"**{manual_review_min:.1f}%–{auto_approve_min:.1f}%** → manual review.  "
        f"Above **{auto_approve_min:.1f}%** → auto-approved."
    )

    if st.button("Save thresholds"):
        if auto_approve_min <= manual_review_min:
            st.error("Auto-approve threshold must be greater than the manual-review threshold.")
        else:
            db.set_active_thresholds(auto_approve_min, manual_review_min, updated_by="dashboard_user")
            st.success("Thresholds updated — the rules engine will use these on the next claim.")

    st.divider()
    st.subheader("Other REF v4.1 policy rules (env-configured, not DB-editable)")
    st.write(
        "These come straight from the refund policy PDF and are env-var overridable "
        "(see `.env.example`), but — unlike the confidence thresholds above — they "
        "aren't business-as-usual tuning knobs, so they're not exposed for live editing here."
    )
    p1, p2, p3 = st.columns(3)
    p1.metric("Auto-approve refund cap", f"₹{settings.auto_approve_refund_cap:.0f}")
    p2.metric("Perishable window", f"{settings.perishable_window_hours:.0f}h")
    p3.metric("Packaged-goods window", f"{settings.packaged_window_hours:.0f}h")
    p4, p5 = st.columns(2)
    p4.metric("Fraud claim-count threshold", settings.fraud_claim_count_threshold)
    p5.metric("Fraud lookback window", f"{settings.fraud_lookback_days}d")
