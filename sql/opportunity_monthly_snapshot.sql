-- ============================================================
--  Opportunity Monthly Snapshot
--  Project: Visual Storytelling — Opportunity Field History
--
--  Produces one row per opportunity per calendar month the
--  opportunity was "open" (created_date ≤ month ≤ close_date
--  or TODAY for still-open deals).
--
--  Each row carries Starting and Ending values for:
--    • CloseDate
--    • Amount
--    • StageName
--    • Probability          (derived from StageName)
--    • WeightedAmount       (Ending Amount × Ending Probability / 100)
--
--  "Starting" = value at the beginning of the month
--  "Ending"   = value at the end of the month
--
--  Source tables (from create_tables.sql):
--    OPPORTUNITIES            — one row per deal
--    OPPORTUNITY_FIELD_HISTORY — audit log of field changes
--
--  Snowflake-specific features used:
--    TABLE(GENERATOR(ROWCOUNT => N))  — inline row generator
--    LAST_VALUE(... IGNORE NULLS)     — carry-forward of sparse changes
--    LAG()                            — prior month's ending value
--    TRY_TO_DATE / TRY_TO_NUMBER      — safe casts from VARCHAR history
-- ============================================================


WITH

-- ────────────────────────────────────────────────────────────
--  1. INITIAL_VALUES
--     The three creation records per opportunity
--     (OLD_VALUE IS NULL in OPPORTUNITY_FIELD_HISTORY).
--     These give us the starting state of each field on the
--     day the opportunity was created.
-- ────────────────────────────────────────────────────────────

initial_values AS (

    SELECT
        opportunity_id,
        MAX(CASE WHEN field = 'StageName' THEN new_value END) AS initial_stage,
        MAX(CASE WHEN field = 'CloseDate' THEN new_value END) AS initial_close_date,
        MAX(CASE WHEN field = 'Amount'    THEN new_value END) AS initial_amount

    FROM opportunity_field_history

    WHERE old_value IS NULL          -- creation records only

    GROUP BY opportunity_id

),


-- ────────────────────────────────────────────────────────────
--  2. MONTH_OFFSETS
--     Generates integers 0 – 79, giving us 80 possible months
--     (≈ 6.5 years; adjust ROWCOUNT if your date range grows).
-- ────────────────────────────────────────────────────────────

month_offsets AS (

    SELECT (ROW_NUMBER() OVER (ORDER BY SEQ4()) - 1) AS offset_months
    FROM TABLE(GENERATOR(ROWCOUNT => 80))

),


-- ────────────────────────────────────────────────────────────
--  3. MONTH_SPINE
--     Cross-join opportunities with month offsets to build
--     one row per opportunity per calendar month.
--
--     month_start = first day of the calendar month
--     month_end   = last day of the calendar month
--
--     Active window:
--       • Created on or before the last day of this month
--       • Deal end date (close_date for closed; 2026-04-12 for
--         open deals) is on or after the first day of this month
-- ────────────────────────────────────────────────────────────

month_spine AS (

    SELECT
        o.opportunity_id,
        o.account_id,
        o.opportunity_name,
        o.status,

        -- Calendar month boundaries
        DATE_TRUNC('month',
            DATEADD('month', mo.offset_months, o.created_date)
        )                                                          AS month_start,

        LAST_DAY(
            DATEADD('month', mo.offset_months, o.created_date)
        )                                                          AS month_end,

        -- Deal active window
        o.created_date,
        o.close_date                                               AS final_close_date,

        -- Open deals cap at project reference date
        CASE
            WHEN o.status IN ('Won', 'Lost') THEN o.close_date
            ELSE DATE('2026-04-12')
        END                                                        AS active_end

    FROM opportunities   o
    CROSS JOIN month_offsets mo

    WHERE
        -- Month must overlap the deal's active window
        DATE_TRUNC('month',
            DATEADD('month', mo.offset_months, o.created_date)
        )  <=  CASE
                    WHEN o.status IN ('Won', 'Lost') THEN o.close_date
                    ELSE DATE('2026-04-12')
               END

),


