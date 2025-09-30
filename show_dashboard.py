#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent.tools import revenue_vs_budget, gross_margin_trend, opex_breakdown, cash_runway_months, ebitda_proxy

def format_currency(value):
    """Format currency values with appropriate suffixes"""
    if abs(value) >= 1e9:
        return f"${value/1e9:.1f}B"
    elif abs(value) >= 1e6:
        return f"${value/1e6:.1f}M" 
    elif abs(value) >= 1e3:
        return f"${value/1e3:.0f}K"
    else:
        return f"${value:,.0f}"

def show_dashboard():
    """Display dashboard data in text format"""
    print("📊 EXECUTIVE FINANCIAL DASHBOARD")
    print("=" * 50)
    
    # Key metrics
    print("\n🎯 KEY PERFORMANCE INDICATORS")
    print("-" * 30)
    
    # Revenue vs Budget
    a, b, label = revenue_vs_budget(None)
    variance = a - b
    variance_pct = (variance / b * 100) if b != 0 else 0
    print(f"💰 Revenue ({label})")
    print(f"   Actual: {format_currency(a)}")
    print(f"   Budget: {format_currency(b)}")
    print(f"   Variance: {format_currency(variance)} ({variance_pct:+.1f}%)")
    
    # Gross Margin
    gm_df = gross_margin_trend(3)
    if len(gm_df) > 0:
        latest_gm = gm_df['gm_pct'].iloc[-1]
        print(f"\n📈 Gross Margin: {latest_gm:.1f}%")
        print("   Last 3 months trend:")
        for _, row in gm_df.iterrows():
            period_str = row['period'].strftime('%B %Y')
            print(f"     {period_str}: {row['gm_pct']:.1f}%")
    
    # EBITDA
    ebitda_df = ebitda_proxy()
    if len(ebitda_df) > 0:
        latest_ebitda = ebitda_df['ebitda_proxy_usd'].iloc[-1]
        avg_ebitda = ebitda_df['ebitda_proxy_usd'].mean()
        print(f"\n💼 EBITDA")
        print(f"   Latest: {format_currency(latest_ebitda)}")
        print(f"   Average: {format_currency(avg_ebitda)}")
    
    # Cash Runway
    cash_usd, runway = cash_runway_months()
    print(f"\n💳 Cash Position")
    print(f"   Current Cash: {format_currency(cash_usd)}")
    if runway == float('inf'):
        print(f"   Runway: ∞ months (Profitable!)")
    else:
        print(f"   Runway: {runway:.1f} months")
    
    # Operating Expenses
    print(f"\n💸 OPERATING EXPENSES BREAKDOWN")
    print("-" * 35)
    opex_df = opex_breakdown(None)
    if len(opex_df) > 0:
        total_opex = opex_df['amount_usd'].sum()
        print(f"Total Opex: {format_currency(total_opex)}")
        account_col = opex_df.columns[0]
        for _, row in opex_df.iterrows():
            percentage = (row['amount_usd'] / total_opex * 100)
            print(f"   {row[account_col]}: {format_currency(row['amount_usd'])} ({percentage:.1f}%)")
    
    print(f"\n📊 CHART ENHANCEMENTS AVAILABLE:")
    print("   ✅ Interactive Plotly charts (when Plotly installed)")
    print("   ✅ Professional styling with corporate color scheme")
    print("   ✅ Trend indicators and variance analysis")
    print("   ✅ Data tables below each chart")
    print("   ✅ Executive-level metrics cards")
    print("   ✅ Responsive design for all screen sizes")
    print("   ✅ Enhanced tooltips and hover information")
    
    print(f"\n🎊 Your Mini CFO Copilot dashboard is ready!")
    print("   Try: 'Show me the dashboard' in the Streamlit app")

if __name__ == "__main__":
    show_dashboard()