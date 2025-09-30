import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from dateutil import parser as dtparser

from agent.intent import classify_intent
from agent.tools import revenue_vs_budget, gross_margin_trend, opex_breakdown, cash_runway_months, ebitda_proxy

st.set_page_config(page_title="Mini CFO Copilot", page_icon="💼", layout="wide")

st.title("💼 Mini CFO Copilot")
st.caption("Ask questions about monthly financials (actuals, budget, FX, cash).")

with st.expander("Data files (fixtures)"):
    st.write("Replace any CSVs below to use your own data.")
    st.write("Expected files in `fixtures/`: actuals.csv, budget.csv, fx.csv, cash.csv")

user_q = st.chat_input("Ask e.g. 'Show me the dashboard' or 'What was June 2025 revenue vs budget in USD?'")

if "history" not in st.session_state:
    st.session_state["history"] = []

for role, content in st.session_state["history"]:
    with st.chat_message(role):
        st.markdown(content)

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

def chart_gm_enhanced(df: pd.DataFrame, n_months: int):
    """Enhanced Gross Margin chart with trend line"""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Main trend line
    ax.plot(df['period'], df['gm_pct'], marker='o', linewidth=3, markersize=8, color='#5E81AC')
    
    # Add target line
    target_gm = 60
    ax.axhline(y=target_gm, linestyle='--', color='#A3BE8C', alpha=0.7, label=f'Target: {target_gm}%')
    
    # Formatting
    ax.set_title(f'Gross Margin Trend - Last {n_months} Months', fontsize=16, fontweight='bold')
    ax.set_xlabel('Period', fontsize=12)
    ax.set_ylabel('Gross Margin (%)', fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # Format x-axis dates
    ax.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    st.pyplot(fig)
    
    # Data table
    display_df = df.copy()
    display_df['period'] = display_df['period'].dt.strftime('%B %Y')
    display_df['gm_pct'] = display_df['gm_pct'].round(1)
    st.dataframe(
        display_df[['period', 'gm_pct']].rename(columns={'period': 'Month', 'gm_pct': 'Gross Margin (%)'}),
        use_container_width=True
    )

def chart_revenue_vs_budget_enhanced(actual, budget, label):
    """Enhanced Revenue vs Budget with variance analysis"""
    variance = actual - budget
    variance_pct = (variance / budget * 100) if budget != 0 else 0
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Revenue bars
    colors = ['#5E81AC' if variance >= 0 else '#BF616A', '#E5E7EB']
    bars = ax.bar(['Actual', 'Budget'], [actual, budget], color=colors)
    
    # Add value labels on bars
    for i, (bar, value) in enumerate(zip(bars, [actual, budget])):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                format_currency(value), ha='center', va='bottom', fontweight='bold')
    
    # Variance annotation
    variance_color = '#A3BE8C' if variance >= 0 else '#BF616A'
    variance_symbol = '▲' if variance >= 0 else '▼'
    
    ax.text(0.5, max(actual, budget) * 1.15, 
            f"{variance_symbol} {format_currency(abs(variance))} ({variance_pct:+.1f}%)",
            ha='center', fontsize=14, color=variance_color, fontweight='bold')
    
    ax.set_title(f'Revenue vs Budget - {label}', fontsize=16, fontweight='bold')
    ax.set_ylabel('Revenue (USD)', fontsize=12)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format_currency(x)))
    ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    st.pyplot(fig)
    
    # Metrics cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Actual Revenue", format_currency(actual))
    with col2:
        st.metric("Budget", format_currency(budget))
    with col3:
        st.metric("Variance", format_currency(variance), f"{variance_pct:+.1f}%")

