import os
import sys
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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
    if st.button("📊  Pipeline Projection"):
        st.session_state.page = "pipeline_projection"
        st.rerun()
    if st.button("🏆  Won Analysis"):
        st.session_state.page = "won_analysis"
        st.rerun()
    if st.button("🎯  Forecast vs. Actual"):
        st.session_state.page = "forecast_vs_actual"
        st.rerun()
    if st.button("🌊  Pipeline Waterfall"):
        st.session_state.page = "waterfall"
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
def load_pipeline_by_close_date(sid):
    """
    For the animated close-date / months-to-close views.
    Returns a DataFrame with columns:
      month_start (datetime), month_label (str), ENDING_CLOSE_DATE (datetime, month-level),
      months_to_close (int), industry, ENDING_WEIGHTED_AMOUNT
    Sorted chronologically so animation frames play in order.
    """
    pivot = load_csv(data_path(sid, "processed", "OppFieldHist_Pivot.csv"))
    acct  = load_csv(data_path(sid, "raw", "accounts.csv"))

    pivot = pivot.merge(acct[["account_id", "industry"]], left_on="ACCOUNT_ID", right_on="account_id", how="left")
    pivot["month_start"]       = pd.to_datetime(pivot["MONTH_START"])
    pivot["ENDING_CLOSE_DATE"] = pd.to_datetime(pivot["ENDING_CLOSE_DATE"])

    # Aggregate close dates to month level
    pivot["close_month"] = pivot["ENDING_CLOSE_DATE"].dt.to_period("M").dt.to_timestamp()

    agg = (
        pivot.groupby(["month_start", "close_month", "industry"])["ENDING_WEIGHTED_AMOUNT"]
        .sum()
        .reset_index()
        .rename(columns={"close_month": "ENDING_CLOSE_DATE"})
    )
    agg = agg.sort_values(["month_start", "ENDING_CLOSE_DATE"])
    agg["month_label"] = agg["month_start"].dt.strftime("%b %Y")

    # Months to close: integer difference between close month and snapshot month
    agg["months_to_close"] = (
        (agg["ENDING_CLOSE_DATE"].dt.year - agg["month_start"].dt.year) * 12
        + (agg["ENDING_CLOSE_DATE"].dt.month - agg["month_start"].dt.month)
    )
    return agg


@st.cache_data(show_spinner=False)
def load_pipeline_projection(sid):
    """
    Open opportunities with close months >= current month.
    Returns: close_month, industry, weighted_amount (amount × probability / 100).
    """
    opps = load_csv(data_path(sid, "raw", "opportunities.csv"))
    acct = load_csv(data_path(sid, "raw", "accounts.csv"))

    opps["close_date"]  = pd.to_datetime(opps["close_date"])
    opps["close_month"] = opps["close_date"].dt.to_period("M").dt.to_timestamp()
    opps = opps.merge(acct[["account_id", "industry"]], on="account_id", how="left")

    TODAY_M = pd.Timestamp("2026-04-01")   # first of current month
    proj = opps[(opps["status"] == "Open") & (opps["close_month"] >= TODAY_M)].copy()
    proj["weighted_amount"] = proj["amount"] * proj["probability"] / 100.0

    return (
        proj.groupby(["close_month", "industry"])["weighted_amount"]
        .sum().reset_index()
    )


@st.cache_data(show_spinner=False)
def load_won_analysis(sid):
    """
    Monthly Won revenue and Win % from raw opportunities.
    Returns: close_month, industry, won_amount, won_count, closed_count, win_pct.
    """
    opps = load_csv(data_path(sid, "raw", "opportunities.csv"))
    acct = load_csv(data_path(sid, "raw", "accounts.csv"))

    opps["close_date"]  = pd.to_datetime(opps["close_date"])
    opps["close_month"] = opps["close_date"].dt.to_period("M").dt.to_timestamp()
    opps = opps.merge(acct[["account_id", "industry"]], on="account_id", how="left")

    closed = opps[opps["status"].isin(["Won", "Lost"])]
    won    = opps[opps["status"] == "Won"]

    won_agg = (
        won.groupby(["close_month", "industry"])
        .agg(won_amount=("amount", "sum"), won_count=("opportunity_id", "count"))
        .reset_index()
    )
    closed_agg = (
        closed.groupby(["close_month", "industry"])
        .agg(closed_count=("opportunity_id", "count"))
        .reset_index()
    )
    agg = won_agg.merge(closed_agg, on=["close_month", "industry"], how="outer").fillna(0)
    agg["win_pct"] = (agg["won_count"] / agg["closed_count"] * 100).where(
        agg["closed_count"] > 0, other=0.0
    )
    return agg.sort_values("close_month")


@st.cache_data(show_spinner=False)
def load_forecast_vs_actual(sid):
    """
    Forecast (weighted pipeline from pivot, last snapshot ≤ close month) vs.
    Actual (Won amount from raw opportunities), by close month and industry.
    Returns (actual_df, forecast_df).
      actual_df:   close_month, industry, actual_amount
      forecast_df: close_month, industry, forecast_amount
    """
    pivot = load_csv(data_path(sid, "processed", "OppFieldHist_Pivot.csv"))
    opps  = load_csv(data_path(sid, "raw", "opportunities.csv"))
    acct  = load_csv(data_path(sid, "raw", "accounts.csv"))

    # ── Actual: Won opps grouped by close month ───────────────────────────
    opps["close_date"]  = pd.to_datetime(opps["close_date"])
    opps["close_month"] = opps["close_date"].dt.to_period("M").dt.to_timestamp()
    opps = opps.merge(acct[["account_id", "industry"]], on="account_id", how="left")

    actual = (
        opps[opps["status"] == "Won"]
        .groupby(["close_month", "industry"])["amount"]
        .sum().reset_index()
        .rename(columns={"amount": "actual_amount"})
    )

    # ── Forecast: pivot — last snapshot where month_start ≤ close month ──
    pivot["month_start"]       = pd.to_datetime(pivot["MONTH_START"])
    pivot["ENDING_CLOSE_DATE"] = pd.to_datetime(pivot["ENDING_CLOSE_DATE"])
    pivot["close_month"]       = pivot["ENDING_CLOSE_DATE"].dt.to_period("M").dt.to_timestamp()
    pivot = pivot.merge(
        acct[["account_id", "industry"]], left_on="ACCOUNT_ID", right_on="account_id", how="left"
    )

    # Keep rows where the snapshot predates or matches the close month
    valid = pivot[pivot["month_start"] <= pivot["close_month"]].copy()

    # Latest snapshot per (opportunity, close_month)
    latest = (
        valid.groupby(["OPPORTUNITY_ID", "close_month"])["month_start"]
        .max().reset_index().rename(columns={"month_start": "latest_snap"})
    )
    valid = valid.merge(latest, on=["OPPORTUNITY_ID", "close_month"])
    valid = valid[valid["month_start"] == valid["latest_snap"]]

    forecast = (
        valid.groupby(["close_month", "industry"])
        .agg(
            forecast_amount=("ENDING_WEIGHTED_AMOUNT", "sum"),
            forecast_total_amount=("ENDING_AMOUNT", "sum"),
        )
        .reset_index()
    )
    forecast["forecast_pct"] = (
        (forecast["forecast_amount"] / forecast["forecast_total_amount"] * 100)
        .where(forecast["forecast_total_amount"] > 0, other=0.0)
    )

    # Augment actual with lost amounts so we can compute amount-weighted win rate
    lost = (
        opps[opps["status"] == "Lost"]
        .groupby(["close_month", "industry"])["amount"]
        .sum().reset_index().rename(columns={"amount": "lost_amount"})
    )
    actual = actual.merge(lost, on=["close_month", "industry"], how="left").fillna(0)
    actual["actual_pct"] = (
        (actual["actual_amount"] / (actual["actual_amount"] + actual["lost_amount"]) * 100)
        .where((actual["actual_amount"] + actual["lost_amount"]) > 0, other=0.0)
    )

    return actual, forecast


