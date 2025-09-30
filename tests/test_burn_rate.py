import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.tools import burn_rate_analysis
import pytest
import pandas as pd

def test_burn_rate_analysis():
    """Test burn rate analysis functionality"""
    result = burn_rate_analysis()
    
    # Verify result is a DataFrame
    assert isinstance(result, pd.DataFrame), "burn_rate_analysis should return a DataFrame"
    
    # Verify some expected columns exist (based on actual output)
    expected_columns = ['period', 'revenue', 'total_expenses', 'net_burn']
    for col in expected_columns:
        assert col in result.columns, f"Result should have {col} column"
    
    # Verify data integrity
    assert len(result) > 0, "Should have burn rate data"
    
    # Verify net burn calculation (net_burn = total_expenses - revenue)
    for _, row in result.iterrows():
        expected_net_burn = row['total_expenses'] - row['revenue']
        assert abs(row['net_burn'] - expected_net_burn) < 0.01, f"Net burn calculation should be correct: {row['total_expenses']} - {row['revenue']} = {expected_net_burn}, got {row['net_burn']}"

def test_burn_rate_profitable_company():
    """Test that burn rate handles profitable companies correctly"""
    result = burn_rate_analysis()
    
    # For a profitable company, net burn should be negative or zero
    # (meaning they're generating cash, not burning it)
    profitable_months = result[result['net_burn'] <= 0]
    
    # We expect this company to be profitable in most/all months
    assert len(profitable_months) > 0, "Should have some profitable months where net burn is negative or zero"