def chart_opex_breakdown_enhanced(df: pd.DataFrame, label: str):
    """Enhanced Opex breakdown with horizontal bar chart"""
    if len(df) == 0:
        st.warning("No Opex data available for the selected period.")
        return
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    account_col = df.columns[0]  # account or entity column
    
    # Pie chart
    ax1.pie(df['amount_usd'], labels=df[account_col], autopct='%1.1f%%', startangle=90)
    ax1.set_title('Opex Distribution')
    
    # Bar chart
    ax2.barh(df[account_col], df['amount_usd'], color='#5E81AC')
    ax2.set_title('Opex by Category')
    ax2.set_xlabel('Amount (USD)')
    ax2.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format_currency(x)))
    
    # Add value labels
    for i, v in enumerate(df['amount_usd']):
        ax2.text(v + v*0.01, i, format_currency(v), va='center')
    
    fig.suptitle(f'Operating Expenses Breakdown - {label}', fontsize=16, fontweight='bold')
    plt.tight_layout()
    st.pyplot(fig)
    
    # Summary metrics
    total_opex = df['amount_usd'].sum()
    avg_opex = df['amount_usd'].mean()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Opex", format_currency(total_opex))
    with col2:
        st.metric("Average per Category", format_currency(avg_opex))

def chart_ebitda_enhanced(df: pd.DataFrame):
    """Enhanced EBITDA chart"""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # EBITDA line
    ax.plot(df['period'], df['ebitda_proxy_usd'], marker='o', linewidth=3, markersize=8, color='#5E81AC')
    
    # Add zero line
    ax.axhline(y=0, linestyle='--', color='#BF616A', alpha=0.7, label='Break-even')
    
    ax.set_title('EBITDA Trend Analysis', fontsize=16, fontweight='bold')
    ax.set_xlabel('Period', fontsize=12)
    ax.set_ylabel('EBITDA (USD)', fontsize=12)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format_currency(x)))
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    # Format x-axis dates
    ax.tick_params(axis='x', rotation=45)
    
    plt.tight_layout()
    st.pyplot(fig)
    
    # Metrics
    latest_ebitda = df['ebitda_proxy_usd'].iloc[-1]
    avg_ebitda = df['ebitda_proxy_usd'].mean()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Latest EBITDA", format_currency(latest_ebitda))
    with col2:
        st.metric("Average EBITDA", format_currency(avg_ebitda))

def chart_cash_runway_enhanced(cash_usd: float, runway: float):
    """Enhanced cash runway visualization"""
    fig, ax = plt.subplots(figsize=(8, 6))
    
    # Create a simple gauge-like visualization
    if runway == float('inf'):
        runway_display = 24  # Cap for display
        ax.text(0.5, 0.7, "♾️", ha='center', va='center', fontsize=60, transform=ax.transAxes)
        ax.text(0.5, 0.5, "Infinite Runway\n(Profitable)", ha='center', va='center', 
                fontsize=16, fontweight='bold', transform=ax.transAxes)
    else:
        runway_display = min(runway, 24)  # Cap at 24 months for display
        
        # Color coding
        if runway < 6:
            color = '#BF616A'  # Red
            status = "Critical"
        elif runway < 12:
            color = '#EBCB8B'  # Yellow
            status = "Warning"
        else:
            color = '#A3BE8C'  # Green
            status = "Healthy"
        
        # Simple bar representation
        bar_width = runway_display / 24
        ax.barh([0], [bar_width], color=color, height=0.3)
        ax.set_xlim(0, 1)
        ax.set_ylim(-0.5, 0.5)
        ax.set_title(f'Cash Runway: {runway:.1f} months ({status})', fontsize=16, fontweight='bold')
        ax.text(bar_width/2, 0, f'{runway:.1f}m', ha='center', va='center', fontweight='bold')
    
    ax.set_xticks([])
    ax.set_yticks([])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    ax.spines['left'].set_visible(False)
    
    plt.tight_layout()
    st.pyplot(fig)
    
    # Cash metrics
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Current Cash", format_currency(cash_usd))
    with col2:
        runway_text = "∞ months" if runway == float('inf') else f"{runway:.1f} months"
        st.metric("Runway", runway_text)