@st.cache_data(show_spinner=False)
def load_waterfall_data(sid, m1_str, m2_str):
    """
    Compute waterfall bar values for the period [m1, m2] (first-of-month strings).

    For each bar:
      Starting  – STARTING value for existing opps (first_month < m1) active at start of m1
      New       – STARTING value at first_month for opps created in [m1, m2]
      Advanced  – sum of positive deltas for opps active at both start and end of period
      Reduced   – sum of negative deltas for the same opps
      Won       – STARTING value (at m1 or first_month) for opps that transitioned to Won
      Lost      – same for Lost  (uses STARTING so weighted-mode shows the pipeline value lost)
      Ending    – ENDING value for all opps still active (not Won/Lost) at m2

    Math balances: Starting + New + Advanced + Reduced − Won − Lost = Ending

    Returns dict[mode] where mode ∈ {"Amount", "Weighted"}, each a dict of bar → float.
    """
    pivot = load_csv(data_path(sid, "processed", "OppFieldHist_Pivot.csv"))
    pivot["month_start"] = pd.to_datetime(pivot["MONTH_START"])

    m1 = pd.Timestamp(m1_str)
    m2 = pd.Timestamp(m2_str)

    CLOSED_WON  = "6 - Closed Won"
    CLOSED_LOST = "7 - Closed Lost"

    # First month per opportunity
    first_months = pivot.groupby("OPPORTUNITY_ID")["month_start"].min().rename("first_month")
    pivot = pivot.join(first_months, on="OPPORTUNITY_ID")

    piv_m1     = pivot[pivot["month_start"] == m1]
    piv_m2     = pivot[pivot["month_start"] == m2]
    piv_period = pivot[(pivot["month_start"] >= m1) & (pivot["month_start"] <= m2)]

    # Classify won/lost transitions within the period.
    # Only count open→Won / open→Lost (exclude already-closed starting stages).
    won_trans = piv_period[
        (piv_period["ENDING_STAGE"] == CLOSED_WON) &
        (~piv_period["STARTING_STAGE"].isin([CLOSED_WON, CLOSED_LOST]))
    ]
    lost_trans = piv_period[
        (piv_period["ENDING_STAGE"] == CLOSED_LOST) &
        (~piv_period["STARTING_STAGE"].isin([CLOSED_WON, CLOSED_LOST]))
    ]
    won_ids  = set(won_trans["OPPORTUNITY_ID"])
    lost_ids = set(lost_trans["OPPORTUNITY_ID"])

    # Opps that transitioned Won→open again and are still active at m2 are not exits.
    reopened_ids = set(piv_m2.loc[
        piv_m2["OPPORTUNITY_ID"].isin(won_ids | lost_ids) &
        ~piv_m2["STARTING_STAGE"].isin([CLOSED_WON, CLOSED_LOST]) &
        ~piv_m2["ENDING_STAGE"].isin([CLOSED_WON, CLOSED_LOST])
    ]["OPPORTUNITY_ID"])
    won_ids  = won_ids  - reopened_ids
    lost_ids = lost_ids - reopened_ids

    # Opps that both won AND lost during the period: treat as Lost (net outcome).
    won_ids = won_ids - lost_ids

    changed_ids = won_ids | lost_ids

    # New vs existing opp sets
    new_ids      = set(first_months[(first_months >= m1) & (first_months <= m2)].index)
    existing_ids = set(first_months[first_months < m1].index)

    result = {}
    for mode in ("Amount", "Weighted"):
        S = "STARTING_AMOUNT"          if mode == "Amount" else "STARTING_WEIGHTED_AMOUNT"
        E = "ENDING_AMOUNT"            if mode == "Amount" else "ENDING_WEIGHTED_AMOUNT"

        # ── Starting ─────────────────────────────────────────────────────────
        starting = piv_m1.loc[
            piv_m1["OPPORTUNITY_ID"].isin(existing_ids) &
            ~piv_m1["STARTING_STAGE"].isin([CLOSED_WON, CLOSED_LOST]),
            S,
        ].sum()

        # ── New ───────────────────────────────────────────────────────────────
        new_val = piv_period.loc[
            piv_period["OPPORTUNITY_ID"].isin(new_ids) &
            (piv_period["month_start"] == piv_period["first_month"]),
            S,
        ].sum()

        # ── Won starting value ────────────────────────────────────────────────
        # Only count existing opps that were open (not already closed) at m1.
        won_exist = piv_m1.loc[
            piv_m1["OPPORTUNITY_ID"].isin(won_ids & existing_ids) &
            ~piv_m1["STARTING_STAGE"].isin([CLOSED_WON, CLOSED_LOST]),
            S,
        ].sum()
        won_new   = piv_period.loc[
            piv_period["OPPORTUNITY_ID"].isin(won_ids & new_ids) &
            (piv_period["month_start"] == piv_period["first_month"]),
            S,
        ].sum()
        won_val = float(won_exist) + float(won_new)

        # ── Lost starting value ───────────────────────────────────────────────
        lost_exist = piv_m1.loc[
            piv_m1["OPPORTUNITY_ID"].isin(lost_ids & existing_ids) &
            ~piv_m1["STARTING_STAGE"].isin([CLOSED_WON, CLOSED_LOST]),
            S,
        ].sum()
        lost_new   = piv_period.loc[
            piv_period["OPPORTUNITY_ID"].isin(lost_ids & new_ids) &
            (piv_period["month_start"] == piv_period["first_month"]),
            S,
        ].sum()
        lost_val = float(lost_exist) + float(lost_new)

        # ── Advanced / Reduced — opps active at BOTH start and end ───────────
        piv_m2_active = piv_m2[
            ~piv_m2["OPPORTUNITY_ID"].isin(changed_ids) &
            ~piv_m2["STARTING_STAGE"].isin([CLOSED_WON, CLOSED_LOST]) &
            ~piv_m2["ENDING_STAGE"].isin([CLOSED_WON, CLOSED_LOST])
        ]
        active_ids = set(piv_m2_active["OPPORTUNITY_ID"])

        end_vals = piv_m2_active.set_index("OPPORTUNITY_ID")[E]

        # Filter by valid STARTING_STAGE at m1 to match what Starting includes.
        start_exist = piv_m1.loc[
            piv_m1["OPPORTUNITY_ID"].isin(active_ids & existing_ids) &
            ~piv_m1["STARTING_STAGE"].isin([CLOSED_WON, CLOSED_LOST])
        ].set_index("OPPORTUNITY_ID")[S]

        start_new = piv_period.loc[
            piv_period["OPPORTUNITY_ID"].isin(active_ids & new_ids) &
            (piv_period["month_start"] == piv_period["first_month"])
        ].set_index("OPPORTUNITY_ID")[S]

        start_vals = pd.concat([start_exist, start_new])
        delta      = end_vals.subtract(start_vals, fill_value=0)

        advanced = float(delta[delta > 0].sum())
        reduced  = float(delta[delta < 0].sum())

        # ── Ending ────────────────────────────────────────────────────────────
        ending = float(
            piv_m2.loc[
                ~piv_m2["STARTING_STAGE"].isin([CLOSED_WON, CLOSED_LOST]) &
                ~piv_m2["ENDING_STAGE"].isin([CLOSED_WON, CLOSED_LOST]),
                E
            ].sum()
        )

        result[mode] = dict(
            starting=float(starting),
            new=float(new_val),
            advanced=advanced,
            reduced=reduced,
            won=won_val,
            lost=lost_val,
            ending=ending,
        )

    return result


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

    col4, col5, col6 = st.columns(3, gap="large")
    with col4:
        if st.button(
            "📊 Pipeline Projection\n\nForward-looking view of open opportunities "
            "by expected close month. Stacked by industry using Amount × Probability "
            "to show projected weighted pipeline.",
            key="home_pipeline_projection",
            use_container_width=True,
        ):
            st.session_state.page = "pipeline_projection"
            st.rerun()
    with col5:
        if st.button(
            "🏆 Won Analysis\n\nMonthly closed-won revenue (bars) and win rate "
            "(line, secondary axis). Toggle industry breakdown to see performance "
            "by segment or in aggregate.",
            key="home_won_analysis",
            use_container_width=True,
        ):
            st.session_state.page = "won_analysis"
            st.rerun()
    with col6:
        if st.button(
            "🎯 Forecast vs. Actual\n\nCompares weighted pipeline forecasts against "
            "actual won revenue by close month. Toggle between dollar amounts and "
            "win-rate %. Delta chart shows over- or under-performance.",
            key="home_forecast_vs_actual",
            use_container_width=True,
        ):
            st.session_state.page = "forecast_vs_actual"
            st.rerun()

    col7, col8, col9 = st.columns(3, gap="large")
    with col7:
        if st.button(
            "🌊 Pipeline Waterfall\n\nBreaks down pipeline movement for any month "
            "or date range: starting balance, new opportunities, stage advances & "
            "reductions, won/lost exits, and ending balance. Amount or weighted.",
            key="home_waterfall",
            use_container_width=True,
        ):
            st.session_state.page = "waterfall"
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


