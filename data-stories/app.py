import os
import sys
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
    if st.button("📈  Pipeline History"):
        st.session_state.page = "pipeline_history"
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


@st.cache_data(show_spinner=False)
def load_monthly_pipeline_from_csv(sid):
    """
    Load pre-computed pipeline data from OppFieldHist_Pivot.csv (SQL output).
    Returns a DataFrame with columns: month, industry, weighted_amount.
    """
    pivot = load_csv(data_path(sid, "processed", "OppFieldHist_Pivot.csv"))
    acct  = load_csv(data_path(sid, "raw", "accounts.csv"))

    pivot["month"] = pd.to_datetime(pivot["MONTH_START"])
    pivot = pivot.merge(acct[["account_id", "industry"]], left_on="ACCOUNT_ID", right_on="account_id", how="left")

    return (
        pivot.groupby(["month", "industry"])["ENDING_WEIGHTED_AMOUNT"]
        .sum()
        .reset_index()
        .rename(columns={"ENDING_WEIGHTED_AMOUNT": "weighted_amount"})
    )


@st.cache_data(show_spinner=False)
def compute_monthly_pipeline(sid):
    """
    Replicate the opportunity_monthly_snapshot SQL logic in Python.
    Returns a DataFrame with columns: month, industry, weighted_amount.
    """
    acct = load_csv(data_path(sid, "raw", "accounts.csv"))
    opps = load_csv(data_path(sid, "raw", "opportunities.csv"))
    hist = load_csv(data_path(sid, "raw", "opportunity_field_history.csv"))

    TODAY = pd.Timestamp("2026-04-12")

    STAGE_PROB = {
        "1 - Prospecting": 10, "2 - Scoping": 15, "3 - Engaged": 25,
        "4 - Proposal": 60,    "5 - Negotiation": 80,
        "6 - Closed Won": 100, "7 - Closed Lost": 0,
    }

    # Parse dates
    opps["created_date"] = pd.to_datetime(opps["created_date"])
    opps["close_date"]   = pd.to_datetime(opps["close_date"])
    hist["created_date"] = pd.to_datetime(hist["created_date"])

    # Active end: closed deals use close_date; open deals use TODAY
    opps["active_end"] = opps["close_date"].where(
        opps["status"].isin(["Won", "Lost"]), other=TODAY
    )

    # Month boundaries (first of month)
    opps["opp_month_start"] = opps["created_date"].dt.to_period("M").dt.to_timestamp()
    opps["opp_month_end"]   = opps["active_end"].dt.to_period("M").dt.to_timestamp()

    # Cross-join opportunities with all calendar months, then filter to active range
    all_months = pd.date_range("2021-01-01", "2026-04-01", freq="MS")
    months_df = pd.DataFrame({"month_start": all_months, "_key": 1})
    opps_slim = opps[["opportunity_id", "account_id",
                       "opp_month_start", "opp_month_end"]].copy()
    opps_slim["_key"] = 1

    spine = opps_slim.merge(months_df, on="_key").drop(columns="_key")
    spine = spine[
        (spine["month_start"] >= spine["opp_month_start"]) &
        (spine["month_start"] <= spine["opp_month_end"])
    ].copy()

    # ── Initial values (creation records: old_value is NaN) ──────────────────
    is_creation = hist["old_value"].isna() | (hist["old_value"] == "")
    initial = (
        hist[is_creation][["opportunity_id", "field", "new_value"]]
        .pivot(index="opportunity_id", columns="field", values="new_value")
        .rename(columns={"StageName": "init_stage",
                         "CloseDate": "init_close",
                         "Amount":    "init_amount"})
        .reset_index()
    )
    initial.columns.name = None

    # ── Post-creation changes: last change per (opp, field, month) ────────────
    changes = hist[~is_creation].copy()
    changes["change_month"] = changes["created_date"].dt.to_period("M").dt.to_timestamp()

    latest_chg = (
        changes.sort_values("created_date")
        .groupby(["opportunity_id", "field", "change_month"])["new_value"]
        .last()
        .reset_index()
        .pivot_table(
            index=["opportunity_id", "change_month"],
            columns="field",
            values="new_value",
            aggfunc="last",
        )
        .rename(columns={"StageName": "chg_stage",
                         "CloseDate": "chg_close",
                         "Amount":    "chg_amount"})
        .reset_index()
    )
    latest_chg.columns.name = None

    # ── Join initial + changes to spine ───────────────────────────────────────
    spine = spine.merge(initial, on="opportunity_id", how="left")
    spine = spine.merge(
        latest_chg,
        left_on=["opportunity_id", "month_start"],
        right_on=["opportunity_id", "change_month"],
        how="left",
    )

    # ── Carry forward: ffill within each opp, fallback to initial value ───────
    spine = spine.sort_values(["opportunity_id", "month_start"])
    for chg_col, init_col, end_col in [
        ("chg_stage",  "init_stage",  "ending_stage"),
        ("chg_amount", "init_amount", "ending_amount"),
    ]:
        spine[end_col] = (
            spine.groupby("opportunity_id")[chg_col]
            .transform("ffill")
            .fillna(spine[init_col])
        )

    # ── Compute weighted amount ───────────────────────────────────────────────
    spine["ending_amount"] = pd.to_numeric(spine["ending_amount"], errors="coerce").fillna(0)
    spine["ending_prob"]   = spine["ending_stage"].map(STAGE_PROB).fillna(0)
    spine["weighted_amount"] = spine["ending_amount"] * spine["ending_prob"] / 100.0

    # ── Join industry from accounts ───────────────────────────────────────────
    spine = spine.merge(acct[["account_id", "industry"]], on="account_id", how="left")

    # ── Aggregate by month + industry ────────────────────────────────────────
    agg = (
        spine.groupby(["month_start", "industry"])["weighted_amount"]
        .sum()
        .reset_index()
        .rename(columns={"month_start": "month"})
    )
    return agg