if user_q:
    st.session_state["history"].append(("user", user_q))
    with st.chat_message("user"):
        st.markdown(user_q)

    intent = classify_intent(user_q)
    with st.chat_message("assistant"):
        if intent.name == "revenue_vs_budget":
            a, b, label = revenue_vs_budget(intent.period)
            st.markdown(f"**Revenue vs Budget — {label}**")
            chart_revenue_vs_budget_enhanced(a, b, label)

        elif intent.name == "gm_trend":
            n = 3
            if intent.period and "last" in intent.period:
                try:
                    n = int(intent.period.split()[1])
                except Exception:
                    n = 3
            df = gross_margin_trend(n)
            st.markdown(f"**Gross Margin % trend for last {n} months**")
            chart_gm_enhanced(df, n)

        elif intent.name == "opex_breakdown":
            label = intent.period or "Latest Month"
            df = opex_breakdown(intent.period)
            st.markdown(f"**Opex by category — {label}**")
            chart_opex_breakdown_enhanced(df, label)

        elif intent.name == "cash_runway":
            cash_usd, runway = cash_runway_months()
            if runway == float('inf'):
                st.markdown(f"**Cash runway:** Infinite runway (company is profitable)")
            else:
                st.markdown(f"**Cash runway:** {runway:.1f} months remaining")
            chart_cash_runway_enhanced(cash_usd, runway)

        elif intent.name == "ebitda" or intent.name == "ebitda_trend":
            st.markdown("**EBITDA Analysis**")
            ebitda_df = ebitda_proxy()
            chart_ebitda_enhanced(ebitda_df)

        elif intent.name == "dashboard":
            st.markdown("# 📊 Executive Financial Dashboard")
            
            # Key metrics row
            col1, col2, col3, col4 = st.columns(4)
            
            # Latest revenue
            a, b, label = revenue_vs_budget(None)
            variance_pct = ((a - b) / b * 100) if b != 0 else 0
            with col1:
                st.metric("Latest Revenue", format_currency(a), f"{variance_pct:+.1f}% vs Budget")
            
            # Latest gross margin
            gm_df = gross_margin_trend(1)
            latest_gm = gm_df['gm_pct'].iloc[-1] if len(gm_df) > 0 else 0
            with col2:
                st.metric("Gross Margin", f"{latest_gm:.1f}%")
            
            # EBITDA
            ebitda_df = ebitda_proxy()
            latest_ebitda = ebitda_df['ebitda_proxy_usd'].iloc[-1] if len(ebitda_df) > 0 else 0
            with col3:
                st.metric("Latest EBITDA", format_currency(latest_ebitda))
            
            # Cash runway
            cash_usd, runway = cash_runway_months()
            runway_text = "∞" if runway == float('inf') else f"{runway:.1f}"
            with col4:
                st.metric("Cash Runway", f"{runway_text} months")
            
            st.markdown("---")
            
            # Charts in grid layout
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Revenue vs Budget")
                chart_revenue_vs_budget_enhanced(a, b, label)
                
                st.subheader("Gross Margin Trend")
                gm_df_3m = gross_margin_trend(3)
                chart_gm_enhanced(gm_df_3m, 3)
            
            with col2:
                st.subheader("EBITDA Analysis")
                chart_ebitda_enhanced(ebitda_df)
                
                st.subheader("Cash Position")
                chart_cash_runway_enhanced(cash_usd, runway)
            
            # Opex analysis full width
            st.subheader("Operating Expenses Breakdown")
            opex_df = opex_breakdown(None)
            chart_opex_breakdown_enhanced(opex_df, "Latest Month")

        elif intent.name == "revenue":
            a, b, label = revenue_vs_budget(None)
            st.markdown(f"**Latest Revenue vs Budget — {label}**")
            chart_revenue_vs_budget_enhanced(a, b, label)

        else:
            st.markdown("""🤖 **Mini CFO Copilot** - I can help with:
            
**Revenue & Performance:**
- "What was June 2025 revenue vs budget in USD?"
- "Show me latest revenue performance"

**Profitability Analysis:**
- "Show Gross Margin % trend for the last 3 months"
- "Show me EBITDA trends and analysis"

**Cost Management:**
- "Break down Opex by category for June"
- "Show operating expenses breakdown"

**Cash Management:**
- "What is our cash runway right now?"
- "Show me cash position"

**Executive Dashboard:**
- "Show me the dashboard" or "Give me a financial overview"

💡 **Tip:** Try asking "Show me the dashboard" for a comprehensive financial overview!
            """)

# Additional comprehensive analysis section
        with st.expander("📊 Additional Financial Analysis", expanded=False):
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("EBITDA Analysis")
                ebitda_df = ebitda_proxy()
                chart_ebitda_enhanced(ebitda_df)
            
            with col2:
                st.subheader("Cash Position")
                cash_usd, runway = cash_runway_months()
                chart_cash_runway_enhanced(cash_usd, runway)