-- ────────────────────────────────────────────────────────────
--  4. LATEST_CHANGE_PER_MONTH
--     For each (opportunity, field, calendar month), keep only
--     the LAST change record that falls within that month.
--     Changes on or before month_end are eligible; we rank DESC
--     by created_date so rank = 1 is the most recent.
-- ────────────────────────────────────────────────────────────

latest_change_per_month AS (

    SELECT
        h.opportunity_id,
        h.field,
        DATE_TRUNC('month', h.created_date) AS change_month,
        h.new_value,
        ROW_NUMBER() OVER (
            PARTITION BY h.opportunity_id, h.field,
                         DATE_TRUNC('month', h.created_date)
            ORDER BY h.created_date DESC
        )                                   AS rn

    FROM opportunity_field_history h

    WHERE h.old_value IS NOT NULL            -- exclude creation records

),


-- ────────────────────────────────────────────────────────────
--  5. PIVOTED_CHANGES
--     Pivot the three field names into columns so one row
--     per (opportunity_id, change_month) carries all three
--     fields' last-change values for that month.
-- ────────────────────────────────────────────────────────────

pivoted_changes AS (

    SELECT
        opportunity_id,
        change_month,
        MAX(CASE WHEN field = 'StageName' THEN new_value END) AS chg_stage,
        MAX(CASE WHEN field = 'CloseDate' THEN new_value END) AS chg_close_date,
        MAX(CASE WHEN field = 'Amount'    THEN new_value END) AS chg_amount

    FROM latest_change_per_month

    WHERE rn = 1

    GROUP BY opportunity_id, change_month

),


-- ────────────────────────────────────────────────────────────
--  6. SPINE_JOINED
--     Attach the initial values and this month's changes
--     (if any) to every row in the spine.
-- ────────────────────────────────────────────────────────────

spine_joined AS (

    SELECT
        ms.opportunity_id,
        ms.account_id,
        ms.opportunity_name,
        ms.status,
        ms.month_start,
        ms.month_end,
        ms.created_date,
        ms.final_close_date,
        ms.active_end,

        -- Initial (creation-day) values
        iv.initial_stage,
        iv.initial_close_date,
        iv.initial_amount,

        -- Changes that landed in this specific calendar month (may be NULL)
        pc.chg_stage,
        pc.chg_close_date,
        pc.chg_amount

    FROM month_spine      ms
    LEFT JOIN initial_values   iv  ON iv.opportunity_id = ms.opportunity_id
    LEFT JOIN pivoted_changes   pc  ON  pc.opportunity_id = ms.opportunity_id
                                    AND pc.change_month   = ms.month_start

),


-- ────────────────────────────────────────────────────────────
--  7. ENDING_RAW
--     Carry each field forward using LAST_VALUE IGNORE NULLS.
--     The window looks back from the current row to the
--     beginning of the opportunity's history, so a month with
--     no change inherits the most recent prior change.
--     If no change has ever occurred, fall back to initial value.
-- ────────────────────────────────────────────────────────────

ending_raw AS (

    SELECT
        *,

        -- Ending StageName for the month
        COALESCE(
            LAST_VALUE(chg_stage IGNORE NULLS) OVER (
                PARTITION BY opportunity_id
                ORDER BY month_start
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ),
            initial_stage
        ) AS ending_stage,

        -- Ending CloseDate for the month (still VARCHAR at this point)
        COALESCE(
            LAST_VALUE(chg_close_date IGNORE NULLS) OVER (
                PARTITION BY opportunity_id
                ORDER BY month_start
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ),
            initial_close_date
        ) AS ending_close_date_raw,

        -- Ending Amount for the month (still VARCHAR)
        COALESCE(
            LAST_VALUE(chg_amount IGNORE NULLS) OVER (
                PARTITION BY opportunity_id
                ORDER BY month_start
                ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
            ),
            initial_amount
        ) AS ending_amount_raw

    FROM spine_joined

),


