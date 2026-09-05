import sys
from pathlib import Path
import random
import time
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from finance_controller import get_captured_payment_ids, run_controller
from components import (
    render_ai_analysis,
    render_audit_trail,
    render_duplicate_warning,
    render_exception_summary,
    render_financial_summary,
    render_financial_trace,
    render_hero,
    render_payment_summary,
    render_results_table,
    render_summary,
    select_payment,
)
from styles import apply_styles


st.set_page_config(
    page_title="FiRecon — AI Finance Controller",
    page_icon=" ",
    layout="wide",
    initial_sidebar_state="collapsed",
)

apply_styles()

@st.cache_data(ttl=30)
def load_payment_ids():
    return get_captured_payment_ids()


render_hero()
all_payment_ids = load_payment_ids()

if ("payment_order" not in st.session_state or set(st.session_state.payment_order) != set(all_payment_ids)):
    st.session_state.payment_order = list(all_payment_ids)
    random.Random(42).shuffle(st.session_state.payment_order)
    st.session_state.processed_count = 0
    st.session_state.processed_results = []
    st.session_state.processing_seconds = 0.0

if "processed_count" not in st.session_state:
    st.session_state.processed_count = 0

if "processed_results" not in st.session_state:
    st.session_state.processed_results = []

if "processing_seconds" not in st.session_state:
    st.session_state.processing_seconds = 0.0

with st.container(border=True):
    st.markdown(
        f"""<div class=\"processing-header\">
            <div class=\"processing-title\">Live Payment Processing</div>
            <div class=\"processing-count\">{st.session_state.processed_count} / {len(all_payment_ids)} processed</div>
        </div>""",
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("▶ Process Next Payment", width="stretch"):
            if st.session_state.processed_count < len(all_payment_ids):
                payment_id = st.session_state.payment_order[
                    st.session_state.processed_count
                ]

                start = time.perf_counter()
                new_results = run_controller([payment_id])
                elapsed = max(time.perf_counter() - start, 1e-9)

                if new_results:
                    st.session_state.processed_results.append(new_results[0])
                    st.session_state.processed_count += 1
                    st.session_state.processing_seconds += elapsed

                st.rerun()

    with col2:
        if st.button("⚡ Process All Payments", width="stretch"):
            remaining_ids = st.session_state.payment_order[
                st.session_state.processed_count:
            ]

            if remaining_ids:
                start = time.perf_counter()
                new_results = run_controller(remaining_ids)
                elapsed = max(time.perf_counter() - start, 1e-9)

                by_id = {result["payment_id"]: result for result in new_results}
                for payment_id in remaining_ids:
                    result = by_id.get(payment_id)
                    if result is not None:
                        st.session_state.processed_results.append(result)

                st.session_state.processed_count = len(all_payment_ids)
                st.session_state.processing_seconds += elapsed

            st.rerun()

results = st.session_state.processed_results
controller_throughput = (
    st.session_state.processed_count / st.session_state.processing_seconds
    if st.session_state.processing_seconds > 0
    else None
)
render_summary(results, controller_throughput)

render_exception_summary(results)

render_results_table(results)
if results:
    selected = select_payment(results)

    if selected is not None:
        evidence = selected["evidence"]
        render_payment_summary(evidence, selected["status"])
        render_financial_summary(evidence)
        render_duplicate_warning(evidence)
        render_ai_analysis(selected)
        render_financial_trace(evidence)
        render_audit_trail(evidence)
else:
    st.info("No payments processed yet. Click **▶ Process Next Payment** to begin.")

