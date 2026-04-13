#!/usr/bin/env python3
"""
generate_opportunities.py
Generates 3,000 mock Opportunity records for the Opportunity Field History case study.
Run from the repo root or from the case-studies/opportunity-field-history/ directory.
Output: data/raw/opportunities.csv
"""

import csv
import math
import os
import random
from datetime import date, timedelta

random.seed(7)

HERE         = os.path.dirname(os.path.abspath(__file__))
ACCOUNTS_CSV = os.path.join(HERE, "data", "raw", "accounts.csv")
OUTPUT_CSV   = os.path.join(HERE, "data", "raw", "opportunities.csv")

TODAY        = date(2026, 4, 12)   # project reference date
START_DATE   = date(2021, 1,  1)   # earliest created date
END_CREATED  = date(2026, 3, 31)   # latest created date
MAX_CLOSE    = date(2026, 8, 31)   # hard cap on close date

NUM_OPPS     = 3_000

# ── Stage catalogue ───────────────────────────────────────────────────────────
# (stage label, probability %)
STAGE_PROB = {
    "1 - Prospecting":  10,
    "2 - Scoping":      15,
    "3 - Engaged":      25,
    "4 - Proposal":     60,
    "5 - Negotiation":  80,
    "6 - Closed Won":  100,
    "7 - Closed Lost":   0,
}

# Open-opp stage distribution (earlier stages are more common)
OPEN_STAGES   = ["1 - Prospecting", "2 - Scoping", "3 - Engaged",
                  "4 - Proposal", "5 - Negotiation"]
OPEN_WEIGHTS  = [5, 4, 3, 2, 1]   # ~33 / 27 / 20 / 13 / 7 %

# ── Opportunity name ingredients ──────────────────────────────────────────────
PRODUCTS = [
    "ERP Implementation", "CRM Rollout", "Data Analytics Platform",
    "Cloud Migration", "Security Assessment", "Network Infrastructure Upgrade",
    "Digital Transformation Initiative", "Training & Enablement Program",
    "Managed Services Contract", "Professional Services Engagement",
    "Business Intelligence Suite", "Systems Integration", "Compliance Program",
    "Infrastructure Refresh", "Workforce Optimization Platform",
]


# ── Helpers ───────────────────────────────────────────────────────────────────

def rand_date(start: date, end: date) -> date:
    return start + timedelta(days=random.randint(0, (end - start).days))


def account_weight(acct: dict) -> float:
    """Log-scale weight so accounts >$100 M earn proportionally more opps."""
    rev_m = max(1.0, acct["annual_revenue"] / 1_000_000)
    return math.log10(rev_m)


def load_accounts() -> list[dict]:
    accounts = []
    with open(ACCOUNTS_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            row["annual_revenue"] = int(row["annual_revenue"])
            accounts.append(row)
    return accounts


# ── Core generator ────────────────────────────────────────────────────────────

def build_opportunities(accounts: list[dict]) -> list[dict]:
    weights = [account_weight(a) for a in accounts]

    opps = []
    for i in range(1, NUM_OPPS + 1):

        # Pick account — higher revenue → higher chance of selection
        acct = random.choices(accounts, weights=weights, k=1)[0]
        rev  = acct["annual_revenue"]

        # Amount: 0.001 % – 0.1 % of annual revenue, rounded to nearest $1 k
        pct    = random.uniform(0.00001, 0.001)
        amount = max(1_000, round(rev * pct / 1_000) * 1_000)

        # Created date: Jan 1 2021 – Mar 31 2026
        created = rand_date(START_DATE, END_CREATED)

        # Close date: +15 d to +24 months (730 d), hard cap Aug 31 2026
        latest_offset = min(730, (MAX_CLOSE - created).days)
        close_date    = created + timedelta(days=random.randint(15, latest_offset))

        # Status & Stage
        if close_date < TODAY:
            # Closed — 30 % Won, 70 % Lost
            if random.random() < 0.30:
                status = "Won"
                stage  = "6 - Closed Won"
            else:
                status = "Lost"
                stage  = "7 - Closed Lost"
        else:
            status = "Open"
            stage  = random.choices(OPEN_STAGES, weights=OPEN_WEIGHTS, k=1)[0]

        probability = STAGE_PROB[stage]
        product     = random.choice(PRODUCTS)
        opp_name    = f"{acct['account_name']} \u2013 {product}"

        opps.append({
            "opportunity_id":   f"OPP-{i:05d}",
            "opportunity_name": opp_name,
            "account_id":       acct["account_id"],
            "amount":           amount,
            "created_date":     created.isoformat(),
            "close_date":       close_date.isoformat(),
            "status":           status,
            "stage":            stage,
            "probability":      probability,
        })

    return opps


# ── Main ──────────────────────────────────────────────────────────────────────

FIELDNAMES = [
    "opportunity_id", "opportunity_name", "account_id",
    "amount", "created_date", "close_date",
    "status", "stage", "probability",
]


def main() -> None:
    accounts = load_accounts()
    opps     = build_opportunities(accounts)

    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(opps)

    won   = sum(1 for o in opps if o["status"] == "Won")
    lost  = sum(1 for o in opps if o["status"] == "Lost")
    open_ = sum(1 for o in opps if o["status"] == "Open")

    print(f"Opportunities written : {len(opps):>5,}")
    print(f"  Won               : {won:>5,}  ({won  / len(opps) * 100:.1f} %)")
    print(f"  Lost              : {lost:>5,}  ({lost / len(opps) * 100:.1f} %)")
    print(f"  Open              : {open_:>5,}  ({open_/ len(opps) * 100:.1f} %)")
    print()
    print(f"Amount range  : ${min(o['amount'] for o in opps):>12,.0f}"
          f"  –  ${max(o['amount'] for o in opps):>12,.0f}")
    print(f"Output        : {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
