import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.tools import load_data, _fx_to_usd, _label_series
import pandas as pd
import pytest

def test_monthly_aggregation():
    """Test that monthly aggregation works correctly across currencies"""
    actuals, budget, fx, cash = load_data()
    
    # Test January 2023 aggregation specifically
    jan_2023 = actuals[actuals['month'] == '2023-01']
    
    # Separate USD and EUR for January 2023
    jan_usd = jan_2023[jan_2023['currency'] == 'USD']
    jan_eur = jan_2023[jan_2023['currency'] == 'EUR']
    
    assert len(jan_usd) > 0, "Should have USD data for Jan 2023"
    assert len(jan_eur) > 0, "Should have EUR data for Jan 2023"
    
    # Test USD amounts (use actual total from data)
    usd_total = jan_usd['amount'].sum()
    assert usd_total > 500000, f"USD total should be substantial, got {usd_total}"
    
    # Test EUR conversion
    jan_eur_converted = _fx_to_usd(jan_eur, fx)
    eur_total_usd = jan_eur_converted['amount_usd'].sum()
    assert eur_total_usd > 100000, f"EUR converted to USD should be substantial, got {eur_total_usd}"
    
    # Test combined total
    combined_total = usd_total + eur_total_usd
    assert combined_total > 600000, f"Combined total should be substantial, got {combined_total}"

def test_aggregation_by_account_category():
    """Test aggregation by account category"""
    actuals, budget, fx, cash = load_data()
    
    # Test aggregation for revenue
    revenue_data = actuals[actuals['account_category'] == 'Revenue']
    
    # Group by month and sum amounts (before FX conversion)
    revenue_by_month = revenue_data.groupby(['month', 'currency'])['amount'].sum().reset_index()
    
    # Verify we have data for multiple months and currencies
    assert len(revenue_by_month) > 0, "Should have revenue data by month"
    
    # Check that we have both USD and EUR revenue
    currencies = revenue_by_month['currency'].unique()
    assert 'USD' in currencies, "Should have USD revenue"
    assert 'EUR' in currencies, "Should have EUR revenue"

def test_period_aggregation():
    """Test that period-based aggregation works correctly"""
    actuals, budget, fx, cash = load_data()
    
    # Convert all data to USD first
    actuals_usd = _fx_to_usd(actuals, fx)
    
    # Group by period and account category
    period_aggregation = actuals_usd.groupby(['period', 'account_category'])['amount_usd'].sum().reset_index()
    
    # Verify we have data
    assert len(period_aggregation) > 0, "Should have period aggregation data"
    
    # Verify we have multiple periods
    periods = period_aggregation['period'].unique()
    assert len(periods) > 1, "Should have multiple periods"
    
    # Verify we have revenue and COGS data
    accounts = period_aggregation['account_category'].unique()
    assert 'Revenue' in accounts, "Should have Revenue data"
    assert 'COGS' in accounts, "Should have COGS data"