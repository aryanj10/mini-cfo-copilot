import pandas as pd
from agent.tools import gross_margin_trend, revenue_vs_budget, ebitda_proxy

def test_gm_trend_runs():
    df = gross_margin_trend(2)
    assert {"period","gm_pct"}.issubset(set(df.columns))
    assert len(df) <= 2

def test_revenue_vs_budget_runs():
    a, b, label = revenue_vs_budget(None)
    assert isinstance(a, float) and isinstance(b, float)
    assert isinstance(label, str)

def test_ebitda_proxy_shape():
    df = ebitda_proxy()
    assert "ebitda_proxy_usd" in df.columns
