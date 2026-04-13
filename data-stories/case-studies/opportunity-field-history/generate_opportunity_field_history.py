#!/usr/bin/env python3
"""
generate_opportunity_field_history.py

Generates a Salesforce-style Opportunity Field History table for all
opportunities in opportunities.csv.

Tracked fields : StageName | CloseDate | Amount
Output         : data/raw/opportunity_field_history.csv
"""

import calendar
import csv
import os
import random
from datetime import date, timedelta

random.seed(99)

HERE      = os.path.dirname(os.path.abspath(__file__))
OPPS_CSV  = os.path.join(HERE, "data", "raw", "opportunities.csv")
OUT_CSV   = os.path.join(HERE, "data", "raw", "opportunity_field_history.csv")

TODAY     = date(2026, 4, 12)   # project reference date

# ── Stage catalogue ───────────────────────────────────────────────────────────

STAGE_ORDER = {
    "1 - Prospecting": 1, "2 - Scoping":   2, "3 - Engaged":    3,
    "4 - Proposal":    4, "5 - Negotiation":5, "6 - Closed Won": 6,
    "7 - Closed Lost": 7,
}
STAGE_BY_NUM = {v: k for k, v in STAGE_ORDER.items()}

# ── Sales reps (one rep stays consistent per account) ─────────────────────────

SALES_REPS = [
    "Sarah Mitchell",    "James Harrington",  "Priya Patel",
    "Derek Thompson",    "Olivia Chen",       "Marcus Webb",
    "Rachel Nguyen",     "Tyler Brooks",      "Jennifer Walsh",
    "Antonio Rodriguez", "Samantha Lee",      "Kevin O'Brien",
    "Natalie Foster",    "Brian Kim",         "Melissa Grant",
]

FIELDNAMES = [
    "history_id", "opportunity_id", "field",
    "old_value", "new_value", "created_date", "created_by",
]


# ── Date helpers ──────────────────────────────────────────────────────────────

def month_end(y: int, m: int) -> date:
    _, last = calendar.monthrange(y, m)
    return date(y, m, last)


def add_months(d: date, n: int) -> date:
    """Add n months to d; result snapped to month-end."""
    total = d.month + n
    y = d.year + (total - 1) // 12
    m = ((total - 1) % 12) + 1
    return month_end(y, m)


# ── Complexity ────────────────────────────────────────────────────────────────

def pick_complexity() -> str:
    return random.choices(
        ["none", "simple", "medium", "complex"],
        weights=[15, 30, 40, 15],
    )[0]


# ── Stage history ─────────────────────────────────────────────────────────────

def gen_stage_changes(
    created: date,
    end_date: date,      # close_date for closed; TODAY for open
    final_stage: str,
    status: str,
    complexity: str,
) -> list[tuple[date, str, str]]:
    """
    Returns [(change_date, old_stage, new_stage), ...] for post-creation
    stage changes.  Initial stage is always "1 - Prospecting".
    """
    final_num = STAGE_ORDER[final_stage]

    # Number of intermediate steps (between creation and final stage)
    n_inter = {
        "none":    random.randint(0, 0),
        "simple":  random.randint(1, 2),
        "medium":  random.randint(3, 6),
        "complex": random.randint(7, 12),
    }[complexity]

    changes: list[tuple[date, str, str]] = []
    cur_num  = 1
    cur_date = created

    is_closed_final = final_num in (6, 7)

    for _ in range(n_inter):
        advance = timedelta(days=random.randint(14, 56))
        new_date = cur_date + advance

        # Keep intermediate changes safely before end_date
        if new_date >= end_date - timedelta(days=7):
            break

        # Regression (~12%) or advance
        if random.random() < 0.12 and cur_num > 1:
            new_num = cur_num - 1
        else:
            # For closed finals (6/7): intermediate cap is final_num - 1
            # For open finals (1-5): intermediate cap is final_num
            cap = (final_num - 1) if is_closed_final else final_num
            cap = max(cap, 1)
            new_num = min(cur_num + 1, cap)

        if new_num != cur_num:
            changes.append((new_date, STAGE_BY_NUM[cur_num], STAGE_BY_NUM[new_num]))
            cur_num = new_num
        cur_date = new_date

    # Final stage change
    if cur_num != final_num:
        if status == "Open":
            # Last actual change happened before TODAY (not exactly TODAY)
            days_back = random.randint(7, min(90, max(7, (TODAY - cur_date).days - 1)))
            final_date = min(TODAY - timedelta(days=days_back),
                             end_date - timedelta(days=1))
            final_date = max(final_date, cur_date + timedelta(days=1))
        else:
            final_date = end_date   # Won/Lost: final stage set on close date
        changes.append((final_date, STAGE_BY_NUM[cur_num], final_stage))

    return changes


# ── Close Date history ────────────────────────────────────────────────────────

def gen_close_date_changes(
    created: date,
    final_close: date,
    status: str,
    complexity: str,
) -> tuple[date, list[tuple[date, str, str]]]:
    """
    Returns (initial_close, [(change_date, old_value, new_value), ...]).
    Builds a chain of close dates backwards from final_close.
    """
    n = {
        "none":    random.randint(0, 0),
        "simple":  random.randint(0, 1),
        "medium":  random.randint(1, 3),
        "complex": random.randint(2, 5),
    }[complexity]

    if n == 0:
        return final_close, []

    # Max date at which a history record can be stamped
    max_stamp = TODAY - timedelta(days=1)

    # Build chain backwards: chain[-1] = final_close
    chain: list[date] = [final_close]
    for _ in range(n):
        prev = chain[-1]
        if random.random() < 0.80:
            # Prior value was earlier (date was pushed out) — go back 1-3 months
            candidate = add_months(prev, -random.randint(1, 3))
        else:
            # Prior value was later (date was pulled in) — go forward 1-2 months
            candidate = add_months(prev, random.randint(1, 2))

        # Must be after created_date
        if candidate <= created:
            candidate = created + timedelta(days=30)
        chain.append(candidate)

    chain.reverse()          # now: initial → ... → final
    initial_close = chain[0]

    # Generate change timestamps: 2-4 weeks before the OLD close date
    changes: list[tuple[date, str, str]] = []
    min_date = created
    for i in range(n):
        old_close = chain[i]
        new_close = chain[i + 1]

        weeks_before = random.randint(2, 4)
        change_date  = old_close - timedelta(weeks=weeks_before)
        change_date  = max(change_date, min_date + timedelta(days=1))
        change_date  = min(change_date, max_stamp)

        if change_date <= min_date:
            break   # can't fit this change in

        changes.append((change_date, old_close.isoformat(), new_close.isoformat()))
        min_date = change_date

    return initial_close, changes


