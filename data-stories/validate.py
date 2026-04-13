import os
import sys
import pandas as pd
import plotly.express as px
import streamlit as st

sys.path.insert(0, os.path.dirname(__file__))
from config import CASE_STUDIES

st.set_page_config(
    page_title="Data Stories",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Hamburger toggle button */
    [data-testid="collapsedControl"] {
        top: 1.2rem;
        background: #ffffff;
        border: 1px solid #d9d9d9;
        border-radius: 6px;
        width: 2.4rem;
        height: 2.4rem;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    }
    [data-testid="collapsedControl"] svg { display: none; }
    [data-testid="collapsedControl"]::after {
        content: "☰";
        font-size: 1.25rem;
        color: #444;
        line-height: 1;
    }

    /* Sidebar panel */
    [data-testid="stSidebar"] {
        background: #1a1a2e;
        padding-top: 1rem;
    }
    [data-testid="stSidebar"] * { color: #e8e8f0 !important; }

    /* Nav buttons */
    [data-testid="stSidebar"] .stButton > button {
        width: 100%;
        text-align: left;
        background: transparent;
        border: none;
        border-radius: 6px;
        padding: 0.55rem 1rem;
        font-size: 0.95rem;
        font-weight: 500;
        color: #c8c8dd !important;
        transition: background 0.15s;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(255,255,255,0.08) !important;
        color: #ffffff !important;
    }

    /* Active nav button */
    [data-testid="stSidebar"] .stButton > button:focus {
        background: rgba(255,140,0,0.25) !important;
        color: #ffaa44 !important;
        box-shadow: none;
    }

    /* Sidebar divider */
    [data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.12) !important; }

    /* Sidebar selectbox label */
    [data-testid="stSidebar"] label { color: #aaaacc !important; font-size: 0.8rem !important; }

    /* Main content top padding */
    .block-container { padding-top: 2rem; }

    /* Home nav card buttons — full-rectangle clickable cards */
    [data-testid="stHorizontalBlock"] [data-testid="stButton"] > button {
        background: #ffffff !important;
        border: 1px solid #e8e8e8 !important;
        border-radius: 10px !important;
        padding: 1.5rem 1.75rem !important;
        text-align: left !important;
        white-space: pre-wrap !important;
        height: auto !important;
        min-height: 110px !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05) !important;
        font-size: 0.9rem !important;
        color: #333 !important;
        line-height: 1.55 !important;
        transition: box-shadow 0.2s, border-color 0.2s !important;
    }
    [data-testid="stHorizontalBlock"] [data-testid="stButton"] > button:hover {
        box-shadow: 0 4px 16px rgba(0,0,0,0.10) !important;
        border-color: #c8c8c8 !important;
        background: #fafafa !important;
        color: #111 !important;
    }
    [data-testid="stHorizontalBlock"] [data-testid="stButton"] > button p {
        font-size: inherit !important;
        text-align: left !important;
    }
</style>
""", unsafe_allow_html=True)

# ── Session state ─────────────────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state.page = "home"

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Data Stories")
    st.markdown("---")

    if st.button("🏠  Home"):
        st.session_state.page = "home"
        st.rerun()
    if st.button("🗂  Data Review"):
        st.session_state.page = "data_review"
        st.rerun()
    if st.button("🗺  Map View"):
        st.session_state.page = "map_view"
        st.rerun()

    st.markdown("---")
    study_titles = [s["title"] for s in CASE_STUDIES]
    selected_title = st.selectbox("Case study", study_titles)
    selected_study = next(s for s in CASE_STUDIES if s["title"] == selected_title)
    study_id = selected_study["id"]


# ── Helpers ───────────────────────────────────────────────────────────────────
@st.cache_data
def load_csv(path):
    return pd.read_csv(path)


def data_path(sid, tier, filename):
    return os.path.join(os.path.dirname(__file__), "case-studies", sid, "data", tier, filename)


def list_files(sid, tier):
    folder = os.path.join(os.path.dirname(__file__), "case-studies", sid, "data", tier)
    return sorted(f for f in os.listdir(folder) if f.endswith((".csv", ".json")))


# ── Pages ─────────────────────────────────────────────────────────────────────

def page_home():
    st.title("Data Stories")
    st.markdown(
        "A library of case studies built on mock data — each one telling a business story "
        "through interactive charts and analysis. Use the **☰ menu** to navigate."
    )
    st.markdown("---")

    col1, col2 = st.columns(2, gap="large")
    with col1:
        if st.button(
            "🗂 Data Review\n\nInspect raw and processed sample data tables for the "
            "selected case study. Sort, filter nulls, review data types, and validate "
            "mock data quality.",
            key="home_data_review",
            use_container_width=True,
        ):
            st.session_state.page = "data_review"
            st.rerun()
    with col2:
        if st.button(
            "🗺 Map View\n\nGeographic view of all accounts on a US map. Points are "
            "color-shaded from gray (low revenue) to orange (high revenue), with "
            "hover details.",
            key="home_map_view",
            use_container_width=True,
        ):
            st.session_state.page = "map_view"
            st.rerun()

    st.markdown("#### Available Case Studies")
    for s in CASE_STUDIES:
        st.markdown(f"- **{s['title']}** — {s['description']}")


def page_data_review(sid):
    st.title("Data Review")
    st.caption(f"Case study: {selected_study['title']}")

    tier = st.radio("Data tier", ["raw", "processed"], horizontal=True)
    files = list_files(sid, tier)

    if not files:
        st.info(f"No files found in `case-studies/{sid}/data/{tier}/`")
        return

    chosen = st.selectbox("File", files)
    df = load_csv(data_path(sid, tier, chosen))

    all_cols = df.columns.tolist()
    sort_col = st.selectbox(
        "Sort by",
        ["(none)"] + all_cols,
        index=all_cols.index("annual_revenue") + 1 if "annual_revenue" in all_cols else 0,
    )
    sort_asc = st.radio("Order", ["Descending", "Ascending"], horizontal=True) == "Ascending"

    if sort_col != "(none)":
        df = df.sort_values(sort_col, ascending=sort_asc)

    c1, c2, c3 = st.columns(3)
    c1.metric("Rows", f"{len(df):,}")
    c2.metric("Columns", len(df.columns))
    c3.metric("File", chosen)

    st.markdown("---")
    st.subheader("Data Table")
    st.dataframe(df, use_container_width=True, hide_index=True)

    with st.expander("Schema (data types)"):
        st.dataframe(df.dtypes.rename("dtype").to_frame(), use_container_width=True)

    with st.expander("Null counts per column"):
        nulls = df.isnull().sum().rename("null_count").to_frame()
        nulls["pct_null"] = (nulls["null_count"] / len(df) * 100).round(1).astype(str) + "%"
        st.dataframe(nulls, use_container_width=True)

    numeric_cols = df.select_dtypes("number").columns.tolist()
    with st.expander("Numeric summary"):
        if numeric_cols:
            st.dataframe(df[numeric_cols].describe().T, use_container_width=True)
        else:
            st.info("No numeric columns.")

    if "industry" in df.columns:
        with st.expander("Industry breakdown"):
            count_col = "account_id" if "account_id" in df.columns else df.columns[0]
            breakdown = (
                df.groupby("industry")[count_col]
                .count()
                .rename("count")
                .reset_index()
                .sort_values("count", ascending=False)
            )
            st.dataframe(breakdown, use_container_width=True, hide_index=True)


def page_map_view(sid):
    st.title("Map View")
    st.caption(f"Case study: {selected_study['title']} — accounts by annual revenue")

    files = list_files(sid, "raw")
    acct_files = [f for f in files if "account" in f.lower()]
    if not acct_files:
        st.info("No accounts file found in raw data.")
        return

    df = load_csv(data_path(sid, "raw", acct_files[0]))

    required = {"latitude", "longitude", "annual_revenue", "account_name"}
    if not required.issubset(df.columns):
        st.error(f"Accounts file is missing columns: {required - set(df.columns)}")
        return

    df = df.dropna(subset=["latitude", "longitude", "annual_revenue"])

    # Revenue display label
    df["revenue_label"] = df["annual_revenue"].apply(
        lambda v: f"${v/1_000_000:.1f}M" if v < 1_000_000_000 else f"${v/1_000_000_000:.2f}B"
    )

    fig = px.scatter_mapbox(
        df,
        lat="latitude",
        lon="longitude",
        color="annual_revenue",
        color_continuous_scale=[[0, "#ABABAB"], [0.4, "#E07020"], [1, "#FF5500"]],
        size="annual_revenue",
        size_max=18,
        zoom=3.4,
        center={"lat": 38.5, "lon": -96.5},
        mapbox_style="carto-positron",
        hover_name="account_name",
        custom_data=[
            "street_address", "city", "state",
            "latitude", "longitude", "revenue_label", "industry",
        ],
    )

    fig.update_traces(
        hovertemplate=(
            "<b>%{hovertext}</b><br>"
            "<span style='color:#888'>%{customdata[6]}</span><br><br>"
            "📍 %{customdata[0]}<br>"
            "    %{customdata[1]}, %{customdata[2]}<br>"
            "    Lat %{customdata[3]:.4f}, Lon %{customdata[4]:.4f}<br><br>"
            "💰 %{customdata[5]}<extra></extra>"
        ),
        marker_opacity=0.85,
    )

    fig.update_layout(
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        height=680,
        coloraxis_colorbar=dict(
            title="Annual Revenue",
            tickprefix="$",
            tickformat=".2s",
            len=0.5,
            thickness=14,
            bgcolor="rgba(255,255,255,0.85)",
            borderwidth=0,
        ),
    )

    st.plotly_chart(fig, use_container_width=True)

    # Summary strip below map
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Accounts", f"{len(df):,}")
    c2.metric("Highest Revenue", df["revenue_label"][df["annual_revenue"].idxmax()])
    c3.metric("Median Revenue",
              f"${df['annual_revenue'].median()/1_000_000:.1f}M")
    c4.metric("Industries", df["industry"].nunique() if "industry" in df.columns else "—")


# ── Router ────────────────────────────────────────────────────────────────────
page = st.session_state.page

if page == "home":
    page_home()
elif page == "data_review":
    page_data_review(study_id)
elif page == "map_view":
    page_map_view(study_id)
else:
    page_home()
