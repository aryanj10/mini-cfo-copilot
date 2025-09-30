import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from dateutil import parser as dtparser
from ui.theme import PLOTLY_THEME
from components.blocks import sample_questions
from utils.formatting import format_currency
from agent.intent import classify_intent
from agent.tools import (revenue_vs_budget, gross_margin_trend, opex_breakdown, cash_runway_months, ebitda_proxy,
                        monthly_comparison, yearly_comparison, pnl_statement, budget_variance_analysis,
                        burn_rate_analysis, revenue_growth_analysis, top_expenses_analysis, quarterly_summary)
from components.charts import (chart_revenue_vs_budget_enhanced, chart_gm_enhanced, chart_opex_breakdown_enhanced,
                                chart_cash_runway_enhanced, chart_ebitda_enhanced, chart_monthly_comparison, chart_budget_variance
                                , chart_revenue_growth)


def handle_intent(intent):
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

    elif intent.name == "monthly_comparison":
            st.markdown("**Month-over-Month Financial Comparison**")
            df = monthly_comparison()
            if len(df) >= 2:
                chart_monthly_comparison(df)
                # Show key insights
                latest = df.iloc[-1]
                previous = df.iloc[-2]
                st.write(f"**Key Changes from {previous['period'].strftime('%B')} to {latest['period'].strftime('%B %Y')}:**")
                rev_change = ((latest['revenue'] - previous['revenue']) / previous['revenue'] * 100) if previous['revenue'] != 0 else 0
                st.write(f"• Revenue: {format_currency(latest['revenue'])} ({rev_change:+.1f}%)")
                ebitda_change = ((latest['ebitda'] - previous['ebitda']) / abs(previous['ebitda']) * 100) if previous['ebitda'] != 0 else 0
                st.write(f"• EBITDA: {format_currency(latest['ebitda'])} ({ebitda_change:+.1f}%)")
            else:
                st.warning("Need at least 2 months of data for month-over-month comparison")

    elif intent.name == "budget_variance":
            st.markdown("**Budget Variance Analysis**")
            df = budget_variance_analysis(intent.period)
            chart_budget_variance(df)
            
            # Highlight major variances
            major_variances = df[abs(df['variance_pct']) > 10]
            if len(major_variances) > 0:
                st.warning("**Major Variances (>10%):**")
                for _, row in major_variances.iterrows():
                    direction = "over" if row['variance_pct'] > 0 else "under"
                    st.write(f"• {row['category']}: {abs(row['variance_pct']):.1f}% {direction} budget")

    elif intent.name == "pnl_statement":
            label = intent.period or "Latest Month"
            st.markdown(f"**P&L Statement — {label}**")
            df = pnl_statement(intent.period)
            
            # Show key P&L metrics as cards first
            revenue_row = df[df['type'] == 'revenue']
            ebitda_row = df[df['type'] == 'ebitda']
            gm_row = df[df['type'] == 'percentage']
            
            if len(revenue_row) > 0 and len(ebitda_row) > 0:
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Revenue", format_currency(revenue_row.iloc[0]['amount']))
                with col2:
                    st.metric("EBITDA", format_currency(ebitda_row.iloc[0]['amount']))
                with col3:
                    if len(gm_row) > 0:
                        st.metric("Gross Margin", f"{gm_row.iloc[0]['amount']:.1f}%")
            
            # Show detailed P&L table
            display_df = df[['line_item', 'amount', 'type']].copy()
            display_df['amount_formatted'] = display_df.apply(
                lambda row: f"{row['amount']:.1f}%" if row['type'] == 'percentage' else format_currency(row['amount']),
                axis=1
            )
            st.dataframe(
                display_df[['line_item', 'amount_formatted']].rename(columns={'line_item': 'Line Item', 'amount_formatted': 'Amount'}),
                use_container_width=True
            )

    elif intent.name == "revenue_growth":
            st.markdown("**Revenue Growth Analysis**")
            df = revenue_growth_analysis()
            chart_revenue_growth(df)
            
            # Show growth summary
            avg_mom_growth = df['mom_growth_pct'].mean()
            recent_growth = df['mom_growth_pct'].tail(3).mean()
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Average MoM Growth", f"{avg_mom_growth:.1f}%")
            with col2:
                st.metric("Recent 3M Growth", f"{recent_growth:.1f}%")

    elif intent.name == "top_expenses":
            st.markdown("**Top Expense Categories**")
            df = top_expenses_analysis()
            
            # Show top 10 expenses
            top_10 = df.head(10)
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=top_10['total_amount'],
                y=top_10['category'],
                orientation='h',
                marker_color='#BF616A',
                text=[format_currency(x) for x in top_10['total_amount']],
                textposition='outside'
            ))
            
            fig.update_layout(
                title="Top 10 Expense Categories (All Time)",
                xaxis_title="Total Amount (USD)",
                **PLOTLY_THEME['layout'],
                xaxis=dict(tickformat='$,.0f')
            )
            
            st.plotly_chart(fig, use_container_width=True, key="top_expenses")
            
            # Show summary table
            st.dataframe(
                top_10[['category', 'total_amount', 'avg_monthly', 'percentage_of_total']].rename(columns={
                    'category': 'Category',
                    'total_amount': 'Total Amount',
                    'avg_monthly': 'Avg Monthly',
                    'percentage_of_total': '% of Total'
                }),
                use_container_width=True
            )

    elif intent.name == "burn_rate":
            st.markdown("**Burn Rate Analysis**")
            df = burn_rate_analysis()
            
            if len(df) > 0:
                # Show current metrics
                latest = df.iloc[-1]
                avg_burn = df['burn_rate_3m_avg'].iloc[-1]
                
                # Check if company is profitable
                is_profitable = avg_burn <= 0
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    if is_profitable:
                        revenue = latest.get('revenue', 0)
                        expenses = latest.get('total_expenses', 0)
                        net_income = revenue - expenses
                        st.metric("Monthly Net Income", format_currency(net_income), delta="Profitable")
                    else:
                        st.metric("Current Monthly Net Burn", format_currency(latest['burn_rate']))
                        
                with col2:
                    if is_profitable:
                        st.metric("3-Month Avg Net Income", format_currency(-avg_burn), delta="Cash Generating")
                    else:
                        st.metric("3-Month Avg Net Burn", format_currency(avg_burn))
                        
                with col3:
                    if is_profitable:
                        st.metric("Cash Runway", "∞ months", delta="Self-Sustaining")
                    elif pd.notna(latest['months_runway']) and latest['months_runway'] != np.inf:
                        st.metric("Cash Runway", f"{latest['months_runway']:.1f} months")
                    else:
                        st.metric("Cash Runway", "∞ months")
                
                # Create trend chart
                fig = go.Figure()
                
                if is_profitable:
                    # Show net income trend for profitable companies
                    df['net_income'] = df.get('revenue', 0) - df.get('total_expenses', 0)
                    fig.add_trace(go.Scatter(
                        x=df['period'], y=df['net_income'],
                        mode='lines+markers', name="Monthly Net Income",
                        line=dict(color='#A3BE8C', width=3),
                        fill='tonexty'
                    ))
                    
                    fig.update_layout(
                        **PLOTLY_THEME['layout'],
                        title="Monthly Net Income Trend (Profitable Company)",
                        xaxis_title="Period",
                        yaxis_title="Net Income (USD)",
                        yaxis=dict(tickformat='$,.0f')
                    )
                else:
                    # Show burn rate for companies with negative cash flow
                    fig.add_trace(go.Scatter(
                        x=df['period'], y=df['burn_rate'],
                        mode='lines+markers', name="Monthly Net Burn",
                        line=dict(color='#BF616A', width=3)
                    ))
                    fig.add_trace(go.Scatter(
                        x=df['period'], y=df['burn_rate_3m_avg'],
                        mode='lines', name="3M Avg Net Burn",
                        line=dict(color='#D08770', width=2, dash='dash')
                    ))
                    
                    fig.update_layout(
                        **PLOTLY_THEME['layout'],
                        title="Monthly Net Burn Rate Trend",
                        xaxis_title="Period",
                        yaxis_title="Net Burn Rate (USD)",
                        yaxis=dict(tickformat='$,.0f')
                    )
                
                st.plotly_chart(fig, use_container_width=True, key="burn_rate_trend")
                
                # Show additional context
                if is_profitable:
                    st.success("🎉 **Company is profitable!** Revenue exceeds expenses, generating positive cash flow.")
                else:
                    if latest['months_runway'] < 12:
                        st.warning(f"⚠️ **Low runway warning:** Only {latest['months_runway']:.1f} months of cash remaining at current burn rate.")
                    elif latest['months_runway'] < 24:
                        st.info(f"📊 Current runway: {latest['months_runway']:.1f} months. Consider monitoring burn rate closely.")
                
            else:
                st.info("No financial data available for burn rate analysis!")

    elif intent.name == "financial_health" or intent.name == "quarterly_summary":
            st.markdown("**Financial Health & Key Metrics**")
            
            # Show quarterly summary
            quarterly_df = quarterly_summary()
            if len(quarterly_df) > 0:
                st.subheader("Quarterly Performance")
                
                # Show latest quarter metrics
                latest_q = quarterly_df.iloc[-1]
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Q Revenue", format_currency(latest_q['revenue']))
                with col2:
                    st.metric("Q Gross Margin", f"{latest_q['gross_margin_pct']:.1f}%")
                with col3:
                    st.metric("Q EBITDA", format_currency(latest_q['ebitda']))
                with col4:
                    if 'revenue_qoq_growth' in quarterly_df.columns and pd.notna(latest_q['revenue_qoq_growth']):
                        st.metric("QoQ Growth", f"{latest_q['revenue_qoq_growth']:.1f}%")
                
                # Quarterly trend chart
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=quarterly_df['quarter'], y=quarterly_df['revenue'],
                    mode='lines+markers', name="Revenue",
                    line=dict(color='#5E81AC', width=3)
                ))
                fig.add_trace(go.Scatter(
                    x=quarterly_df['quarter'], y=quarterly_df['ebitda'],
                    mode='lines+markers', name="EBITDA",
                    line=dict(color='#A3BE8C', width=3)
                ))
                
                fig.update_layout(
                    title="Quarterly Financial Trends",
                    xaxis_title="Quarter",
                    yaxis_title="Amount (USD)",
                    **PLOTLY_THEME['layout'],
                    yaxis=dict(tickformat='$,.0f')
                )
                
                st.plotly_chart(fig, use_container_width=True, key="quarterly_trends")
                
                # Show quarterly table
                st.dataframe(quarterly_df.round(1), use_container_width=True)

    else:
            st.markdown("""🤖 **Mini CFO Copilot** - I can help with:
            
**📊 Executive Overview:**
- "Show me the dashboard" - Comprehensive financial overview
- "Show me financial health" - Key metrics and quarterly summary
- "Give me a P&L statement for June 2025" - Detailed profit & loss

**💰 Revenue & Growth:**
- "What was June 2025 revenue vs budget in USD?"
- "Show me revenue growth trends"
- "Show me month over month comparison"
- "Show me year over year revenue comparison"

**📈 Profitability Analysis:**
- "Show Gross Margin % trend for the last 3 months"
- "Show me EBITDA trends and analysis"
- "Show me budget variance analysis"

**💸 Cost Management:**
- "Break down Opex by category for June"
- "Show me top expense categories"
- "What is our cost structure?"

**💳 Cash & Burn Analysis:**
- "What is our cash runway right now?"
- "Show me burn rate analysis"
- "Show me monthly burn trends"

**📋 Advanced Analytics:**
- "Show quarterly financial trends"
- "Give me a complete budget variance report"
- "Show me month-over-month financial comparison"

💡 **Pro Tips:**
- Add specific months: "June 2025", "last 6 months"
- Ask for comparisons: "month over month", "year over year"  
- Request detailed analysis: "budget variance", "burn rate trends"

🎯 **Try:** "Show me the dashboard" for a complete executive overview!
            """)
        
        # Additional comprehensive analysis section
    with st.expander("📊 Additional Financial Analysis", expanded=False):
            st.markdown("### 📈 Historical Trends & Analysis")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("6-Month Gross Margin Trend")
                gm_df_6m = gross_margin_trend(6)
                chart_gm_enhanced(gm_df_6m, 6)
            
            with col2:
                st.subheader("12-Month EBITDA History")
                ebitda_df_full = ebitda_proxy()
                # Show last 12 months
                ebitda_12m = ebitda_df_full.tail(12) if len(ebitda_df_full) > 12 else ebitda_df_full
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=ebitda_12m['period'],
                    y=ebitda_12m['ebitda_proxy_usd'],
                    mode='lines+markers',
                    name='EBITDA',
                    line=dict(color='#5E81AC', width=3),
                    marker=dict(size=8),
                    hovertemplate='<b>%{x|%B %Y}</b><br>EBITDA: %{y:$,.0f}<extra></extra>'
                ))
                fig.add_hline(y=0, line_dash="dash", line_color="#BF616A", annotation_text="Break-even")
                fig.update_layout(
                    title="12-Month EBITDA History",
                    xaxis_title="Period",
                    yaxis_title="EBITDA (USD)",
                    **PLOTLY_THEME['layout'],
                    showlegend=False,
                    yaxis=dict(tickformat='$,.0f', gridcolor='#E5E7EB', zeroline=True)
                )
                st.plotly_chart(fig, use_container_width=True, key="ebitda_12m_history")