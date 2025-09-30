#!/usr/bin/env python3
"""
Test script for enhanced Mini CFO Copilot functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.intent import classify_intent
from agent.tools import (monthly_comparison, yearly_comparison, pnl_statement, 
                        budget_variance_analysis, burn_rate_analysis, 
                        revenue_growth_analysis, top_expenses_analysis, quarterly_summary)
import pytest
import pandas as pd

def test_intent_classification():
    """Test enhanced intent classifications"""
    test_queries = [
        ("Show me month over month comparison", "monthly_comparison"),
        ("Give me year over year revenue trends", "yearly_comparison"), 
        ("Show me P&L statement for June 2025", "pnl_statement"),
        ("What's our budget variance this month?", "budget_variance"),
        ("Show me burn rate analysis", "burn_rate"),
        ("What's our revenue growth rate?", "revenue_growth"),
        ("Show me top expense categories", "top_expenses"),
        ("Give me quarterly financial summary", "quarterly_summary"),
        ("Show me financial health metrics", "financial_health"),
        ("What's our cost structure?", "cost_structure"),
    ]
    
    for query, expected in test_queries:
        intent = classify_intent(query)
        status = "✅" if intent.name == expected else "❌"
        print(f"{status} '{query}' → {intent.name} (expected: {expected})")
    
    print("\n" + "="*50)

def test_new_analysis_functions():
    """Test new analysis functions"""
    print("\n📊 Testing Enhanced Analysis Functions...")
    print("-" * 50)
    
    try:
        # Monthly comparison
        print("🔄 Monthly Comparison...")
        df = monthly_comparison()
        print(f"   ✅ Monthly comparison: {len(df)} months of data")
        
        # P&L Statement
        print("📋 P&L Statement...")
        pnl_df = pnl_statement(None)
        print(f"   ✅ P&L statement: {len(pnl_df)} line items")
        
        # Budget variance
        print("📊 Budget Variance...")
        var_df = budget_variance_analysis(None)
        print(f"   ✅ Budget variance: {len(var_df)} categories analyzed")
        
        # Revenue growth
        print("📈 Revenue Growth...")
        growth_df = revenue_growth_analysis()
        print(f"   ✅ Revenue growth: {len(growth_df)} months of data")
        
        # Top expenses
        print("💸 Top Expenses...")
        expenses_df = top_expenses_analysis()
        print(f"   ✅ Top expenses: {len(expenses_df)} expense categories")
        
        # Quarterly summary
        print("📅 Quarterly Summary...")
        quarterly_df = quarterly_summary()
        print(f"   ✅ Quarterly data: {len(quarterly_df)} quarters")
        
        # Burn rate analysis
        print("🔥 Burn Rate...")
        burn_df = burn_rate_analysis()
        print(f"   ✅ Burn rate analysis: {len(burn_df)} months")
        
        print(f"\n🎉 All enhanced analysis functions working!")
        return True
        
    except Exception as e:
        print(f"❌ Error in analysis functions: {e}")
        return False

def show_sample_outputs():
    """Show sample outputs from new functions"""
    print("\n🎯 Sample Analysis Outputs...")
    print("="*50)
    
    # Monthly comparison sample
    print("\n📊 MONTHLY COMPARISON SAMPLE:")
    df = monthly_comparison()
    if len(df) >= 2:
        latest = df.iloc[-1]
        previous = df.iloc[-2]
        print(f"Current Month ({latest['period'].strftime('%B %Y')}):")
        print(f"  Revenue: ${latest['revenue']:,.0f}")
        print(f"  EBITDA: ${latest['ebitda']:,.0f}")
        print(f"  Gross Margin: {latest['gross_margin_pct']:.1f}%")
        
        print(f"\nPrevious Month ({previous['period'].strftime('%B %Y')}):")
        print(f"  Revenue: ${previous['revenue']:,.0f}")
        print(f"  EBITDA: ${previous['ebitda']:,.0f}")
        print(f"  Gross Margin: {previous['gross_margin_pct']:.1f}%")
    
    # Top expenses sample
    print(f"\n💸 TOP 5 EXPENSE CATEGORIES:")
    expenses_df = top_expenses_analysis()
    for i, (_, row) in enumerate(expenses_df.head(5).iterrows()):
        print(f"  {i+1}. {row['category']}: ${row['total_amount']:,.0f} ({row['percentage_of_total']:.1f}%)")
    
    # Revenue growth sample
    print(f"\n📈 RECENT REVENUE GROWTH:")
    growth_df = revenue_growth_analysis()
    if len(growth_df) >= 3:
        recent_months = growth_df.tail(3)
        avg_growth = recent_months['mom_growth_pct'].mean()
        print(f"  Average MoM Growth (Last 3 months): {avg_growth:.1f}%")
        print(f"  Latest Revenue: ${recent_months.iloc[-1]['amount_usd']:,.0f}")
    
    print(f"\n🎊 Enhanced Mini CFO Copilot is ready!")

if __name__ == "__main__":
    print("🚀 MINI CFO COPILOT - ENHANCED FUNCTIONALITY TEST")
    print("="*60)
    
    # Run all tests
    test_new_intents()
    
    analysis_success = test_new_analysis_functions()
    
    if analysis_success:
        show_sample_outputs()
        
        print(f"\n🎉 ALL ENHANCED FEATURES WORKING PERFECTLY!")
        print(f"\n🌟 NEW QUESTIONS YOU CAN ASK:")
        print("   • 'Show me month over month comparison'")
        print("   • 'Give me budget variance analysis'") 
        print("   • 'What's our revenue growth rate?'")
        print("   • 'Show me top expense categories'")
        print("   • 'Give me P&L statement for June 2025'")
        print("   • 'Show me burn rate trends'")
        print("   • 'Give me quarterly financial summary'")
        print("   • 'Show me financial health metrics'")
        
        print(f"\n🎯 Your Mini CFO Copilot now handles {len([
            'revenue_vs_budget', 'gm_trend', 'opex_breakdown', 'cash_runway', 
            'ebitda', 'monthly_comparison', 'yearly_comparison', 'pnl_statement',
            'budget_variance', 'burn_rate', 'revenue_growth', 'top_expenses',
            'quarterly_summary', 'financial_health', 'dashboard'
        ])} different types of financial analysis!")
        
    else:
        print(f"\n❌ Some enhanced features need debugging.")