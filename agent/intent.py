from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Optional

@dataclass
class Intent:
    name: str
    period: Optional[str] = None           # e.g., "June 2025", "last 3 months"
    extra: Optional[str] = None

def classify_intent(q: str) -> Intent:
    ql = q.lower().strip()

    # cash runway
    if "cash runway" in ql or ("runway" in ql and "cash" in ql):
        return Intent(name="cash_runway")

    # revenue vs budget (in usd)
    if "revenue" in ql and "budget" in ql:
        # extract a month + year like "June 2025"
        m = re.search(r"""(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s+\d{4}""", ql)
        if m:
            return Intent(name="revenue_vs_budget", period=m.group(0))
        return Intent(name="revenue_vs_budget", period=None)

    # gross margin trend
    if "gross margin" in ql and ("trend" in ql or "last" in ql):
        m3 = re.search(r"last\s+(\d+)\s+months?", ql)
        if m3:
            return Intent(name="gm_trend", period=f"last {m3.group(1)} months")
        return Intent(name="gm_trend", period="last 3 months")

    # EBITDA analysis
    if "ebitda" in ql or "earnings" in ql:
        if "trend" in ql or "analysis" in ql:
            return Intent(name="ebitda_trend")
        return Intent(name="ebitda")

    # Monthly performance comparison
    if "month over month" in ql or "mom" in ql or "monthly comparison" in ql:
        return Intent(name="monthly_comparison")

    # Year over year analysis
    if "year over year" in ql or "yoy" in ql or "yearly comparison" in ql:
        return Intent(name="yearly_comparison")

    # Profit and loss / P&L
    if ("profit and loss" in ql or "p&l" in ql or "income statement" in ql) and not "trend" in ql:
        m = re.search(r"""(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s+\d{4}""", ql)
        if m:
            return Intent(name="pnl_statement", period=m.group(0))
        return Intent(name="pnl_statement", period=None)

    # Budget variance analysis
    if ("variance" in ql or "vs budget" in ql) and not "revenue" in ql:
        m = re.search(r"""(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s+\d{4}""", ql)
        if m:
            return Intent(name="budget_variance", period=m.group(0))
        return Intent(name="budget_variance", period=None)

    # Cost structure analysis
    if "cost structure" in ql or "cost breakdown" in ql or "cost analysis" in ql:
        return Intent(name="cost_structure")

    # Quarterly trends
    if "quarterly" in ql or "quarter" in ql:
        if "trend" in ql or "comparison" in ql:
            return Intent(name="quarterly_trends")
        return Intent(name="quarterly_summary")

    # Burn rate analysis
    if "burn rate" in ql or "monthly burn" in ql or "spending rate" in ql:
        return Intent(name="burn_rate")

    # Financial health / metrics
    if ("financial health" in ql or "key metrics" in ql or "kpi" in ql or 
        "financial summary" in ql or "performance metrics" in ql):
        return Intent(name="financial_health")

    # Top expenses
    if "top expenses" in ql or "biggest costs" in ql or "largest expenses" in ql:
        return Intent(name="top_expenses")

    # Revenue growth
    if "revenue growth" in ql or "growth rate" in ql or "revenue trend" in ql:
        return Intent(name="revenue_growth")

    # opex breakdown
    if ("opex" in ql or "operating expense" in ql) and ("breakdown" in ql or "by category" in ql):
        m = re.search(r"""(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s+\d{4}""", ql)
        if m:
            return Intent(name="opex_breakdown", period=m.group(0))
        return Intent(name="opex_breakdown", period=None)

    # comprehensive dashboard
    if "dashboard" in ql or "overview" in ql or "summary" in ql:
        return Intent(name="dashboard")

    # fallback revenue
    if "revenue" in ql:
        return Intent(name="revenue")
    return Intent(name="unknown")