# ── Amount history ────────────────────────────────────────────────────────────

def gen_amount_changes(
    created: date,
    end_date: date,
    final_amount: int,
    complexity: str,
) -> tuple[int, list[tuple[date, str, str]]]:
    """
    Returns (initial_amount, [(change_date, old_value, new_value), ...]).
    Only ~10 % of opportunities have amount changes.
    """
    if random.random() > 0.10:
        return final_amount, []

    n = {"none": 1, "simple": 1, "medium": 2, "complex": 3}[complexity]

    # Build chain backwards from final_amount
    chain: list[int] = [final_amount]
    for _ in range(n):
        factor   = random.uniform(0.75, 1.25)
        prev_amt = max(1_000, round(chain[-1] * factor / 1_000) * 1_000)
        chain.append(prev_amt)

    chain.reverse()
    initial_amount = chain[0]
    total_days     = max(1, (end_date - created).days)

    changes: list[tuple[date, str, str]] = []
    min_date = created
    for i in range(n):
        # Spread changes evenly across the active window
        segment_start = int(total_days * i / n)
        segment_end   = int(total_days * (i + 1) / n)
        offset        = random.randint(segment_start + 1, max(segment_start + 1, segment_end))
        change_date   = created + timedelta(days=offset)
        change_date   = max(change_date, min_date + timedelta(days=1))
        change_date   = min(change_date, TODAY - timedelta(days=1))

        if change_date <= min_date:
            break

        changes.append((change_date, str(chain[i]), str(chain[i + 1])))
        min_date = change_date

    return initial_amount, changes


# ── Main builder ──────────────────────────────────────────────────────────────

def build_history(opps: list[dict]) -> list[dict]:
    rep_by_account: dict[str, str] = {}
    records: list[dict] = []
    hist_id = 1

    for opp in opps:
        opp_id       = opp["opportunity_id"]
        acct_id      = opp["account_id"]
        created      = date.fromisoformat(opp["created_date"])
        final_close  = date.fromisoformat(opp["close_date"])
        final_amount = int(opp["amount"])
        final_stage  = opp["stage"]
        status       = opp["status"]

        # Consistent rep per account
        if acct_id not in rep_by_account:
            rep_by_account[acct_id] = random.choice(SALES_REPS)
        rep = rep_by_account[acct_id]

        # Active end for generating changes
        end_date   = final_close if status in ("Won", "Lost") else TODAY
        complexity = pick_complexity()

        # Generate histories
        stage_changes = gen_stage_changes(
            created, end_date, final_stage, status, complexity)

        initial_close, close_changes = gen_close_date_changes(
            created, final_close, status, complexity)

        initial_amount, amount_changes = gen_amount_changes(
            created, end_date, final_amount, complexity)

        def row(field, old_val, new_val, chg_date):
            nonlocal hist_id
            r = {
                "history_id":     f"HIST-{hist_id:07d}",
                "opportunity_id": opp_id,
                "field":          field,
                "old_value":      old_val,
                "new_value":      new_val,
                "created_date":   chg_date.isoformat(),
                "created_by":     rep,
            }
            hist_id += 1
            return r

        # ── Creation records (old_value blank) ────────────────────────────
        records.append(row("StageName", "", "1 - Prospecting",       created))
        records.append(row("CloseDate", "", initial_close.isoformat(), created))
        records.append(row("Amount",    "", str(initial_amount),       created))

        # ── Post-creation stage changes ────────────────────────────────────
        for chg_date, old_val, new_val in stage_changes:
            records.append(row("StageName", old_val, new_val, chg_date))

        # ── Post-creation close date changes ──────────────────────────────
        for chg_date, old_val, new_val in close_changes:
            records.append(row("CloseDate", old_val, new_val, chg_date))

        # ── Post-creation amount changes ───────────────────────────────────
        for chg_date, old_val, new_val in amount_changes:
            records.append(row("Amount", old_val, new_val, chg_date))

    return records


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    with open(OPPS_CSV, newline="", encoding="utf-8") as f:
        opps = list(csv.DictReader(f))

    print(f"Loaded {len(opps):,} opportunities …")
    records = build_history(opps)

    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(records)

    # ── Summary stats ─────────────────────────────────────────────────────
    by_field = {}
    creation = 0
    for r in records:
        f = r["field"]
        by_field[f] = by_field.get(f, 0) + 1
        if r["old_value"] == "":
            creation += 1

    print(f"\nHistory records written : {len(records):>8,}")
    print(f"  Creation records       : {creation:>8,}  (old_value blank)")
    print(f"  Change records         : {len(records)-creation:>8,}")
    print(f"\nBy field:")
    for field, cnt in sorted(by_field.items()):
        print(f"  {field:<14} {cnt:>8,}")
    print(f"\nOutput : {OUT_CSV}")


if __name__ == "__main__":
    main()