@st.cache_data(show_spinner=False)
def load_us_states_geojson():
    """
    Fetch US state boundaries GeoJSON from Natural Earth data hosted on
    GitHub (nvkelso/natural-earth-vector).  Cached for the session so it
    is only downloaded once.
    """
    import json, urllib.request
    url = (
        "https://raw.githubusercontent.com/nvkelso/natural-earth-vector"
        "/master/geojson/ne_10m_admin_1_states_provinces_lakes.geojson"
    )
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            data = json.loads(r.read().decode())
        # Keep only US features to stay lightweight
        data["features"] = [
            f for f in data["features"]
            if f.get("properties", {}).get("iso_a2") == "US"
        ]
        return data
    except Exception:
        return None


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

    col1, col2, col3 = st.columns(3, gap="large")
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
    with col3:
        if st.button(
            "📈 Pipeline History\n\nMonthly ending weighted pipeline by industry. "
            "Tracks how opportunity stage and amount changes flow through the "
            "forecast over time.",
            key="home_pipeline_history",
            use_container_width=True,
        ):
            st.session_state.page = "pipeline_history"
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

    # ── Header + metric selector ──────────────────────────────────────────────
    col_title, col_metric = st.columns([3, 1])
    with col_title:
        st.title("Map View")
        st.caption(f"Case study: {selected_study['title']}")
    with col_metric:
        st.markdown("<br>", unsafe_allow_html=True)   # nudge selector down
        metric_choice = st.selectbox(
            "Color & size metric",
            options=[
                "Company Annual Revenue",
                "Employee Headcount",
                "Annual Revenue per Employee",
                "All Opportunity Amounts",
                "Won Opportunity Amounts",
                "Open Opportunity Amounts",
            ],
            key="map_metric",
        )

    # ── Load accounts ─────────────────────────────────────────────────────────
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
    df = df.dropna(subset=["latitude", "longitude"])

    # ── Join opportunity aggregates ───────────────────────────────────────────
    opp_files = [f for f in files
                 if "opportunit" in f.lower() and "history" not in f.lower()]
    if opp_files:
        df_opp = load_csv(data_path(sid, "raw", opp_files[0]))
        for col, filt in [
            ("total_opp_amount", None),
            ("won_opp_amount",   df_opp["status"] == "Won"),
            ("open_opp_amount",  df_opp["status"] == "Open"),
        ]:
            sub = df_opp if filt is None else df_opp[filt]
            agg = sub.groupby("account_id")["amount"].sum().rename(col)
            df  = df.merge(agg, on="account_id", how="left")
        df[["total_opp_amount", "won_opp_amount", "open_opp_amount"]] = (
            df[["total_opp_amount", "won_opp_amount", "open_opp_amount"]].fillna(0)
        )
    else:
        df["total_opp_amount"] = df["won_opp_amount"] = df["open_opp_amount"] = 0

    # ── Metric config ─────────────────────────────────────────────────────────
    METRICS = {
        "Company Annual Revenue":      ("annual_revenue",              "Annual Revenue",        "dollar"),
        "Employee Headcount":          ("number_of_employees",         "Employee Headcount",    "count"),
        "Annual Revenue per Employee": ("annual_revenue_per_employee", "Revenue / Employee",    "dollar"),
        "All Opportunity Amounts":     ("total_opp_amount",            "All Opportunity $",     "dollar"),
        "Won Opportunity Amounts":     ("won_opp_amount",              "Won Opportunity $",     "dollar"),
        "Open Opportunity Amounts":    ("open_opp_amount",             "Open Opportunity $",    "dollar"),
    }
    metric_col, metric_title, metric_fmt = METRICS[metric_choice]

    df = df.dropna(subset=[metric_col])

    # ── Value formatter ───────────────────────────────────────────────────────
    def fmt_val(v):
        if metric_fmt == "count":
            return f"{int(v):,}"
        if v >= 1_000_000_000:
            return f"${v/1_000_000_000:.2f}B"
        if v >= 1_000_000:
            return f"${v/1_000_000:.1f}M"
        if v >= 1_000:
            return f"${v/1_000:.0f}K"
        return f"${v:,.0f}"

    df["metric_display"] = df[metric_col].apply(fmt_val)

    # ── Colorbar ticks ────────────────────────────────────────────────────────
    max_val = df[metric_col].max() or 1
    if metric_fmt == "count":
        step = max(1_000, round(max_val / 5 / 1_000) * 1_000)
        cb_vals = list(range(0, int(max_val) + step, step))
        cb_text = [f"{int(v/1_000)}K" if v >= 1_000 else str(int(v)) for v in cb_vals]
    elif max_val >= 1e9:
        max_b  = int(max_val / 1e9) + 1
        step_b = max(1, max_b // 5)
        cb_vals = [b * 1e9 for b in range(0, max_b + 1, step_b)]
        cb_text = ["$0" if v == 0 else f"${int(v/1e9)}B" for v in cb_vals]
    else:
        max_m  = int(max_val / 1e6) + 1
        step_m = max(1, max_m // 5)
        cb_vals = [m * 1e6 for m in range(0, max_m + 1, step_m)]
        cb_text = ["$0" if v == 0 else f"${int(v/1e6)}M" for v in cb_vals]

    # ── Build map ─────────────────────────────────────────────────────────────
    us_states = load_us_states_geojson()

    fig = px.scatter_mapbox(
        df,
        lat="latitude",
        lon="longitude",
        color=metric_col,
        color_continuous_scale=[[0, "#ABABAB"], [0.4, "#E07020"], [1, "#FF5500"]],
        size=metric_col,
        size_max=18,
        zoom=3.4,
        center={"lat": 38.5, "lon": -96.5},
        mapbox_style="white-bg",
        hover_name="account_name",
        custom_data=[
            "street_address", "city", "state",
            "latitude", "longitude", "metric_display", "industry",
        ],
    )

    layers = [
        {
            "below": "traces",
            "sourcetype": "raster",
            "sourceattribution": (
                '&copy; <a href="https://www.openstreetmap.org/copyright">'
                "OpenStreetMap</a> contributors &copy; "
                '<a href="https://carto.com/attributions">CARTO</a>'
            ),
            "source": [
                "https://a.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}.png",
                "https://b.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}.png",
                "https://c.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}.png",
                "https://d.basemaps.cartocdn.com/light_nolabels/{z}/{x}/{y}.png",
            ],
        },
    ]
    if us_states:
        layers.append({
            "below": "traces", "sourcetype": "geojson",
            "source": us_states, "type": "line",
            "color": "#c0c0c0", "line": {"width": 1.2},
        })
    fig.update_layout(mapbox_layers=layers)

    fig.update_traces(
        hovertemplate=(
            "<b>%{hovertext}</b><br>"
            "<span style='color:#888'>%{customdata[6]}</span><br><br>"
            "📍 %{customdata[0]}<br>"
            "    %{customdata[1]}, %{customdata[2]}<br>"
            "    Lat %{customdata[3]:.4f}, Lon %{customdata[4]:.4f}<br><br>"
            f"{'👥' if metric_fmt == 'count' else '💰'} "
            f"{metric_title}: %{{customdata[5]}}<extra></extra>"
        ),
        marker_opacity=0.85,
    )

    fig.update_layout(
        margin={"l": 0, "r": 0, "t": 0, "b": 0},
        height=660,
        coloraxis_colorbar=dict(
            title=metric_title,
            tickvals=cb_vals,
            ticktext=cb_text,
            len=0.5,
            thickness=14,
            bgcolor="rgba(255,255,255,0.85)",
            borderwidth=0,
        ),
    )

    st.plotly_chart(fig, use_container_width=True)

    # ── Summary strip ─────────────────────────────────────────────────────────
    st.markdown("---")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Accounts", f"{len(df):,}")
    c2.metric(f"Highest {metric_title}",
              df["metric_display"].iloc[df[metric_col].values.argmax()])
    c3.metric(f"Median {metric_title}", fmt_val(df[metric_col].median()))
    c4.metric("Industries",
              df["industry"].nunique() if "industry" in df.columns else "—")


def page_pipeline_history(sid):

    st.title("Opportunity Pipeline History")
    st.caption(f"Case study: {selected_study['title']}")
    st.markdown(
        "Monthly **ending weighted pipeline** per industry — each opportunity's "
        "closing amount multiplied by its stage probability, summed by month."
    )

    source = st.radio("Data source", ["Python", "SQL"], horizontal=True, key="pipeline_source")

    if source == "SQL":
        df = load_monthly_pipeline_from_csv(sid)
    else:
        with st.spinner("Computing monthly pipeline…"):
            df = compute_monthly_pipeline(sid)

    if df.empty:
        st.info("No pipeline data available.")
        return

    # ── Industry colour palette (consistent ordering) ─────────────────────────
    industries = sorted(df["industry"].dropna().unique())
    palette = px.colors.qualitative.Set2
    colour_map = {ind: palette[i % len(palette)] for i, ind in enumerate(industries)}

    # ── Line chart ────────────────────────────────────────────────────────────
    fig = go.Figure()

    for ind in industries:
        sub = df[df["industry"] == ind].sort_values("month")
        fig.add_trace(go.Scatter(
            x=sub["month"],
            y=sub["weighted_amount"],
            mode="lines",
            name=ind,
            line=dict(color=colour_map[ind], width=2.5),
            hovertemplate=(
                f"<b>{ind}</b><br>"
                "%{x|%b %Y}<br>"
                "Weighted pipeline: $%{y:,.0f}<extra></extra>"
            ),
        ))

    # Total line (dashed, secondary)
    total = df.groupby("month")["weighted_amount"].sum().reset_index()
    fig.add_trace(go.Scatter(
        x=total["month"],
        y=total["weighted_amount"],
        mode="lines",
        name="All Industries",
        line=dict(color="#333333", width=1.5, dash="dot"),
        hovertemplate=(
            "<b>All Industries</b><br>"
            "%{x|%b %Y}<br>"
            "Weighted pipeline: $%{y:,.0f}<extra></extra>"
        ),
    ))

    # Y-axis tick formatter — pick B or M scale
    max_val = total["weighted_amount"].max()
    if max_val >= 1e9:
        ytick_vals = [i * 1e9 for i in range(0, int(max_val / 1e9) + 2)]
        ytick_text = [f"${int(v/1e9)}B" for v in ytick_vals]
    else:
        step_m = max(1, int(max_val / 1e6 / 5))
        ytick_vals = [i * step_m * 1e6 for i in range(0, int(max_val / (step_m * 1e6)) + 2)]
        ytick_text = [f"${int(v/1e6)}M" for v in ytick_vals]

    fig.update_layout(
        height=520,
        margin={"l": 0, "r": 0, "t": 20, "b": 0},
        hovermode="x unified",
        legend=dict(
            title="Industry",
            orientation="v",
            x=1.01, y=1,
            xanchor="left",
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="#e0e0e0",
            borderwidth=1,
        ),
        xaxis=dict(
            title="Month",
            tickformat="%b %Y",
            showgrid=False,
        ),
        yaxis=dict(
            title="Weighted Pipeline",
            tickvals=ytick_vals,
            ticktext=ytick_text,
            showgrid=True,
            gridcolor="#f0f0f0",
        ),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )

    st.plotly_chart(fig, use_container_width=True)

    # ── Summary strip ─────────────────────────────────────────────────────────
    st.markdown("---")
    latest_month = df["month"].max()
    total_by_month = total.set_index("month")["weighted_amount"]

    latest_total  = total_by_month.get(latest_month, 0)
    peak_month    = total_by_month.idxmax()
    peak_val      = total_by_month.max()
    top_industry  = (
        df.groupby("industry")["weighted_amount"].sum().idxmax()
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Latest Month Total",
              f"${latest_total/1e6:.1f}M" if latest_total < 1e9 else f"${latest_total/1e9:.2f}B")
    c2.metric("Peak Month", peak_month.strftime("%b %Y"))
    c3.metric("Peak Pipeline",
              f"${peak_val/1e6:.1f}M" if peak_val < 1e9 else f"${peak_val/1e9:.2f}B")
    c4.metric("Largest Industry", top_industry)

    # ── Monthly table (collapsed) ─────────────────────────────────────────────
    with st.expander("Monthly data table"):
        pivot = (
            df.pivot_table(
                index="month", columns="industry",
                values="weighted_amount", aggfunc="sum",
            )
            .fillna(0)
            .sort_index(ascending=False)
        )
        pivot.index = pivot.index.strftime("%b %Y")
        st.dataframe(
            pivot.style.format("${:,.0f}"),
            use_container_width=True,
        )


# ── Router ────────────────────────────────────────────────────────────────────
page = st.session_state.page

if page == "home":
    page_home()
elif page == "data_review":
    page_data_review(study_id)
elif page == "map_view":
    page_map_view(study_id)
elif page == "pipeline_history":
    page_pipeline_history(study_id)
else:
    page_home()
