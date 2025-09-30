from __future__ import annotations
import pandas as pd
import numpy as np
from dateutil import parser as dtparser
from typing import Tuple, Optional
from pathlib import Path

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"

# ---------------------------
# Flexible time normalization
# ---------------------------
def _ensure_period_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize various time representations to a 'period' month-start Timestamp.

    Fast paths:
    - If a 'period' column exists and at least one value parses, use it (no 60% threshold).
    - Else try common single date-like columns.
    - Else try (year, month) combos and other heuristics.
    """
    df = df.copy()
    cols = [c.lower() for c in df.columns]

    def try_parse_series(s: pd.Series, require_ratio: float = 0.6):
        ts = pd.to_datetime(s, errors="coerce", infer_datetime_format=True)
        ok_ratio = ts.notna().mean()
        if ok_ratio >= require_ratio:
            return ts.dt.to_period("M").dt.to_timestamp()
        return None

    # FAST PATH: honor an existing 'period' column if anything parses
    if "period" in cols:
        s = df[df.columns[cols.index("period")]]
        # accept if ANY non-null parses (robust after filters)
        ts_any = pd.to_datetime(s, errors="coerce", infer_datetime_format=True)
        if ts_any.notna().any():
            df["period"] = ts_any.dt.to_period("M").dt.to_timestamp()
            return df

    # 1) Common single date-ish columns by name (excluding 'period' handled above)
    date_candidates = [c for c in cols if any(k in c for k in [
        "date","month_year","mnth_yr","monthyr","yr_mo","yyyymm","period_start","period_end","time"
    ])]
    for dc in date_candidates:
        parsed = try_parse_series(df[df.columns[cols.index(dc)]])
        if parsed is not None:
            df["period"] = parsed
            return df

    # 2) Separate year & month columns (accept aliases)
    year_names = [n for n in ["year","yr"] if n in cols]
    month_names = [n for n in ["month","mo","mnth","mth"] if n in cols]
    if year_names and month_names:
        ycol = year_names[0]; mcol = month_names[0]
        def to_month_number(x):
            try:
                return int(str(x).strip())
            except Exception:
                return dtparser.parse(str(x)).month
        df["period"] = pd.to_datetime({
            "year": df[df.columns[cols.index(ycol)]].astype(int),
            "month": df[df.columns[cols.index(mcol)]].map(to_month_number),
            "day": 1
        })
        return df

    # 3) Look for a single column with yyyymm/ yyyy-mm / yyyy_mm / yyyy.mm
    for c in df.columns:
        lc = c.lower()
        if any(k in lc for k in ["time","month","date","yyyymm","yrmo"]):
            s = df[c].astype(str).str.replace(r"[^0-9-/_ ]","", regex=True)
            s2 = np.where(s.str.len()==6, s.str[:4]+"-"+s.str[4:6], s)
            parsed = try_parse_series(pd.Series(s2))
            if parsed is not None:
                df["period"] = parsed
                return df

    # 4) Brute-force every column; accept best if any parses (≥60%)
    best = None; best_score = -1.0
    for c in df.columns:
        ts = pd.to_datetime(df[c], errors="coerce", infer_datetime_format=True)
        score = ts.notna().mean()
        if score >= 0.6 and score > best_score:
            best = ts; best_score = score
    if best is not None:
        df["period"] = best.dt.to_period("M").dt.to_timestamp()
        return df

    raise ValueError("Expected a recognizable time column (date/year+month/period). Found columns: " + ", ".join(df.columns))



# ---------------------------
# Flexible schema normalization
# ---------------------------
def _standardize_schema(df: pd.DataFrame) -> pd.DataFrame:
    """
    Try to standardize common FP&A columns to a canonical set:
      - account  (e.g., 'Revenue', 'COGS', 'Opex:Marketing', ...)
      - amount   (numeric)
      - currency (optional)
      - entity   (optional)
    Accepts many aliases: 'Account Name', 'GL Account', 'Category', 'Line Item', etc.
    Also normalizes column names to lowercase snake case.
    """
    df = df.copy()
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

    def pick(candidates):
        for c in candidates:
            if c in df.columns:
                return c
        return None

    account_col = pick([
    "account","account_name","gl_account","line_item","line","category",
    "acct","name","acct_name","account_title","account_category"  # <-- added
])

    amount_col = pick([
        "amount","value","usd","total","amount_usd","net","balance","amt"
    ])
    currency_col = pick([
        "currency","ccy","curr","fx"
    ])
    entity_col = pick([
        "entity","company","business_unit","bu","org","division"
    ])

    # If no amount guess, try to infer the first numeric column (excluding common non-amounts)
    if amount_col is None:
        numeric_candidates = df.select_dtypes(include=[np.number]).columns.tolist()
        numeric_candidates = [c for c in numeric_candidates if c not in {"rate","rate_to_usd"}]
        amount_col = numeric_candidates[0] if numeric_candidates else None

    # Create canonical columns if present
    if account_col and "account" not in df.columns:
        df["account"] = df[account_col]
    if amount_col and "amount" not in df.columns:
        df["amount"] = pd.to_numeric(df[amount_col], errors="coerce")
    if currency_col and "currency" not in df.columns:
        df["currency"] = df[currency_col]
    if entity_col and "entity" not in df.columns:
        df["entity"] = df[entity_col]

    return df


# ---------------------------
# IO helpers
# ---------------------------
def _read_csvs():
    actuals = pd.read_csv(FIXTURES / "actuals.csv")
    budget = pd.read_csv(FIXTURES / "budget.csv")
    fx = pd.read_csv(FIXTURES / "fx.csv")
    cash = pd.read_csv(FIXTURES / "cash.csv")
    return actuals, budget, fx, cash

def load_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    actuals, budget, fx, cash = _read_csvs()
    actuals = _standardize_schema(actuals)
    budget  = _standardize_schema(budget)
    fx      = _standardize_schema(fx)
    cash    = _standardize_schema(cash)

    actuals = _ensure_period_columns(actuals)
    budget  = _ensure_period_columns(budget)
    cash    = _ensure_period_columns(cash)
    fx      = _ensure_period_columns(fx)

    return actuals, budget, fx, cash


# ---------------------------
# FX conversion
# ---------------------------
def _fx_to_usd(df: pd.DataFrame, fx: pd.DataFrame, amount_col: str = "amount") -> pd.DataFrame:
    df = df.copy()
    fx = fx.copy()

    if "currency" not in df.columns:
        df["currency"] = "USD"

    # FX: expect rate_to_usd or rate
    rate_col = "rate_to_usd" if "rate_to_usd" in fx.columns else ("rate" if "rate" in fx.columns else None)
    if rate_col is None:
        raise ValueError("FX CSV must include 'rate_to_usd' or 'rate' column")

    df = _ensure_period_columns(df)
    fx = _ensure_period_columns(fx)

    merged = df.merge(
        fx[["period","currency",rate_col]].rename(columns={rate_col:"rate_to_usd"}),
        on=["period","currency"], how="left"
    )
    merged["rate_to_usd"] = merged["rate_to_usd"].fillna(1.0)

    # Resolve amount column
    if amount_col not in merged.columns:
        # Fallback to any numeric col if 'amount' absent
        numeric_cols = merged.select_dtypes(include=[np.number]).columns.tolist()
        numeric_cols = [c for c in numeric_cols if c not in ("rate_to_usd",)]
        if numeric_cols:
            amount_col = numeric_cols[0]
        else:
            raise ValueError("No amount-like numeric column found for FX conversion.")

    merged["amount_usd"] = pd.to_numeric(merged[amount_col], errors="coerce").fillna(0) * merged["rate_to_usd"]
    return merged


# ---------------------------
# Label helpers (account/entity fallback)
# ---------------------------
def _label_series(df: pd.DataFrame) -> pd.Series:
    """
    Returns the best label column as a Series:
    - Prefer 'account' if present
    - Else use 'entity' if present
    - Else create an empty Series
    """
    if "account" in df.columns:
        return df["account"].astype(str)
    if "entity" in df.columns:
        return df["entity"].astype(str)
    return pd.Series(index=df.index, dtype="object")


def _is_revenue_labels(labels: pd.Series) -> pd.Series:
    s = labels.astype(str).str.lower()
    return s.eq("revenue") | s.str.contains(r"\bsales\b", na=False)


def _is_cogs_labels(labels: pd.Series) -> pd.Series:
    s = labels.astype(str).str.lower()
    return s.eq("cogs") | s.str.contains("cost of goods", na=False)


def _is_opex_labels(labels: pd.Series) -> pd.Series:
    s = labels.astype(str).str.lower()
    return s.str.startswith("opex") | s.str.contains("operating expense", na=False)


# ---------------------------
# Public tools
# ---------------------------
def revenue_vs_budget(month_text: Optional[str]) -> Tuple[float,float,str]:
    actuals, budget, fx, cash = load_data()
    # infer month
    if month_text:
        period = pd.to_datetime(dtparser.parse(month_text).date()).to_period("M").to_timestamp()
    else:
        period = actuals["period"].max()

    # Select rows for revenue (actuals & budget)
    a_labels = _label_series(actuals)
    b_labels = _label_series(budget)
    a_mask = _is_revenue_labels(a_labels)
    b_mask = _is_revenue_labels(b_labels)
    a_rev = _fx_to_usd(actuals[a_mask], fx)
    b_rev = _fx_to_usd(budget[b_mask], fx)

    a = float(a_rev[a_rev["period"].eq(period)]["amount_usd"].sum())
    b = float(b_rev[b_rev["period"].eq(period)]["amount_usd"].sum())
    label = period.strftime("%B %Y")
    return a, b, label


def gross_margin_trend(last_n_months: int = 3) -> pd.DataFrame:
    actuals, budget, fx, cash = load_data()

    labels = _label_series(actuals)
    rev_mask  = _is_revenue_labels(labels)
    cogs_mask = _is_cogs_labels(labels)
    rev  = _fx_to_usd(actuals[rev_mask], fx)
    cogs = _fx_to_usd(actuals[cogs_mask], fx)

    grp = (rev.groupby("period")["amount_usd"].sum().to_frame("revenue_usd")
           .join(cogs.groupby("period")["amount_usd"].sum().to_frame("cogs_usd"), how="outer").fillna(0.0))
    grp["gm_pct"] = np.where(grp["revenue_usd"]==0, np.nan,
                             (grp["revenue_usd"] - grp["cogs_usd"]) / grp["revenue_usd"] * 100.0)
    grp = grp.sort_index().tail(last_n_months).reset_index()
    return grp


def opex_breakdown(month_text: Optional[str]) -> pd.DataFrame:
    actuals, budget, fx, cash = load_data()
    if month_text:
        period = pd.to_datetime(dtparser.parse(month_text).date()).to_period("M").to_timestamp()
    else:
        period = actuals["period"].max()

    op_mask = _is_opex_labels(_label_series(actuals))
    opex = _fx_to_usd(actuals[op_mask], fx)
    df = opex[opex["period"].eq(period)].copy()
    label_col = "account" if "account" in df.columns else ("entity" if "entity" in df.columns else df.columns[0])
    out = df.groupby(label_col)["amount_usd"].sum().reset_index().sort_values("amount_usd", ascending=False)
    return out


def ebitda_proxy() -> pd.DataFrame:
    actuals, budget, fx, cash = load_data()

    labels = _label_series(actuals)
    rev  = _fx_to_usd(actuals[_is_revenue_labels(labels)], fx)
    cogs = _fx_to_usd(actuals[_is_cogs_labels(labels)], fx)
    opex = _fx_to_usd(actuals[_is_opex_labels(labels)], fx)

    grp = pd.DataFrame(index=sorted(actuals["period"].unique()))
    grp.index.name = "period"
    grp["revenue_usd"] = rev.groupby("period")["amount_usd"].sum()
    grp["cogs_usd"] = cogs.groupby("period")["amount_usd"].sum()
    grp["opex_usd"] = opex.groupby("period")["amount_usd"].sum()
    grp = grp.fillna(0.0)
    grp["ebitda_proxy_usd"] = grp["revenue_usd"] - grp["cogs_usd"] - grp["opex_usd"]
    grp = grp.reset_index().sort_values("period")
    return grp


def cash_runway_months() -> Tuple[float, float]:
    actuals, budget, fx, cash = load_data()
    e = ebitda_proxy().set_index("period")
    e["net_burn"] = -e["ebitda_proxy_usd"]
    last3 = e.tail(3)
    avg_burn = float(last3["net_burn"].mean()) if len(last3) else float("nan")

    cash_df = _fx_to_usd(cash, fx)
    latest_cash = cash_df.sort_values("period").tail(1)
    cash_usd = float(latest_cash["amount_usd"].sum())

    if not np.isfinite(avg_burn) or avg_burn <= 0:
        runway = float("inf")
    else:
        runway = cash_usd / avg_burn
    return cash_usd, runway


def monthly_comparison() -> pd.DataFrame:
    """Compare latest month vs previous month across key metrics"""
    actuals, budget, fx, cash = load_data()
    
    # Get last 2 months of data
    latest_periods = sorted(actuals["period"].unique())[-2:]
    if len(latest_periods) < 2:
        return pd.DataFrame()
    
    results = []
    for period in latest_periods:
        period_data = {}
        period_data['period'] = period
        
        # Revenue
        labels = _label_series(actuals)
        rev_mask = _is_revenue_labels(labels)
        rev_data = _fx_to_usd(actuals[rev_mask], fx)
        period_data['revenue'] = float(rev_data[rev_data["period"].eq(period)]["amount_usd"].sum())
        
        # COGS
        cogs_mask = _is_cogs_labels(labels)
        cogs_data = _fx_to_usd(actuals[cogs_mask], fx)
        period_data['cogs'] = float(cogs_data[cogs_data["period"].eq(period)]["amount_usd"].sum())
        
        # Opex
        opex_mask = _is_opex_labels(labels)
        opex_data = _fx_to_usd(actuals[opex_mask], fx)
        period_data['opex'] = float(opex_data[opex_data["period"].eq(period)]["amount_usd"].sum())
        
        # Gross Margin
        if period_data['revenue'] > 0:
            period_data['gross_margin_pct'] = (period_data['revenue'] - period_data['cogs']) / period_data['revenue'] * 100
        else:
            period_data['gross_margin_pct'] = 0
            
        # EBITDA
        period_data['ebitda'] = period_data['revenue'] - period_data['cogs'] - period_data['opex']
        
        results.append(period_data)
    
    df = pd.DataFrame(results)
    
    # Calculate month-over-month changes
    if len(df) == 2:
        df.loc[1, 'revenue_change'] = ((df.loc[1, 'revenue'] - df.loc[0, 'revenue']) / df.loc[0, 'revenue'] * 100) if df.loc[0, 'revenue'] != 0 else 0
        df.loc[1, 'opex_change'] = ((df.loc[1, 'opex'] - df.loc[0, 'opex']) / df.loc[0, 'opex'] * 100) if df.loc[0, 'opex'] != 0 else 0
        df.loc[1, 'ebitda_change'] = ((df.loc[1, 'ebitda'] - df.loc[0, 'ebitda']) / df.loc[0, 'ebitda'] * 100) if df.loc[0, 'ebitda'] != 0 else 0
        df.loc[1, 'gm_change'] = df.loc[1, 'gross_margin_pct'] - df.loc[0, 'gross_margin_pct']
    
    return df


def yearly_comparison() -> pd.DataFrame:
    """Compare current year vs previous year by month"""
    actuals, budget, fx, cash = load_data()
    
    # Group by year and month
    actuals['year'] = actuals['period'].dt.year
    actuals['month'] = actuals['period'].dt.month
    
    current_year = actuals['year'].max()
    prev_year = current_year - 1
    
    # Filter for current and previous year
    current_data = actuals[actuals['year'] == current_year]
    prev_data = actuals[actuals['year'] == prev_year]
    
    if len(prev_data) == 0:
        return pd.DataFrame()
    
    # Calculate revenue by month for both years
    labels = _label_series(actuals)
    rev_mask = _is_revenue_labels(labels)
    
    results = []
    for month in range(1, 13):
        row = {'month': month, 'month_name': pd.Timestamp(2025, month, 1).strftime('%B')}
        
        # Current year
        curr_month_data = current_data[(current_data['month'] == month) & rev_mask]
        if len(curr_month_data) > 0:
            curr_rev = _fx_to_usd(curr_month_data, fx)["amount_usd"].sum()
            row[f'revenue_{current_year}'] = float(curr_rev)
        else:
            row[f'revenue_{current_year}'] = 0
        
        # Previous year
        prev_month_data = prev_data[(prev_data['month'] == month) & rev_mask]
        if len(prev_month_data) > 0:
            prev_rev = _fx_to_usd(prev_month_data, fx)["amount_usd"].sum()
            row[f'revenue_{prev_year}'] = float(prev_rev)
        else:
            row[f'revenue_{prev_year}'] = 0
        
        # YoY Growth
        if row[f'revenue_{prev_year}'] > 0:
            row['yoy_growth_pct'] = ((row[f'revenue_{current_year}'] - row[f'revenue_{prev_year}']) / 
                                   row[f'revenue_{prev_year}'] * 100)
        else:
            row['yoy_growth_pct'] = 0
        
        results.append(row)
    
    return pd.DataFrame(results)


def pnl_statement(month_text: Optional[str]) -> pd.DataFrame:
    """Generate P&L statement for a specific month"""
    actuals, budget, fx, cash = load_data()
    
    if month_text:
        period = pd.to_datetime(dtparser.parse(month_text).date()).to_period("M").to_timestamp()
    else:
        period = actuals["period"].max()
    
    labels = _label_series(actuals)
    period_data = actuals[actuals["period"].eq(period)]
    
    # Revenue
    rev_mask = _is_revenue_labels(labels)
    revenue = _fx_to_usd(period_data[rev_mask], fx)["amount_usd"].sum()
    
    # COGS
    cogs_mask = _is_cogs_labels(labels)
    cogs = _fx_to_usd(period_data[cogs_mask], fx)["amount_usd"].sum()
    
    # Gross Profit
    gross_profit = revenue - cogs
    gross_margin_pct = (gross_profit / revenue * 100) if revenue > 0 else 0
    
    # Operating Expenses (detailed)
    opex_mask = _is_opex_labels(labels)
    opex_data = _fx_to_usd(period_data[opex_mask], fx)
    
    # Group opex by category
    if len(opex_data) > 0:
        account_col = "account" if "account" in opex_data.columns else ("entity" if "entity" in opex_data.columns else opex_data.columns[0])
        opex_by_category = opex_data.groupby(account_col)["amount_usd"].sum().to_dict()
    else:
        opex_by_category = {}
    
    total_opex = sum(opex_by_category.values())
    
    # EBITDA
    ebitda = gross_profit - total_opex
    
    # Create P&L structure
    pnl_data = [
        {"line_item": "Revenue", "amount": revenue, "type": "revenue"},
        {"line_item": "Cost of Goods Sold (COGS)", "amount": -cogs, "type": "cogs"},
        {"line_item": "Gross Profit", "amount": gross_profit, "type": "gross_profit"},
        {"line_item": f"Gross Margin %", "amount": gross_margin_pct, "type": "percentage"},
    ]
    
    # Add opex line items
    for category, amount in opex_by_category.items():
        pnl_data.append({"line_item": category, "amount": -amount, "type": "opex"})
    
    pnl_data.extend([
        {"line_item": "Total Operating Expenses", "amount": -total_opex, "type": "total_opex"},
        {"line_item": "EBITDA", "amount": ebitda, "type": "ebitda"}
    ])
    
    df = pd.DataFrame(pnl_data)
    df['period'] = period.strftime('%B %Y')
    
    return df


def budget_variance_analysis(month_text: Optional[str]) -> pd.DataFrame:
    """Comprehensive budget variance analysis"""
    actuals, budget, fx, cash = load_data()
    
    if month_text:
        period = pd.to_datetime(dtparser.parse(month_text).date()).to_period("M").to_timestamp()
    else:
        period = actuals["period"].max()
    
    labels_a = _label_series(actuals)
    labels_b = _label_series(budget)
    
    results = []
    
    # Revenue variance
    rev_mask_a = _is_revenue_labels(labels_a)
    rev_mask_b = _is_revenue_labels(labels_b)
    actual_rev = _fx_to_usd(actuals[rev_mask_a], fx)
    budget_rev = _fx_to_usd(budget[rev_mask_b], fx)
    
    a_rev = float(actual_rev[actual_rev["period"].eq(period)]["amount_usd"].sum())
    b_rev = float(budget_rev[budget_rev["period"].eq(period)]["amount_usd"].sum())
    
    results.append({
        "category": "Revenue",
        "actual": a_rev,
        "budget": b_rev,
        "variance": a_rev - b_rev,
        "variance_pct": ((a_rev - b_rev) / b_rev * 100) if b_rev != 0 else 0
    })
    
    # COGS variance
    cogs_mask_a = _is_cogs_labels(labels_a)
    cogs_mask_b = _is_cogs_labels(labels_b)
    actual_cogs = _fx_to_usd(actuals[cogs_mask_a], fx)
    budget_cogs = _fx_to_usd(budget[cogs_mask_b], fx)
    
    a_cogs = float(actual_cogs[actual_cogs["period"].eq(period)]["amount_usd"].sum())
    b_cogs = float(budget_cogs[budget_cogs["period"].eq(period)]["amount_usd"].sum())
    
    results.append({
        "category": "COGS",
        "actual": a_cogs,
        "budget": b_cogs,
        "variance": a_cogs - b_cogs,
        "variance_pct": ((a_cogs - b_cogs) / b_cogs * 100) if b_cogs != 0 else 0
    })
    
    # Opex variance
    opex_mask_a = _is_opex_labels(labels_a)
    opex_mask_b = _is_opex_labels(labels_b)
    actual_opex = _fx_to_usd(actuals[opex_mask_a], fx)
    budget_opex = _fx_to_usd(budget[opex_mask_b], fx)
    
    a_opex = float(actual_opex[actual_opex["period"].eq(period)]["amount_usd"].sum())
    b_opex = float(budget_opex[budget_opex["period"].eq(period)]["amount_usd"].sum())
    
    results.append({
        "category": "Operating Expenses",
        "actual": a_opex,
        "budget": b_opex,
        "variance": a_opex - b_opex,
        "variance_pct": ((a_opex - b_opex) / b_opex * 100) if b_opex != 0 else 0
    })
    
    # Gross Profit
    gross_profit_actual = a_rev - a_cogs
    gross_profit_budget = b_rev - b_cogs
    
    results.append({
        "category": "Gross Profit",
        "actual": gross_profit_actual,
        "budget": gross_profit_budget,
        "variance": gross_profit_actual - gross_profit_budget,
        "variance_pct": ((gross_profit_actual - gross_profit_budget) / gross_profit_budget * 100) if gross_profit_budget != 0 else 0
    })
    
    # EBITDA
    ebitda_actual = gross_profit_actual - a_opex
    ebitda_budget = gross_profit_budget - b_opex
    
    results.append({
        "category": "EBITDA",
        "actual": ebitda_actual,
        "budget": ebitda_budget,
        "variance": ebitda_actual - ebitda_budget,
        "variance_pct": ((ebitda_actual - ebitda_budget) / ebitda_budget * 100) if ebitda_budget != 0 else 0
    })
    
    df = pd.DataFrame(results)
    df['period'] = period.strftime('%B %Y')
    return df


def burn_rate_analysis() -> pd.DataFrame:
    """Analyze monthly burn rate trends"""
    actuals, budget, fx, cash = load_data()
    
    # Calculate net burn rate as expenses minus revenue
    labels = _label_series(actuals)
    
    # Get Revenue
    rev_mask = _is_revenue_labels(labels)
    rev_data = _fx_to_usd(actuals[rev_mask], fx)
    monthly_rev = rev_data.groupby("period")["amount_usd"].sum().reset_index()
    monthly_rev.columns = ['period', 'revenue']
    
    # Get COGS
    cogs_mask = _is_cogs_labels(labels)
    cogs_data = _fx_to_usd(actuals[cogs_mask], fx)
    monthly_cogs = cogs_data.groupby("period")["amount_usd"].sum().reset_index()
    monthly_cogs.columns = ['period', 'cogs']
    
    # Get OpEx
    opex_mask = _is_opex_labels(labels)
    opex_data = _fx_to_usd(actuals[opex_mask], fx)
    monthly_opex = opex_data.groupby("period")["amount_usd"].sum().reset_index()
    monthly_opex.columns = ['period', 'opex']
    
    # Merge all data
    burn_df = monthly_rev.merge(monthly_cogs, on="period", how="outer").fillna(0)
    burn_df = burn_df.merge(monthly_opex, on="period", how="outer").fillna(0)
    
    # Calculate net burn: total expenses - revenue
    burn_df['total_expenses'] = burn_df['cogs'] + burn_df['opex']
    burn_df['net_burn'] = burn_df['total_expenses'] - burn_df['revenue']
    
    # Only positive net burn (when expenses > revenue)
    burn_df['burn_rate'] = burn_df['net_burn'].where(burn_df['net_burn'] > 0, 0)
    
    # Calculate rolling average of net burn
    burn_df['burn_rate_3m_avg'] = burn_df['burn_rate'].rolling(window=3, min_periods=1).mean()
    
    # Get cash data
    cash_df = _fx_to_usd(cash, fx)
    cash_monthly = cash_df.groupby("period")["amount_usd"].sum().reset_index()
    
    # Merge with burn data
    merged = burn_df.merge(cash_monthly, on="period", how="left")
    
    # Calculate runway: cash ÷ avg monthly net burn (last 3 months)
    # If net burn is 0 or negative (profitable), runway is infinite
    merged['months_runway'] = merged.apply(
        lambda row: row['amount_usd'] / row['burn_rate_3m_avg'] 
        if row['burn_rate_3m_avg'] > 0 
        else float('inf'), axis=1
    )
    # Don't replace inf with nan - inf means unlimited runway
    merged['months_runway'] = merged['months_runway'].replace([-np.inf], np.nan)
    
    return merged.tail(12)  # Last 12 months


def revenue_growth_analysis() -> pd.DataFrame:
    """Analyze revenue growth trends"""
    actuals, budget, fx, cash = load_data()
    
    labels = _label_series(actuals)
    rev_mask = _is_revenue_labels(labels)
    rev_data = _fx_to_usd(actuals[rev_mask], fx)
    
    # Monthly revenue
    monthly_rev = rev_data.groupby("period")["amount_usd"].sum().reset_index()
    monthly_rev = monthly_rev.sort_values("period")
    
    # Calculate growth rates
    monthly_rev['prev_month_revenue'] = monthly_rev['amount_usd'].shift(1)
    monthly_rev['mom_growth_pct'] = ((monthly_rev['amount_usd'] - monthly_rev['prev_month_revenue']) / 
                                   monthly_rev['prev_month_revenue'] * 100)
    
    # Year-over-year growth
    monthly_rev['year'] = monthly_rev['period'].dt.year
    monthly_rev['month'] = monthly_rev['period'].dt.month
    
    # Calculate YoY growth
    monthly_rev['yoy_growth_pct'] = monthly_rev.groupby('month')['amount_usd'].pct_change(periods=1) * 100
    
    # 3-month rolling average
    monthly_rev['revenue_3m_avg'] = monthly_rev['amount_usd'].rolling(window=3, min_periods=1).mean()
    monthly_rev['growth_3m_avg'] = monthly_rev['mom_growth_pct'].rolling(window=3, min_periods=1).mean()
    
    return monthly_rev.tail(12)


def top_expenses_analysis() -> pd.DataFrame:
    """Identify top expense categories across all time"""
    actuals, budget, fx, cash = load_data()
    
    # Get all expense data (COGS + Opex)
    labels = _label_series(actuals)
    cogs_mask = _is_cogs_labels(labels)
    opex_mask = _is_opex_labels(labels)
    
    expense_data = actuals[cogs_mask | opex_mask]
    expense_usd = _fx_to_usd(expense_data, fx)
    
    # Group by account/category
    account_col = "account" if "account" in expense_usd.columns else ("entity" if "entity" in expense_usd.columns else expense_usd.columns[0])
    
    top_expenses = (expense_usd.groupby(account_col)["amount_usd"]
                   .agg(['sum', 'mean', 'count'])
                   .round(2)
                   .sort_values('sum', ascending=False)
                   .reset_index())
    
    top_expenses.columns = ['category', 'total_amount', 'avg_monthly', 'months_count']
    
    # Calculate percentage of total expenses
    total_all_expenses = top_expenses['total_amount'].sum()
    top_expenses['percentage_of_total'] = (top_expenses['total_amount'] / total_all_expenses * 100).round(1)
    
    return top_expenses


def quarterly_summary() -> pd.DataFrame:
    """Generate quarterly financial summary"""
    actuals, budget, fx, cash = load_data()
    
    # Add quarter information
    actuals['quarter'] = actuals['period'].dt.to_period('Q')
    
    labels = _label_series(actuals)
    
    quarterly_data = []
    for quarter in sorted(actuals['quarter'].unique()):
        quarter_actuals = actuals[actuals['quarter'] == quarter]
        
        # Revenue
        rev_mask = _is_revenue_labels(labels)
        rev_data = _fx_to_usd(quarter_actuals[rev_mask], fx)
        revenue = rev_data["amount_usd"].sum()
        
        # COGS
        cogs_mask = _is_cogs_labels(labels)
        cogs_data = _fx_to_usd(quarter_actuals[cogs_mask], fx)
        cogs = cogs_data["amount_usd"].sum()
        
        # Opex
        opex_mask = _is_opex_labels(labels)
        opex_data = _fx_to_usd(quarter_actuals[opex_mask], fx)
        opex = opex_data["amount_usd"].sum()
        
        quarterly_data.append({
            'quarter': str(quarter),
            'revenue': revenue,
            'cogs': cogs,
            'opex': opex,
            'gross_profit': revenue - cogs,
            'gross_margin_pct': ((revenue - cogs) / revenue * 100) if revenue > 0 else 0,
            'ebitda': revenue - cogs - opex,
            'ebitda_margin_pct': ((revenue - cogs - opex) / revenue * 100) if revenue > 0 else 0
        })
    
    df = pd.DataFrame(quarterly_data)
    
    # Calculate quarter-over-quarter growth
    if len(df) > 1:
        df['revenue_qoq_growth'] = df['revenue'].pct_change() * 100
        df['ebitda_qoq_growth'] = df['ebitda'].pct_change() * 100
    
    return df
