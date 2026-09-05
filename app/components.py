import html
import pandas as pd
import streamlit as st

from core.analyst import analyze_financial_evidence


def _safe(value):
    return html.escape(str(value))

def status_label(status):
    return {"MATCHED": "✓ MATCHED", "EXPLAINED": "✓ EXPLAINED", "EXCEPTION": "⚠ EXCEPTION",}.get(status, status)


def action_for(status):
    return {"MATCHED": "Auto-close", "EXPLAINED": "Review explanation", "EXCEPTION": "Investigate",}.get(status, "Review")


def _section(title, caption=None):
    st.markdown(
        f'''<div class="section-title">{_safe(title)}</div>'''
        + (f'''<div class="section-caption">{_safe(caption)}</div>''' if caption else ""),
        unsafe_allow_html=True,
    )

def _subsection(title, caption=None):
    st.markdown(
        f'''<div class="subsection-title">{_safe(title)}</div>'''
        + (
            f'''<div class="subsection-caption">{_safe(caption)}</div>'''
            if caption else ""
        ),
        unsafe_allow_html=True,
    )

def _metric_card(label, value, css_class="", note=None):
    note_html = (
        f'<div class="metric-note">{_safe(note)}</div>'
        if note else ""
    )
    return (
        f'<div class="metric-card {css_class}">'
        f'<div class="metric-label">{_safe(label)}</div>'
        f'<div class="metric-value">{_safe(value)}</div>'
        f'{note_html}</div>'
    )


def render_hero():
    st.markdown(
        '''<div class="hero">
            <div class="hero-title">FiRecon — AI Finance Controller</div>
            <div class="hero-status">Evidence-backed payment reconciliation</div>
        </div>''',
        unsafe_allow_html=True,
    )


def render_summary(results, controller_throughput=None):
    total = len(results)
    counts = {
        status: sum(r["status"] == status for r in results)
        for status in ("MATCHED", "EXPLAINED", "EXCEPTION")
    }

    resolved = counts["MATCHED"] + counts["EXPLAINED"]
    resolution_rate = resolved / total * 100 if total else 0

    throughput_value = (
       f"{controller_throughput:.1f}/s"
        if total > 0 and controller_throughput is not None
        else "—"
    )
    throughput_note = "controller execution"

    metrics = [
        ("Payments Processed", total, "metric-green", None),
        ("Matched", counts["MATCHED"], "metric-green", None),
        ("Explained", counts["EXPLAINED"], "metric-amber", None),
        ("Resolved", f"{resolved} ({resolution_rate:.1f}%)", "metric-green", None),
        ("Exceptions", counts["EXCEPTION"], "metric-red", "needs investigation"),
        ("Throughput", throughput_value, "metric-green", throughput_note),
    ]

    cols = st.columns(6, gap="small")
    for col, (label, value, css_class, note) in zip(cols, metrics):
        with col:
            st.markdown(
                _metric_card(label, value, css_class, note),
                unsafe_allow_html=True,
            )



