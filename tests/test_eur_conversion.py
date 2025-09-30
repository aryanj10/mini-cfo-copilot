import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.tools import load_data, _fx_to_usd
import pandas as pd
import pytest

def test_eur_to_usd_conversion():
    """Test EUR to USD conversion functionality"""
    # Load the data
    actuals, budget, fx, cash = load_data()
    
    # Verify we have EUR data
    eur_data = actuals[actuals['currency'] == 'EUR']
    assert len(eur_data) > 0, "Should have EUR data in actuals"
    
    # Verify we have FX rates for EUR
    eur_fx = fx[fx['currency'] == 'EUR']
    assert len(eur_fx) > 0, "Should have EUR FX rates"
    
    # Test conversion
    sample_eur = eur_data.head(3)
    converted = _fx_to_usd(sample_eur, fx)
    
    # Verify conversion worked
    assert 'amount_usd' in converted.columns, "Should have amount_usd column after conversion"
    assert 'rate_to_usd' in converted.columns, "Should have rate_to_usd column"
    
    # Verify conversion math (EUR amount * rate = USD amount)
    for _, row in converted.iterrows():
        expected_usd = row['amount'] * row['rate_to_usd']
        assert abs(row['amount_usd'] - expected_usd) < 0.01, f"Conversion math should be correct: {row['amount']} * {row['rate_to_usd']} = {expected_usd}, got {row['amount_usd']}"
    
    # Test specific known conversion (EUR 95,000 × 1.085 = USD 103,075)
    jan_2023_eur = eur_data[(eur_data['month'] == '2023-01') & (eur_data['account'] == 'Revenue')]
    if len(jan_2023_eur) > 0:
        jan_converted = _fx_to_usd(jan_2023_eur, fx)
        eur_amount = jan_2023_eur['amount'].iloc[0]
        usd_amount = jan_converted['amount_usd'].iloc[0]
        fx_rate = jan_converted['rate_to_usd'].iloc[0]
        expected = eur_amount * fx_rate
        assert abs(usd_amount - expected) < 0.01, f"EUR {eur_amount} should convert correctly using rate {fx_rate}"
    
    # Verification output for debugging
    print(f"\nVerification:")
    for _, row in converted.iterrows():
        original_eur = row['amount']
        fx_rate = row['rate_to_usd']
        converted_usd = row['amount_usd']
        expected_usd = original_eur * fx_rate
        print(f"EUR {original_eur} × {fx_rate} = USD {expected_usd:.2f} (got {converted_usd:.2f})")
    print(f"EUR {original_eur:,.0f} * {fx_rate} = USD {expected_usd:,.0f} (got {converted_usd:,.0f}) ✓" if abs(expected_usd - converted_usd) < 0.01 else f"EUR {original_eur} * {fx_rate} = USD {expected_usd} (got {converted_usd}) ❌")