-- ────────────────────────────────────────────────────────────
--  8. WITH_STARTING
--     Starting values = the ending values from the prior month.
--     For the first month of an opportunity, LAG returns NULL,
--     so we fall back to the initial (creation-day) values.
-- ────────────────────────────────────────────────────────────

with_starting AS (

    SELECT
        *,

        -- Starting StageName
        COALESCE(
            LAG(ending_stage) OVER (
                PARTITION BY opportunity_id ORDER BY month_start
            ),
            initial_stage
        ) AS starting_stage,

        -- Starting CloseDate (VARCHAR)
        COALESCE(
            LAG(ending_close_date_raw) OVER (
                PARTITION BY opportunity_id ORDER BY month_start
            ),
            initial_close_date
        ) AS starting_close_date_raw,

        -- Starting Amount (VARCHAR)
        COALESCE(
            LAG(ending_amount_raw) OVER (
                PARTITION BY opportunity_id ORDER BY month_start
            ),
            initial_amount
        ) AS starting_amount_raw

    FROM ending_raw

),


-- ────────────────────────────────────────────────────────────
--  9. STAGE_PROB
--     Inline lookup: StageName → win probability %.
--     Mirrors the probability values in OPPORTUNITIES.
-- ────────────────────────────────────────────────────────────

stage_prob (stage_name, probability) AS (

    VALUES
        ('1 - Prospecting',   10),
        ('2 - Scoping',       15),
        ('3 - Engaged',       25),
        ('4 - Proposal',      60),
        ('5 - Negotiation',   80),
        ('6 - Closed Won',   100),
        ('7 - Closed Lost',    0)

),


-- ────────────────────────────────────────────────────────────
--  10. FINAL
--      Cast VARCHAR amounts and dates to native types,
--      join probability, and compute weighted amount.
--      Also joins back to OPPORTUNITIES for deal context.
-- ────────────────────────────────────────────────────────────

final AS (

    SELECT

        -- ── Identity ─────────────────────────────────────────
        ws.opportunity_id,
        ws.opportunity_name,
        ws.account_id,
        ws.status                                              AS deal_status,
        ws.created_date                                        AS opp_created_date,
        ws.final_close_date                                    AS opp_close_date,

        -- ── Month window ─────────────────────────────────────
        ws.month_start,
        ws.month_end,

        -- ── Starting values ───────────────────────────────────
        ws.starting_stage,
        sp_s.probability                                       AS starting_probability,
        TRY_TO_DATE(ws.starting_close_date_raw,   'YYYY-MM-DD') AS starting_close_date,
        TRY_TO_NUMBER(ws.starting_amount_raw)                 AS starting_amount,
        TRY_TO_NUMBER(ws.starting_amount_raw)
            * sp_s.probability / 100.0                        AS starting_weighted_amount,

        -- ── Ending values ─────────────────────────────────────
        ws.ending_stage,
        sp_e.probability                                       AS ending_probability,
        TRY_TO_DATE(ws.ending_close_date_raw,     'YYYY-MM-DD') AS ending_close_date,
        TRY_TO_NUMBER(ws.ending_amount_raw)                   AS ending_amount,
        TRY_TO_NUMBER(ws.ending_amount_raw)
            * sp_e.probability / 100.0                        AS ending_weighted_amount

    FROM with_starting          ws
    LEFT JOIN stage_prob        sp_s  ON sp_s.stage_name = ws.starting_stage
    LEFT JOIN stage_prob        sp_e  ON sp_e.stage_name = ws.ending_stage

)


-- ────────────────────────────────────────────────────────────
--  OUTPUT
--  Ordered by deal, then month ascending.
--  Remove the LIMIT clause (or increase it) for full output.
-- ────────────────────────────────────────────────────────────

SELECT *
FROM   final
ORDER  BY opportunity_id, month_start
;