def render_exception_summary(results):
    exceptions = [
        result for result in results
        if result["status"] == "EXCEPTION"
    ]

    if not exceptions:
        st.markdown(
            '''<div class="mini-panel exception-panel exception-clear">
                <div class="exception-head">
                    <span class="exception-kicker">Exceptions</span>
                    <span class="exception-count">0 unresolved</span>
                </div>
                <div class="exception-clear-text">No unresolved exceptions in the processed batch.</div>
            </div>''',
            unsafe_allow_html=True,
        )
        return

    reason_counts = {}
    for result in exceptions:
        reason = result["reason"]
        reason_counts[reason] = reason_counts.get(reason, 0) + 1

    summary = " · ".join(
        f"{reason.replace('_', ' ').title()} ({count})"
        for reason, count in sorted(
            reason_counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )

    st.markdown(
        f'''<div class="mini-panel exception-panel">
            <div class="exception-head">
                <span class="exception-kicker">Exceptions</span>
                <span class="exception-count">{len(exceptions)} unresolved</span>
            </div>
            <div class="exception-summary-text">{_safe(summary)}</div>
        </div>''',
        unsafe_allow_html=True,
    )


def render_results_table(results):
    _section("Reconciliation Results", "High-level controller decisions across all captured payments.")
    st.dataframe(
        pd.DataFrame([{"Payment ID": r["payment_id"], "Status": r["status"], "Reason": r["reason"], "Action": action_for(r["status"]),} for r in results]),
        width="stretch",
        hide_index=True,
    )

def select_payment(results):
    _section("Investigate a Payment","Select a payment to inspect the complete financial evidence chain.",)

    if not results:
        st.info("Process a payment to begin investigation.")
        return None

    payment_ids = sorted(r["payment_id"] for r in results)
    selected_id = st.selectbox("Payment", payment_ids, index=None, placeholder="Select a payment…",label_visibility="collapsed", key="payment_selector",)

    if selected_id is None:
        return None

    return next(
        (r for r in results if r["payment_id"] == selected_id),
        None,
    )

def render_ai_analysis(selected):
    evidence = selected["evidence"]
    payment_id = selected["payment_id"]
    key = f"ai_analysis_{payment_id}"

    if selected["status"] == "MATCHED" and selected["reason"] == "EXACT_MATCH":
        st.info("Exact match confirmed by the deterministic controller. AI analysis is not needed.")
        return

    _subsection("AI Analysis", "Generate an AI-assisted explanation of the controller decision.",)

    with st.container(key="ai_generate_button"):
        generate_ai = st.button(
            "✦ Generate AI Analysis",
            type="primary",
            key=f"ai_button_{payment_id}",
        )

    if generate_ai:
        with st.spinner("Analyzing financial evidence…"):
            st.session_state[key] = analyze_financial_evidence(
                evidence=evidence,
                controller_status=selected["status"],
                controller_reason=selected["reason"],
            )

    if key not in st.session_state:
        return

    ai = st.session_state[key]

    _subsection("AI Analysis Result")

    st.markdown(
        f'''<div class="section-card">
            <div class="decision-title">Classification</div>
            <div class="decision-value">{_safe(ai["classification"])}</div>
            <div style="margin-top:12px;color:#475569;line-height:1.65;">
                {_safe(ai["explanation"])}
            </div>
        </div>''',
        unsafe_allow_html=True,
    )

    st.markdown(
        f'''<div class="section-card" style="margin-top:10px;">
            <div class="decision-title">Recommended Action</div>
            <div style="margin-top:8px;color:#334155;line-height:1.6;">
                {_safe(ai["recommended_action"])}
            </div>
        </div>''',
        unsafe_allow_html=True,
    )

    if ai.get("source") == "fallback":
        st.warning(
            "Gemini analysis was unavailable. "
            "The deterministic controller decision remains authoritative."
        )

def render_payment_summary(evidence, controller_status=None):
    st.markdown(
        '<div class="subsection-title">Payment Details</div>',
        unsafe_allow_html=True,
    )

    decision_css = "metric-green"
    if controller_status == "MATCHED":
        decision_css = "metric-green"
    elif controller_status == "EXPLAINED":
        decision_css = "metric-amber"
    elif controller_status == "EXCEPTION":
        decision_css = "metric-red"

    values = [
        ("Payment ID", evidence["payment_id"], "metric-green"),
        ("Amount", f"₹{evidence['payment_amount']}", "metric-green"),
        ("Currency", evidence["payment_currency"], "metric-green"),
        ("Payment Status", evidence["payment_status"], "metric-green"),
        ("Controller Decision", status_label(controller_status) if controller_status else "—", decision_css),
        ("Controller Action", action_for(controller_status) if controller_status else "—", "metric-green"),
    ]

    for col, (label, value, css_class) in zip(st.columns(6, gap="small"), values):
        with col:
            st.markdown(_metric_card(label, value, css_class), unsafe_allow_html=True,)

    st.caption(
        f"Order ID: {evidence['order_id']}    —     "
        f"Created: {evidence['payment_created_at']}"
    )


def render_financial_summary(evidence):
    settlements = evidence["settlement_evidence"]

    # Reconciliation values
    has_batch = any(s["is_batch_settlement"] for s in settlements)

    settlement_total = sum((s["settlement_amount"] for s in settlements), 0)

    bank_amount = (sum((s["bank_credit"] for s in settlements), 0) if has_batch else evidence["total_bank_credit"])

    recon_col, components_col = st.columns(2, gap="medium")

    # Financial Reconciliation
    with recon_col:
        _subsection("Financial Reconciliation",None)

        labels = (("Selected Payment", "Settlement Batch", "Bank Credit") if has_batch else ("Payment Amount", "Settlement Amount", "Bank Amount",))

        values = (
            f"₹{evidence['payment_amount']}",
            f"₹{settlement_total:.2f}",
            (f"₹{bank_amount:.2f}" if bank_amount is not None else "NOT FOUND"),
        )

        cols = st.columns([2.2, 0.55, 2.2, 0.55, 2.2], gap="small")

        for index, (label, value) in enumerate(zip(labels, values)):
            if index > 0:
                with cols[index * 2 - 1]:
                    st.markdown(
                        '<div class="flow-arrow">→</div>',
                        unsafe_allow_html=True,
                    )

            with cols[index * 2]:
                st.markdown(
                _metric_card(label, value),
                unsafe_allow_html=True,
            )

        if has_batch:
            st.caption(
                "Batch settlement: settlement and bank amounts "
                "represent the complete batch."
            )

    # Financial Components
    with components_col:
        _subsection("Financial Components", None)

        components = [
            ("Fees", evidence["total_fee"], "metric-red"),
            ("Tax", evidence["total_tax"], "metric-amber"),
            ("Refund", evidence["total_refund"], "metric-green"),
        ]

        cols = st.columns(3, gap="small")

        for col, (label, value, css_class) in zip(cols, components):
            with col:
                st.markdown(
                    _metric_card(
                        label,
                        f"₹{value}",
                        css_class,
                    ),
                    unsafe_allow_html=True,
                )

def render_duplicate_warning(evidence):
    if evidence["duplicate_detected"]:
        ids = ", ".join(map(str, evidence["duplicate_payment_ids"]))

        with st.container(key="duplicate_warning"):
            st.error(f"Duplicate payment detected. Related payment IDs: {ids}")


def _render_table(title, rows, empty_message=None):
    st.markdown(f"#### {_safe(title)}")
    if rows:
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    elif empty_message:
        st.info(empty_message)


def render_financial_trace(evidence):
    _subsection("Financial Trace", "Source-level evidence used by the controller decision.")
    settlements = evidence["settlement_evidence"]
    if not settlements:
        st.warning("No settlement transaction was found for this payment.")
        return

    for settlement in settlements:
        settlement_type = "BATCH" if settlement["is_batch_settlement"] else "DIRECT"
        bank_verified = bool(settlement.get("bank_integrity"))
        pill = '<span class="verified-pill">✓ BANK VERIFIED</span>' if bank_verified else '<span class="exception-pill">⚠ BANK EXCEPTION</span>'

        with st.expander(f"Settlement {settlement['settlement_id']}  —   {settlement_type}", expanded=False):
            st.markdown(
                f'''<div class="trace-card"><div class="trace-header">₹{settlement['settlement_amount']} · {_safe(settlement['settlement_status'])} · {pill}</div>
                <div class="trace-meta">UTR: {_safe(settlement['utr'])} · Created: {_safe(settlement['settlement_created_at'])}</div></div>''',
                unsafe_allow_html=True,
            )

            c1, c2, c3 = st.columns(3)
            c1.metric("Settlement Amount", f"₹{settlement['settlement_amount']}")
            c2.metric("Status", settlement["settlement_status"])
            c3.metric("UTR", settlement["utr"] or "—")
            st.caption(f"Created: {settlement['settlement_created_at']}")

            if settlement["is_batch_settlement"]:
                _render_table(
                    "Batch Composition",
                    [
                        {
                            "Payment ID": item["payment_id"],
                            "Payment Amount": f"₹{item['amount']}",
                            "Settlement Credit": f"₹{item['credit']}",
                            "Fee": f"₹{item['fee']}",
                            "Tax": f"₹{item['tax']}",
                            "Status": item["status"],
                        }
                        for item in settlement.get("batch_payments", [])
                    ],
                    "Batch composition unavailable.",
                )
                if settlement.get("batch_payments"):
                    st.caption(f"{settlement['batch_payment_count']} payments included in this settlement.")

            _render_table(
                "Settlement Transactions",
                [
                    {
                        "Txn ID": txn["id"],
                        "Payment ID": txn["payment_id"],
                        "Type": txn["type"],
                        "Credit": f"₹{txn['credit']}",
                        "Fee": f"₹{txn['fee']}",
                        "Tax": f"₹{txn['tax']}",
                        "Posted": txn["posted_at"],
                        "Settled": txn["settled_at"],
                        "Description": txn["description"],
                    }
                    for txn in settlement.get("settlement_transactions", [])
                ],
                "No settlement transactions found.",
            )

            bank_rows = [
                {
                    "Bank Txn ID": bank["id"],
                    "Amount": f"₹{bank['amount']}",
                    "Currency": bank["currency"],
                    "Type": bank["transaction_type"],
                    "Date": bank["transaction_date"],
                    "UTR": bank["utr"],
                    "Description": bank["description"],
                }
                for bank in settlement.get("bank_transactions", [])
            ]
            _render_table("Bank Transactions", bank_rows, "No corresponding bank transaction was found.")

    # Refund Evidence
    refunds = evidence.get("refunds", [])

    if refunds:
        with st.expander("Refund Evidence"):
            st.dataframe(
                pd.DataFrame([
                    {
                        "Refund ID": r["id"],
                        "Amount": f"₹{r['amount']}",
                        "Currency": r["currency"],
                        "Status": r["status"],
                        "Created": r["created_at"],
                    }
                    for r in refunds
                ]),
                width="stretch",
                hide_index=True,
            )

def render_audit_trail(evidence):
    with st.expander("Audit Trail"):
        st.code(f"Payment {evidence['payment_id']} → Settlement → Settlement Transactions → UTR → Bank Transaction")