def _ytick_format(max_val):
    """Return (tick_vals, tick_text) for a dollar y-axis."""
    if max_val >= 1e9:
        ticks = [i * 1e9 for i in range(0, int(max_val / 1e9) + 2)]
        return ticks, [f"${int(v/1e9)}B" for v in ticks]
    step_m = max(1, int(max_val / 1e6 / 5))
    ticks = [i * step_m * 1e6 for i in range(0, int(max_val / (step_m * 1e6)) + 2)]
    return ticks, [f"${int(v/1e6)}M" for v in ticks]


def page_pipeline_history(sid):

    # ── Header row ────────────────────────────────────────────────────────────
    col_title, col_xaxis = st.columns([3, 1])
    with col_title:
        st.title("Opportunity Pipeline History")
        st.caption(f"Case study: {selected_study['title']}")
    with col_xaxis:
        st.markdown("<br>", unsafe_allow_html=True)
        xaxis_choice = st.selectbox(
            "X-axis",
            ["Month Start", "Close Date Ending Value", "Months to Close Date"],
            key="pipeline_xaxis",
        )

    # ── Shared colour palette ─────────────────────────────────────────────────
    acct_df   = load_csv(data_path(sid, "raw", "accounts.csv"))
    industries = sorted(acct_df["industry"].dropna().unique())
    palette    = px.colors.qualitative.Set2
    colour_map = {ind: palette[i % len(palette)] for i, ind in enumerate(industries)}

    # ══════════════════════════════════════════════════════════════════════════
    # MODE A — Month Start (line chart)
    # ══════════════════════════════════════════════════════════════════════════
    if xaxis_choice == "Month Start":
        st.markdown(
            "Monthly **ending weighted pipeline** per industry — each opportunity's "
            "closing amount multiplied by its stage probability, summed by month."
        )

        df = load_monthly_pipeline_from_csv(sid)
        if df.empty:
            st.info("No pipeline data available.")
            return

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

        ytick_vals, ytick_text = _ytick_format(total["weighted_amount"].max())
        fig.update_layout(
            height=520,
            margin={"l": 0, "r": 0, "t": 20, "b": 0},
            hovermode="x unified",
            legend=dict(
                title="Industry", orientation="v",
                x=1.01, y=1, xanchor="left",
                bgcolor="rgba(255,255,255,0.85)",
                bordercolor="#e0e0e0", borderwidth=1,
            ),
            xaxis=dict(title="Month", tickformat="%b %Y", showgrid=False),
            yaxis=dict(
                title="Weighted Pipeline",
                tickvals=ytick_vals, ticktext=ytick_text,
                showgrid=True, gridcolor="#f0f0f0",
            ),
            plot_bgcolor="white", paper_bgcolor="white",
        )
        st.plotly_chart(fig, use_container_width=True)

        # ── Summary strip ─────────────────────────────────────────────────────
        st.markdown("---")
        total_by_month = total.set_index("month")["weighted_amount"]
        latest_month   = df["month"].max()
        latest_total   = total_by_month.get(latest_month, 0)
        peak_month     = total_by_month.idxmax()
        peak_val       = total_by_month.max()
        top_industry   = df.groupby("industry")["weighted_amount"].sum().idxmax()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Latest Month Total",
                  f"${latest_total/1e6:.1f}M" if latest_total < 1e9 else f"${latest_total/1e9:.2f}B")
        c2.metric("Peak Month", peak_month.strftime("%b %Y"))
        c3.metric("Peak Pipeline",
                  f"${peak_val/1e6:.1f}M" if peak_val < 1e9 else f"${peak_val/1e9:.2f}B")
        c4.metric("Largest Industry", top_industry)

        with st.expander("Monthly data table"):
            tbl = (
                df.pivot_table(index="month", columns="industry",
                               values="weighted_amount", aggfunc="sum")
                .fillna(0).sort_index(ascending=False)
            )
            tbl.index = tbl.index.strftime("%b %Y")
            st.dataframe(tbl.style.format("${:,.0f}"), use_container_width=True)

    # ══════════════════════════════════════════════════════════════════════════
    # MODE B — Close Date Ending Value (animated line chart, monthly x-axis)
    # MODE C — Months to Close Date (animated line chart, integer x-axis)
    # ══════════════════════════════════════════════════════════════════════════
    else:
        if xaxis_choice == "Close Date Ending Value":
            st.markdown(
                "Weighted pipeline by expected close month. Each frame is one monthly snapshot — "
                "use the play axis to animate through time."
            )
        else:
            st.markdown(
                "Weighted pipeline by months remaining until expected close, relative to each snapshot. "
                "Each frame is one monthly snapshot — use the play axis to animate through time."
            )

        speed_label = st.radio(
            "Playback speed", ["1×", "2×", "4×"],
            horizontal=True, key="pipeline_speed",
        )
        frame_ms = {"1×": 800, "2×": 400, "4×": 200}[speed_label]

        df = load_pipeline_by_close_date(sid)
        if df.empty:
            st.info("No pipeline data available.")
            return

        # Ordered frame labels (chronological)
        ordered_labels = (
            df[["month_start", "month_label"]]
            .drop_duplicates()
            .sort_values("month_start")["month_label"]
            .tolist()
        )

        # Industries sorted descending by total weighted amount so the
        # highest-value industry appears first in legend and hover tooltip
        industry_order = (
            df.groupby("industry")["ENDING_WEIGHTED_AMOUNT"]
            .sum()
            .sort_values(ascending=False)
            .index.tolist()
        )

        max_val = df["ENDING_WEIGHTED_AMOUNT"].max()
        ytick_vals, ytick_text = _ytick_format(max_val)

        # X-axis config varies by mode
        if xaxis_choice == "Close Date Ending Value":
            x_col    = "ENDING_CLOSE_DATE"
            x_label  = "Expected Close Month"
            x_min    = df["ENDING_CLOSE_DATE"].min()
            x_max    = df["ENDING_CLOSE_DATE"].max()
            range_x  = [x_min, x_max]
            xaxis_kw = dict(tickformat="%b '%y", showgrid=False, range=[x_min, x_max])
        else:
            x_col    = "months_to_close"
            x_label  = "Months to Close"
            x_min    = int(df["months_to_close"].min())
            x_max    = int(df["months_to_close"].max())
            range_x  = [x_min, x_max]
            xaxis_kw = dict(showgrid=False, range=[x_min, x_max], dtick=3, ticksuffix=" mo")

        fig = px.line(
            df,
            x=x_col,
            y="ENDING_WEIGHTED_AMOUNT",
            color="industry",
            animation_frame="month_label",
            color_discrete_map=colour_map,
            category_orders={
                "month_label": ordered_labels,
                "industry":    industry_order,
            },
            labels={
                x_col:                    x_label,
                "ENDING_WEIGHTED_AMOUNT": "Weighted Pipeline",
                "industry":               "Industry",
                "month_label":            "Snapshot Month",
            },
            range_x=range_x,
            range_y=[0, max_val * 1.08],
        )

        fig.update_traces(line=dict(width=2.5))

        fig.update_layout(
            height=560,
            margin={"l": 0, "r": 0, "t": 20, "b": 0},
            hovermode="x unified",
            legend=dict(
                title="Industry", orientation="v",
                x=1.01, y=1, xanchor="left",
                traceorder="normal",
                bgcolor="rgba(255,255,255,0.85)",
                bordercolor="#e0e0e0", borderwidth=1,
            ),
            xaxis=xaxis_kw,
            yaxis=dict(
                title="Weighted Pipeline",
                tickvals=ytick_vals, ticktext=ytick_text,
                showgrid=True, gridcolor="#f0f0f0",
            ),
            plot_bgcolor="white", paper_bgcolor="white",
            updatemenus=[{
                "type": "buttons",
                "showactive": False,
                "y": -0.12, "x": 0.5, "xanchor": "center",
                "buttons": [
                    {"label": "▶  Play",
                     "method": "animate",
                     "args": [None, {"frame": {"duration": frame_ms, "redraw": True},
                                     "fromcurrent": True, "transition": {"duration": 0}}]},
                    {"label": "⏭  Fast Forward",
                     "method": "animate",
                     "args": [None, {"frame": {"duration": max(frame_ms // 4, 50), "redraw": True},
                                     "fromcurrent": True, "transition": {"duration": 0}}]},
                    {"label": "⏸  Pause",
                     "method": "animate",
                     "args": [[None], {"frame": {"duration": 0, "redraw": False},
                                       "mode": "immediate", "transition": {"duration": 0}}]},
                ],
            }],
        )

        fig.layout.sliders[0].update(
            currentvalue={"prefix": "Snapshot: ", "font": {"size": 13}},
            y=-0.04,
        )

        st.plotly_chart(fig, use_container_width=True)


def page_pipeline_projection(sid):

    col_title, _ = st.columns([3, 1])
    with col_title:
        st.title("Pipeline Projection")
        st.caption(f"Case study: {selected_study['title']}")

    st.markdown(
        "Projected weighted pipeline for **open** opportunities with expected close dates "
        "in the current or future months. Each bar = Amount × Probability, stacked by industry."
    )

    acct_df   = load_csv(data_path(sid, "raw", "accounts.csv"))
    industries = sorted(acct_df["industry"].dropna().unique())
    palette    = px.colors.qualitative.Set2
    colour_map = {ind: palette[i % len(palette)] for i, ind in enumerate(industries)}

    df = load_pipeline_projection(sid)
    if df.empty:
        st.info("No open opportunities with current or future close dates found.")
        return

    total = df.groupby("close_month")["weighted_amount"].sum().reset_index()
    ytick_vals, ytick_text = _ytick_format(total["weighted_amount"].max())

    fig = go.Figure()
    for ind in industries:
        sub = df[df["industry"] == ind].sort_values("close_month")
        if sub["weighted_amount"].sum() == 0:
            continue
        fig.add_trace(go.Bar(
            x=sub["close_month"],
            y=sub["weighted_amount"],
            name=ind,
            marker_color=colour_map[ind],
            hovertemplate=(
                f"<b>{ind}</b><br>"
                "%{x|%b %Y}<br>"
                "Projected pipeline: $%{y:,.0f}<extra></extra>"
            ),
        ))

    fig.update_layout(
        barmode="stack",
        height=520,
        margin={"l": 0, "r": 0, "t": 20, "b": 0},
        hovermode="x unified",
        legend=dict(
            title="Industry", orientation="v",
            x=1.01, y=1, xanchor="left",
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="#e0e0e0", borderwidth=1,
        ),
        xaxis=dict(title="Close Month", tickformat="%b %Y", showgrid=False, dtick="M1"),
        yaxis=dict(
            title="Projected Weighted Pipeline",
            tickvals=ytick_vals, ticktext=ytick_text,
            showgrid=True, gridcolor="#f0f0f0",
        ),
        plot_bgcolor="white", paper_bgcolor="white",
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Summary strip ─────────────────────────────────────────────────────
    st.markdown("---")
    opps_raw = load_csv(data_path(sid, "raw", "opportunities.csv"))
    opps_raw["close_date"]  = pd.to_datetime(opps_raw["close_date"])
    opps_raw["close_month"] = opps_raw["close_date"].dt.to_period("M").dt.to_timestamp()
    future_open_ct = int(
        ((opps_raw["status"] == "Open") & (opps_raw["close_month"] >= pd.Timestamp("2026-04-01"))).sum()
    )
    total_proj   = df["weighted_amount"].sum()
    peak_month   = total.set_index("close_month")["weighted_amount"].idxmax()
    top_industry = df.groupby("industry")["weighted_amount"].sum().idxmax()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Projected Pipeline",
              f"${total_proj/1e6:.1f}M" if total_proj < 1e9 else f"${total_proj/1e9:.2f}B")
    c2.metric("Open Opportunities in Projection", f"{future_open_ct:,}")
    c3.metric("Largest Close Month", peak_month.strftime("%b %Y"))
    c4.metric("Largest Industry", top_industry)


def page_won_analysis(sid):

    col_title, col_toggle = st.columns([3, 1])
    with col_title:
        st.title("Won Analysis")
        st.caption(f"Case study: {selected_study['title']}")
    with col_toggle:
        st.markdown("<br>", unsafe_allow_html=True)
        show_industry = st.checkbox("Break out by Industry", value=False, key="won_industry")

    st.markdown(
        "Monthly closed-won revenue (**bars**, left axis) and win rate (**line**, right axis). "
        "Win rate = Won ÷ (Won + Lost) opportunities closed in that month."
    )

    acct_df   = load_csv(data_path(sid, "raw", "accounts.csv"))
    industries = sorted(acct_df["industry"].dropna().unique())
    palette    = px.colors.qualitative.Set2
    colour_map = {ind: palette[i % len(palette)] for i, ind in enumerate(industries)}

    df = load_won_analysis(sid)
    if df.empty:
        st.info("No closed opportunities found.")
        return

    max_won = df.groupby("close_month")["won_amount"].sum().max()
    ytick_vals, ytick_text = _ytick_format(max_won)

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    if show_industry:
        for ind in industries:
            sub = df[df["industry"] == ind].sort_values("close_month")
            if sub["won_amount"].sum() == 0:
                continue
            fig.add_trace(go.Bar(
                x=sub["close_month"],
                y=sub["won_amount"],
                name=ind,
                marker_color=colour_map[ind],
                legendgroup=ind,
                hovertemplate=(
                    f"<b>{ind}</b><br>"
                    "%{x|%b %Y}<br>"
                    "Won: $%{y:,.0f}<extra></extra>"
                ),
            ), secondary_y=False)

        for ind in industries:
            sub = df[df["industry"] == ind].sort_values("close_month")
            if sub["closed_count"].sum() == 0:
                continue
            fig.add_trace(go.Scatter(
                x=sub["close_month"],
                y=sub["win_pct"],
                name=f"{ind} Win %",
                mode="lines+markers",
                line=dict(color=colour_map[ind], dash="dot", width=1.5),
                marker=dict(size=5),
                showlegend=False,
                legendgroup=ind,
                hovertemplate=(
                    f"<b>{ind}</b><br>"
                    "%{x|%b %Y}<br>"
                    "Win rate: %{y:.1f}%<extra></extra>"
                ),
            ), secondary_y=True)
    else:
        agg = (
            df.groupby("close_month")
            .agg(won_amount=("won_amount", "sum"),
                 won_count=("won_count", "sum"),
                 closed_count=("closed_count", "sum"))
            .reset_index().sort_values("close_month")
        )
        agg["win_pct"] = (agg["won_count"] / agg["closed_count"] * 100).where(
            agg["closed_count"] > 0, other=0.0
        )
        fig.add_trace(go.Bar(
            x=agg["close_month"],
            y=agg["won_amount"],
            name="Won Amount",
            marker_color="#FF8C00",
            hovertemplate=(
                "<b>All Industries</b><br>"
                "%{x|%b %Y}<br>"
                "Won: $%{y:,.0f}<extra></extra>"
            ),
        ), secondary_y=False)
        fig.add_trace(go.Scatter(
            x=agg["close_month"],
            y=agg["win_pct"],
            name="Win %",
            mode="lines+markers",
            line=dict(color="#1a1a2e", width=2),
            marker=dict(size=6),
            hovertemplate=(
                "<b>Win Rate</b><br>"
                "%{x|%b %Y}<br>"
                "Win rate: %{y:.1f}%<extra></extra>"
            ),
        ), secondary_y=True)

    fig.update_layout(
        barmode="stack",
        height=520,
        margin={"l": 0, "r": 0, "t": 20, "b": 60},
        hovermode="x unified",
        legend=dict(
            title="Industry" if show_industry else None,
            orientation="v",
            x=1.08, y=1, xanchor="left",
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="#e0e0e0", borderwidth=1,
        ),
        xaxis=dict(title="Close Month", tickformat="%b %Y", showgrid=False),
        plot_bgcolor="white", paper_bgcolor="white",
    )
    fig.update_yaxes(
        title_text="Won Revenue",
        tickvals=ytick_vals, ticktext=ytick_text,
        showgrid=True, gridcolor="#f0f0f0",
        secondary_y=False,
    )
    fig.update_yaxes(
        title_text="Win Rate (%)",
        range=[0, 105],
        ticksuffix="%",
        showgrid=False,
        secondary_y=True,
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Summary strip ─────────────────────────────────────────────────────
    st.markdown("---")
    total_won      = df["won_amount"].sum()
    total_won_ct   = int(df["won_count"].sum())
    total_closed_ct = int(df["closed_count"].sum())
    overall_win_pct = total_won_ct / total_closed_ct * 100 if total_closed_ct > 0 else 0
    top_ind        = df.groupby("industry")["won_amount"].sum().idxmax()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Won Revenue",
              f"${total_won/1e6:.1f}M" if total_won < 1e9 else f"${total_won/1e9:.2f}B")
    c2.metric("Deals Won", f"{total_won_ct:,}")
    c3.metric("Overall Win Rate", f"{overall_win_pct:.1f}%")
    c4.metric("Top Industry by Won Revenue", top_ind)


def page_forecast_vs_actual(sid):

    col_title, col_right = st.columns([3, 1])
    with col_title:
        st.title("Forecast vs. Actual")
        st.caption(f"Case study: {selected_study['title']}")
    with col_right:
        st.markdown("<br>", unsafe_allow_html=True)
        yaxis_mode    = st.radio("Y-axis", ["Amount ($)", "% Won"],
                                 horizontal=False, key="fva_yaxis")
        show_industry = st.checkbox("By Industry", value=False, key="fva_industry")

    if yaxis_mode == "% Won":
        st.markdown(
            "**Solid lines** = blended forecast probability (weighted pipeline ÷ total pipeline amount). "
            "**Dashed lines** = actual win rate (won ÷ won + lost, by amount) per expected close month."
        )
    else:
        st.markdown(
            "**Solid lines** = forecasted weighted pipeline (last snapshot before each close month). "
            "**Dashed lines** = actual closed-won revenue by expected close month."
        )

    acct_df   = load_csv(data_path(sid, "raw", "accounts.csv"))
    industries = sorted(acct_df["industry"].dropna().unique())
    palette    = px.colors.qualitative.Set2
    colour_map = {ind: palette[i % len(palette)] for i, ind in enumerate(industries)}

    actual, forecast = load_forecast_vs_actual(sid)
    if actual.empty and forecast.empty:
        st.info("No data available.")
        return

    # ── Monthly aggregates — Amount ───────────────────────────────────────
    f_monthly = forecast.groupby("close_month")["forecast_amount"].sum().reset_index()
    a_monthly = actual.groupby("close_month")["actual_amount"].sum().reset_index()
    delta_monthly_amt = (
        f_monthly.merge(a_monthly, on="close_month", how="outer")
        .fillna(0).sort_values("close_month")
    )
    delta_monthly_amt["delta"] = (
        delta_monthly_amt["actual_amount"] - delta_monthly_amt["forecast_amount"]
    )

    # ── Monthly aggregates — % Won ────────────────────────────────────────
    f_monthly_pct = (
        forecast.groupby("close_month")
        .agg(total_weighted=("forecast_amount", "sum"),
             total_amount=("forecast_total_amount", "sum"))
        .reset_index()
    )
    f_monthly_pct["forecast_pct"] = (
        (f_monthly_pct["total_weighted"] / f_monthly_pct["total_amount"] * 100)
        .where(f_monthly_pct["total_amount"] > 0, other=0.0)
    )
    a_monthly_pct = (
        actual.groupby("close_month")
        .agg(won=("actual_amount", "sum"), lost=("lost_amount", "sum"))
        .reset_index()
    )
    a_monthly_pct["actual_pct"] = (
        (a_monthly_pct["won"] / (a_monthly_pct["won"] + a_monthly_pct["lost"]) * 100)
        .where((a_monthly_pct["won"] + a_monthly_pct["lost"]) > 0, other=0.0)
    )
    delta_monthly_pct = (
        f_monthly_pct[["close_month", "forecast_pct"]]
        .merge(a_monthly_pct[["close_month", "actual_pct"]], on="close_month", how="outer")
        .fillna(0).sort_values("close_month")
    )
    delta_monthly_pct["delta"] = (
        delta_monthly_pct["actual_pct"] - delta_monthly_pct["forecast_pct"]
    )

    all_dates = pd.concat([forecast["close_month"], actual["close_month"]])
    x_min = all_dates.min()
    x_max = all_dates.max()

    # ── Axis/label config per mode ────────────────────────────────────────
    if yaxis_mode == "Amount ($)":
        delta_monthly  = delta_monthly_amt
        all_amounts    = pd.concat([forecast["forecast_amount"], actual["actual_amount"]])
        ytick_vals, ytick_text = _ytick_format(all_amounts.max())
        yaxis_kw       = dict(title="Amount ($)", tickvals=ytick_vals, ticktext=ytick_text,
                              showgrid=True, gridcolor="#f0f0f0")
        delta_yaxis_kw = dict(title="Delta ($)", showgrid=True, gridcolor="#f0f0f0",
                              zeroline=True, zerolinecolor="#888", zerolinewidth=1.5)
        chart_title    = "Weighted Forecast vs. Actual Won Revenue"
        delta_header   = "#### Delta: Actual Won − Forecast"
    else:
        delta_monthly  = delta_monthly_pct
        yaxis_kw       = dict(title="Win Rate (%)", range=[0, 105],
                              ticksuffix="%", showgrid=True, gridcolor="#f0f0f0")
        delta_yaxis_kw = dict(title="Delta (pp)", showgrid=True, gridcolor="#f0f0f0",
                              zeroline=True, zerolinecolor="#888", zerolinewidth=1.5,
                              ticksuffix=" pp")
        chart_title    = "Forecast Win Probability vs. Actual Win Rate"
        delta_header   = "#### Delta: Actual Win Rate − Forecast Probability (percentage points)"

    # ── Top chart ─────────────────────────────────────────────────────────
    fig_top = go.Figure()

    if show_industry:
        f_y   = "forecast_pct"  if yaxis_mode == "% Won" else "forecast_amount"
        a_y   = "actual_pct"    if yaxis_mode == "% Won" else "actual_amount"
        f_fmt = "%{y:.1f}%"     if yaxis_mode == "% Won" else "$%{y:,.0f}"
        a_fmt = "%{y:.1f}%"     if yaxis_mode == "% Won" else "$%{y:,.0f}"
        f_lbl = "Probability"   if yaxis_mode == "% Won" else "Forecast"
        a_lbl = "Win rate"      if yaxis_mode == "% Won" else "Actual won"

        for ind in industries:
            f = forecast[forecast["industry"] == ind].sort_values("close_month")
            a = actual[actual["industry"] == ind].sort_values("close_month")
            if f[f_y].sum() > 0:
                fig_top.add_trace(go.Scatter(
                    x=f["close_month"], y=f[f_y],
                    name=ind, mode="lines",
                    line=dict(color=colour_map[ind], width=2),
                    legendgroup=ind,
                    hovertemplate=(
                        f"<b>{ind} — Forecast</b><br>%{{x|%b %Y}}<br>"
                        f"{f_lbl}: {f_fmt}<extra></extra>"
                    ),
                ))
            if a[a_y].sum() > 0:
                fig_top.add_trace(go.Scatter(
                    x=a["close_month"], y=a[a_y],
                    name=f"{ind} (Actual)", mode="lines",
                    line=dict(color=colour_map[ind], width=2, dash="dash"),
                    legendgroup=ind, showlegend=False,
                    hovertemplate=(
                        f"<b>{ind} — Actual</b><br>%{{x|%b %Y}}<br>"
                        f"{a_lbl}: {a_fmt}<extra></extra>"
                    ),
                ))
    else:
        if yaxis_mode == "Amount ($)":
            fig_top.add_trace(go.Scatter(
                x=f_monthly["close_month"], y=f_monthly["forecast_amount"],
                name="Forecast", mode="lines",
                line=dict(color="#2196F3", width=2.5),
                hovertemplate="<b>Forecast</b><br>%{x|%b %Y}<br>$%{y:,.0f}<extra></extra>",
            ))
            fig_top.add_trace(go.Scatter(
                x=a_monthly["close_month"], y=a_monthly["actual_amount"],
                name="Actual Won", mode="lines",
                line=dict(color="#FF5722", width=2.5, dash="dash"),
                hovertemplate="<b>Actual Won</b><br>%{x|%b %Y}<br>$%{y:,.0f}<extra></extra>",
            ))
        else:
            fig_top.add_trace(go.Scatter(
                x=f_monthly_pct["close_month"], y=f_monthly_pct["forecast_pct"],
                name="Forecast Probability", mode="lines",
                line=dict(color="#2196F3", width=2.5),
                hovertemplate="<b>Forecast Probability</b><br>%{x|%b %Y}<br>%{y:.1f}%<extra></extra>",
            ))
            fig_top.add_trace(go.Scatter(
                x=a_monthly_pct["close_month"], y=a_monthly_pct["actual_pct"],
                name="Actual Win Rate", mode="lines",
                line=dict(color="#FF5722", width=2.5, dash="dash"),
                hovertemplate="<b>Actual Win Rate</b><br>%{x|%b %Y}<br>%{y:.1f}%<extra></extra>",
            ))

    fig_top.update_layout(
        height=400,
        margin={"l": 0, "r": 0, "t": 30, "b": 0},
        hovermode="x unified",
        title=dict(text=chart_title, font=dict(size=14), x=0),
        legend=dict(
            title="Industry" if show_industry else None,
            orientation="v", x=1.01, y=1, xanchor="left",
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="#e0e0e0", borderwidth=1,
        ),
        xaxis=dict(tickformat="%b '%y", showgrid=False, range=[x_min, x_max]),
        yaxis=yaxis_kw,
        plot_bgcolor="white", paper_bgcolor="white",
    )
    st.plotly_chart(fig_top, use_container_width=True)

    # ── Delta chart ────────────────────────────────────────────────────────
    st.markdown(delta_header)
    fig_delta = go.Figure()

    if show_industry:
        if yaxis_mode == "Amount ($)":
            f_by = forecast.groupby(["close_month","industry"])["forecast_amount"].sum().reset_index()
            a_by = actual.groupby(["close_month","industry"])["actual_amount"].sum().reset_index()
            d_by = f_by.merge(a_by, on=["close_month","industry"], how="outer").fillna(0)
            d_by["delta"] = d_by["actual_amount"] - d_by["forecast_amount"]
            hover_val = "Delta: $%{y:,.0f}"
        else:
            f_by = forecast[["close_month","industry","forecast_pct"]]
            a_by = actual[["close_month","industry","actual_pct"]]
            d_by = f_by.merge(a_by, on=["close_month","industry"], how="outer").fillna(0)
            d_by["delta"] = d_by["actual_pct"] - d_by["forecast_pct"]
            hover_val = "Delta: %{y:.1f} pp"
        d_by = d_by.sort_values("close_month")
        for ind in industries:
            sub = d_by[d_by["industry"] == ind]
            if sub["delta"].abs().sum() == 0:
                continue
            fig_delta.add_trace(go.Bar(
                x=sub["close_month"], y=sub["delta"],
                name=ind, marker_color=colour_map[ind],
                hovertemplate=f"<b>{ind}</b><br>%{{x|%b %Y}}<br>{hover_val}<extra></extra>",
            ))
        delta_barmode = "relative"
    else:
        if yaxis_mode == "Amount ($)":
            hover_val = "$%{y:,.0f}"
        else:
            hover_val = "%{y:.1f} pp"
        colors = ["#4CAF50" if d >= 0 else "#F44336" for d in delta_monthly["delta"]]
        fig_delta.add_trace(go.Bar(
            x=delta_monthly["close_month"], y=delta_monthly["delta"],
            marker_color=colors, name="Delta",
            hovertemplate=(
                f"<b>Delta (Actual − Forecast)</b><br>%{{x|%b %Y}}<br>{hover_val}<extra></extra>"
            ),
        ))
        delta_barmode = "overlay"

    fig_delta.update_layout(
        barmode=delta_barmode,
        height=280,
        margin={"l": 0, "r": 0, "t": 10, "b": 0},
        hovermode="x unified",
        showlegend=show_industry,
        legend=dict(
            title="Industry" if show_industry else None,
            orientation="v", x=1.01, y=1, xanchor="left",
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="#e0e0e0", borderwidth=1,
        ),
        xaxis=dict(tickformat="%b '%y", showgrid=False),
        yaxis=delta_yaxis_kw,
        plot_bgcolor="white", paper_bgcolor="white",
    )
    st.plotly_chart(fig_delta, use_container_width=True)

    # ── Summary strip (always in $ terms) ─────────────────────────────────
    st.markdown("---")
    f_total     = forecast["forecast_amount"].sum()
    a_total     = actual["actual_amount"].sum()
    delta_total = a_total - f_total
    delta_pct   = delta_total / f_total * 100 if f_total > 0 else 0

    combined = pd.DataFrame({
        "forecast": f_monthly.set_index("close_month")["forecast_amount"],
        "actual":   a_monthly.set_index("close_month")["actual_amount"],
    }).fillna(0)
    beat_months = int((combined["actual"] > combined["forecast"]).sum())

    def _fmt(v):
        sign = "+" if v >= 0 else ""
        return f"{sign}${v/1e9:.2f}B" if abs(v) >= 1e9 else f"{sign}${v/1e6:.1f}M"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Forecast",
              f"${f_total/1e6:.1f}M" if f_total < 1e9 else f"${f_total/1e9:.2f}B")
    c2.metric("Total Actual Won",
              f"${a_total/1e6:.1f}M" if a_total < 1e9 else f"${a_total/1e9:.2f}B")
    c3.metric("Overall Delta", _fmt(delta_total), delta=f"{delta_pct:+.1f}% vs forecast")
    c4.metric("Months Beating Forecast", f"{beat_months} of {len(combined)}")


def page_waterfall(sid):

    # ── Header controls ───────────────────────────────────────────────────
    col_title, col_metric, col_period = st.columns([2, 1, 1])
    with col_title:
        st.title("Pipeline Waterfall")
        st.caption(f"Case study: {selected_study['title']}")
    with col_metric:
        st.markdown("<br>", unsafe_allow_html=True)
        mode = st.radio("Metric", ["Amount", "Weighted Amount"],
                        horizontal=False, key="wf_mode")
    with col_period:
        st.markdown("<br>", unsafe_allow_html=True)
        period_type = st.radio("Period", ["Monthly", "Date Range"],
                               horizontal=False, key="wf_period")

    # ── Month list from pivot ─────────────────────────────────────────────
    raw_pivot = load_csv(data_path(sid, "processed", "OppFieldHist_Pivot.csv"))
    month_ts_list = sorted(
        pd.to_datetime(raw_pivot["MONTH_START"]).dt.to_period("M")
        .dt.to_timestamp().unique()
    )

    # ── Period selectors ──────────────────────────────────────────────────
    if period_type == "Monthly":
        m_sel = st.selectbox(
            "Month",
            options=month_ts_list,
            index=len(month_ts_list) - 1,
            format_func=lambda ts: ts.strftime("%b %Y"),
            key="wf_month",
        )
        m1 = m2 = m_sel
    else:
        c1, c2 = st.columns(2)
        with c1:
            m1 = st.selectbox(
                "Starting Month",
                options=month_ts_list,
                index=0,
                format_func=lambda ts: ts.strftime("%b %Y"),
                key="wf_start",
            )
        with c2:
            m2 = st.selectbox(
                "Ending Month",
                options=month_ts_list,
                index=len(month_ts_list) - 1,
                format_func=lambda ts: ts.strftime("%b %Y"),
                key="wf_end",
            )
        if m1 > m2:
            st.warning("Starting Month must be on or before Ending Month.")
            return

    # ── Load data ─────────────────────────────────────────────────────────
    data = load_waterfall_data(
        sid,
        m1.strftime("%Y-%m-%d"),
        m2.strftime("%Y-%m-%d"),
    )
    mode_key = "Amount" if mode == "Amount" else "Weighted"
    d = data[mode_key]

    # ── Format helper ─────────────────────────────────────────────────────
    def _fmt(v):
        sign = "+" if v > 0 else ""
        av = abs(v)
        if av >= 1e9:
            return f"{sign}${v/1e9:.2f}B"
        if av >= 1e6:
            return f"{sign}${v/1e6:.1f}M"
        if av >= 1e3:
            return f"{sign}${v/1e3:.0f}K"
        return f"{''+sign}${v:,.0f}"

    # Bars and values
    labels   = ["Starting\nPipeline", "New\nOpportunities", "Advanced",
                "Reduced",             "Won\n(Exit)",        "Lost\n(Exit)",
                "Ending\nPipeline"]
    measures = ["absolute", "relative", "relative",
                "relative",  "relative", "relative",
                "total"]
    values   = [
        d["starting"],
        d["new"],
        d["advanced"],
        d["reduced"],
        -d["won"],
        -d["lost"],
        0,              # "total" measure: Plotly computes running sum
    ]
    # Colors per bar
    COLORS = {
        "Starting\nPipeline":   "#1565C0",
        "New\nOpportunities":   "#2E7D32",
        "Advanced":             "#43A047",
        "Reduced":              "#EF6C00",
        "Won\n(Exit)":          "#6A1B9A",
        "Lost\n(Exit)":         "#C62828",
        "Ending\nPipeline":     "#1565C0",
    }
    bar_colors = [COLORS[lbl] for lbl in labels]

    # Text labels (show on each bar)
    display_vals = [d["starting"], d["new"], d["advanced"],
                    d["reduced"], -d["won"], -d["lost"], d["ending"]]
    bar_texts = [_fmt(v) for v in display_vals]

    period_label = (
        m1.strftime("%b %Y")
        if m1 == m2
        else f"{m1.strftime('%b %Y')} – {m2.strftime('%b %Y')}"
    )

    # ── Chart ─────────────────────────────────────────────────────────────
    fig = go.Figure(go.Waterfall(
        orientation="v",
        measure=measures,
        x=labels,
        y=values,
        text=bar_texts,
        textposition="outside",
        connector=dict(line=dict(color="rgba(80,80,80,0.55)", dash="dot", width=1.5)),
        marker=dict(color=bar_colors),
        hovertemplate="<b>%{x}</b><br>%{customdata}<extra></extra>",
        customdata=bar_texts,
    ))

    # Y-axis ticks
    max_val = max(d["starting"], d["ending"], d["new"], d["won"])
    ytick_vals, ytick_text = _ytick_format(max_val * 1.15)

    fig.update_layout(
        height=540,
        margin={"l": 0, "r": 0, "t": 50, "b": 10},
        title=dict(
            text=(
                f"Pipeline Waterfall — {period_label}"
                + (" (Weighted)" if mode_key == "Weighted" else "")
            ),
            font=dict(size=14), x=0,
        ),
        xaxis=dict(showgrid=False, tickfont=dict(size=11)),
        yaxis=dict(
            tickvals=ytick_vals, ticktext=ytick_text,
            showgrid=True, gridcolor="#f0f0f0",
            zeroline=True, zerolinecolor="#bbbbbb", zerolinewidth=1,
        ),
        plot_bgcolor="white", paper_bgcolor="white",
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Summary strip ─────────────────────────────────────────────────────
    st.markdown("---")
    net_change = d["ending"] - d["starting"]
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Starting Pipeline", _fmt(d["starting"]).lstrip("+"))
    c2.metric("New Opportunities",  _fmt(d["new"]).lstrip("+"))
    c3.metric("Advanced",           _fmt(d["advanced"]).lstrip("+"))
    c4.metric("Won (Exit)",         _fmt(d["won"]).lstrip("+"))
    c5.metric("Lost (Exit)",        _fmt(d["lost"]).lstrip("+"))
    c6.metric("Ending Pipeline",    _fmt(d["ending"]).lstrip("+"),
              delta=_fmt(net_change) + " vs start")


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
elif page == "pipeline_projection":
    page_pipeline_projection(study_id)
elif page == "won_analysis":
    page_won_analysis(study_id)
elif page == "forecast_vs_actual":
    page_forecast_vs_actual(study_id)
elif page == "waterfall":
    page_waterfall(study_id)
else:
    page_home()
