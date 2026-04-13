import importlib
import streamlit as st
from config import CASE_STUDIES

st.set_page_config(page_title="Data Stories", layout="wide")

# ── Sidebar: case study selector ─────────────────────────────────────────────
st.sidebar.title("Data Stories")
study_titles = [s["title"] for s in CASE_STUDIES]
selection = st.sidebar.radio("Choose a case study", study_titles)

selected = next(s for s in CASE_STUDIES if s["title"] == selection)
st.sidebar.markdown(f"_{selected['description']}_")

# ── Load the selected case study's config ────────────────────────────────────
study_id = selected["id"]
study_config = importlib.import_module(f"case-studies.{study_id}.config".replace("-", "_"))

if not study_config.SLIDE_ORDER:
    st.title(selected["title"])
    st.info("No slides have been added to this case study yet.")
    st.stop()

# ── Slide navigation via session state ───────────────────────────────────────
if "slide_index" not in st.session_state or st.session_state.get("active_study") != study_id:
    st.session_state.slide_index = 0
    st.session_state.active_study = study_id

total = len(study_config.SLIDE_ORDER)
idx = st.session_state.slide_index

col_prev, col_counter, col_next = st.columns([1, 2, 1])
with col_prev:
    if st.button("← Previous", disabled=(idx == 0)):
        st.session_state.slide_index -= 1
        st.rerun()
with col_counter:
    st.markdown(f"<div style='text-align:center'>Slide {idx + 1} of {total}</div>", unsafe_allow_html=True)
with col_next:
    if st.button("Next →", disabled=(idx == total - 1)):
        st.session_state.slide_index += 1
        st.rerun()

# ── Render the active slide ───────────────────────────────────────────────────
slide_module_path = (
    f"case_studies.{study_id.replace('-', '_')}.slides.{study_config.SLIDE_ORDER[idx]}"
)
slide = importlib.import_module(slide_module_path)
slide.render()
