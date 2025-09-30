# components/charts.py
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from ui.theme import PLOTLY_THEME
from utils.formatting import format_currency
from agent.tools import (revenue_vs_budget, gross_margin_trend, opex_breakdown, cash_runway_months, ebitda_proxy,
                        monthly_comparison, yearly_comparison, pnl_statement, budget_variance_analysis,
                        burn_rate_analysis, revenue_growth_analysis, top_expenses_analysis, quarterly_summary)

def chart_gm_enhanced(df: pd.DataFrame, n_months: int):
    """Enhanced Gross Margin chart with trend line and benchmarks"""
    fig = go.Figure()
    
    # Main trend line
    fig.add_trace(go.Scatter(
        x=df['period'],
        y=df['gm_pct'],
        mode='lines+markers',
        name='Gross Margin %',
        line=dict(color='#5E81AC', width=3),
        marker=dict(size=8, color='#5E81AC'),
        hovertemplate='<b>%{x|%B %Y}</b><br>Gross Margin: %{y:.1f}%<extra></extra>'
    ))
    
    # Add target line (example: 60% target)
    target_gm = 60
    fig.add_hline(y=target_gm, line_dash="dash", line_color="#A3BE8C", 
                  annotation_text=f"Target: {target_gm}%")
    
    # Calculate trend
    if len(df) >= 2:
        trend_slope = (df['gm_pct'].iloc[-1] - df['gm_pct'].iloc[0]) / (len(df) - 1)
        trend_direction = "📈" if trend_slope > 0 else "📉" if trend_slope < 0 else "➡️"
        
        fig.add_annotation(
            x=df['period'].iloc[-1],
            y=df['gm_pct'].iloc[-1],
            text=f"{trend_direction} {trend_slope:+.1f}pp/month",
            showarrow=True,
            arrowhead=2,
            bgcolor="white",
            bordercolor="#5E81AC"
        )
    
    fig.update_layout(
        **PLOTLY_THEME['layout'],
        title=f"Gross Margin Trend - Last {n_months} Months",
        xaxis_title="Period",
        yaxis_title="Gross Margin (%)",
        showlegend=False,
        yaxis=dict(ticksuffix="%", gridcolor='#E5E7EB')
    )
    
    st.plotly_chart(fig, use_container_width=True, key=f"gm_trend_{n_months}")
    
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
    
    fig = go.Figure()
    
    # Revenue bars
    fig.add_trace(go.Bar(
        x=['Actual', 'Budget'],
        y=[actual, budget],
        name='Revenue',
        marker_color=['#5E81AC' if variance >= 0 else '#BF616A', '#E5E7EB'],
        text=[format_currency(actual), format_currency(budget)],
        textposition='outside',
        hovertemplate='<b>%{x}</b><br>Revenue: %{text}<extra></extra>'
    ))
    
    # Variance indicator
    variance_color = '#A3BE8C' if variance >= 0 else '#BF616A'
    variance_symbol = '▲' if variance >= 0 else '▼'
    
    fig.add_annotation(
        x=1, y=max(actual, budget) * 1.1,
        text=f"{variance_symbol} {format_currency(abs(variance))} ({variance_pct:+.1f}%)",
        showarrow=False,
        font=dict(size=14, color=variance_color, family="Arial Black")
    )
    
    fig.update_layout(
        title=f"Revenue vs Budget - {label}",
        yaxis_title="Revenue (USD)",
        **PLOTLY_THEME['layout'],
        showlegend=False,
        yaxis=dict(tickformat='$,.0f', gridcolor='#E5E7EB')
    )
    
    st.plotly_chart(fig, use_container_width=True, key=f"revenue_budget_{label.replace(' ', '_')}")
    
    # Metrics cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Actual Revenue", format_currency(actual))
    with col2:
        st.metric("Budget", format_currency(budget))
    with col3:
        st.metric("Variance", format_currency(variance), f"{variance_pct:+.1f}%")

def chart_opex_breakdown_enhanced(df: pd.DataFrame, label: str):
    """Enhanced Opex breakdown with pie chart and bar chart"""
    if len(df) == 0:
        st.warning("No Opex data available for the selected period.")
        return
    
    # Create subplot with pie and bar charts
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "domain"}, {"type": "xy"}]],
        subplot_titles=["Opex Distribution", "Opex by Category"],
        column_widths=[0.4, 0.6]
    )
    
    # Pie chart
    account_col = df.columns[0]  # account or entity column
    fig.add_trace(go.Pie(
        labels=df[account_col],
        values=df['amount_usd'],
        name="Opex",
        hovertemplate='<b>%{label}</b><br>Amount: %{value:$,.0f}<br>Percentage: %{percent}<extra></extra>',
        textinfo='label+percent',
        textposition='auto'
    ), row=1, col=1)
    
    # Bar chart
    fig.add_trace(go.Bar(
        x=df['amount_usd'],
        y=df[account_col],
        orientation='h',
        name="Amount",
        marker_color='#5E81AC',
        text=[format_currency(x) for x in df['amount_usd']],
        textposition='outside',
        hovertemplate='<b>%{y}</b><br>Amount: %{text}<extra></extra>'
    ), row=1, col=2)
    
    fig.update_layout(
        title=f"Operating Expenses Breakdown - {label}",
        **PLOTLY_THEME['layout'],
        showlegend=False
    )
    
    fig.update_xaxes(title_text="Amount (USD)", tickformat='$,.0f', row=1, col=2)
    
    st.plotly_chart(fig, use_container_width=True, key=f"opex_breakdown_{label.replace(' ', '_')}")
    
    # Summary metrics
    total_opex = df['amount_usd'].sum()
    avg_opex = df['amount_usd'].mean()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Opex", format_currency(total_opex))
    with col2:
        st.metric("Average per Category", format_currency(avg_opex))
    
    # Data table
    display_df = df.copy()
    display_df['amount_usd'] = display_df['amount_usd'].apply(format_currency)
    display_df['percentage'] = (df['amount_usd'] / total_opex * 100).round(1).astype(str) + '%'
    st.dataframe(
        display_df.rename(columns={account_col: 'Category', 'amount_usd': 'Amount', 'percentage': 'Share (%)'}),
        use_container_width=True
    )

def chart_ebitda_enhanced(df: pd.DataFrame):
    """Enhanced EBITDA chart with revenue components"""
    fig = go.Figure()
    
    # EBITDA line
    fig.add_trace(go.Scatter(
        x=df['period'],
        y=df['ebitda_proxy_usd'],
        mode='lines+markers',
        name='EBITDA',
        line=dict(color='#5E81AC', width=3),
        marker=dict(size=8),
        hovertemplate='<b>%{x|%B %Y}</b><br>EBITDA: %{y:$,.0f}<extra></extra>'
    ))
    
    # Add zero line
    fig.add_hline(y=0, line_dash="dash", line_color="#BF616A", 
                  annotation_text="Break-even")
    
    # Trend analysis
    if len(df) >= 2:
        trend_slope = (df['ebitda_proxy_usd'].iloc[-1] - df['ebitda_proxy_usd'].iloc[0]) / (len(df) - 1)
        trend_direction = "📈" if trend_slope > 0 else "📉" if trend_slope < 0 else "➡️"
        
        fig.add_annotation(
            x=df['period'].iloc[-1],
            y=df['ebitda_proxy_usd'].iloc[-1],
            text=f"{trend_direction} {format_currency(trend_slope)}/month",
            showarrow=True,
            arrowhead=2,
            bgcolor="white",
            bordercolor="#5E81AC"
        )
    
    fig.update_layout(
        title="EBITDA Trend Analysis",
        xaxis_title="Period",
        yaxis_title="EBITDA (USD)",
        **PLOTLY_THEME['layout'],
        showlegend=False,
        yaxis=dict(tickformat='$,.0f', gridcolor='#E5E7EB', zeroline=True)
    )
    
    st.plotly_chart(fig, use_container_width=True, key="ebitda_trend")
    
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
    
    if runway == float('inf'):
        # For infinite runway, create a different visualization
        fig = go.Figure()
        
        # Create a simple indicator for infinite runway
        fig.add_trace(go.Indicator(
            mode = "number",
            value = 0,
            title = {"text": "Cash Runway<br><span style='font-size:0.8em;color:gray'>Company is Profitable</span>"},
            number = {"font": {"size": 1}},  # Hide the number
            domain = {'x': [0, 1], 'y': [0.3, 1]}
        ))
        
        # Add infinity symbol and text
        fig.add_annotation(
            x=0.5, y=0.5,
            text="∞",
            showarrow=False,
            font=dict(size=80, color="#A3BE8C", family="Arial Black")
        )
        
        fig.add_annotation(
            x=0.5, y=0.2,
            text="<b>Infinite Runway</b><br>Company generates positive cash flow",
            showarrow=False,
            font=dict(size=14, color="#A3BE8C"),
            xanchor="center"
        )
        
    else:
        # Create a gauge chart for finite runway
        fig = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = min(runway, 36),  # Cap at 36 for better display
            title = {'text': "Cash Runway (Months)", 'font': {'size': 16}},
            number = {'suffix': " months", 'font': {'size': 24}},
            gauge = {
                'axis': {'range': [0, 36], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': "#5E81AC", 'thickness': 0.3},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 6], 'color': "#FFE5E5"},    # Critical (light red)
                    {'range': [6, 12], 'color': "#FFF5E5"},   # Warning (light orange)
                    {'range': [12, 24], 'color': "#E5F5E5"},  # Good (light green)
                    {'range': [24, 36], 'color': "#E5FFE5"}   # Excellent (lighter green)
                ],
                'threshold': {
                    'line': {'color': "#BF616A", 'width': 4},
                    'thickness': 0.75,
                    'value': 6  # Critical threshold
                }
            }
        ))
        
        # Add status text based on runway
        if runway <= 6:
            status_text = "Critical - Need immediate action"
            status_color = "#BF616A"
        elif runway <= 12:
            status_text = "Warning - Monitor closely"
            status_color = "#EBCB8B"
        elif runway <= 24:
            status_text = "Healthy runway"
            status_color = "#A3BE8C"
        else:
            status_text = "Excellent runway"
            status_color = "#A3BE8C"
            
        fig.add_annotation(
            x=0.5, y=0.1,
            text=status_text,
            showarrow=False,
            font=dict(size=12, color=status_color),
            xanchor="center"
        )
    
    fig.update_layout(
        **PLOTLY_THEME['layout'],
        height=350
    )
    
    st.plotly_chart(fig, use_container_width=True, key="cash_runway_gauge")
    
    # Cash metrics below the chart
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Current Cash", format_currency(cash_usd))
    with col2:
        if runway == float('inf'):
            st.metric("Runway", "∞ months", delta="Self-Sustaining")
        else:
            # Add delta indicator based on runway health
            if runway > 12:
                delta = "Healthy"
                delta_color = "normal"
            elif runway > 6:
                delta = "Monitor"
                delta_color = "off"
            else:
                delta = "Critical"
                delta_color = "inverse"
            st.metric("Runway", f"{runway:.1f} months")

def chart_monthly_comparison(df: pd.DataFrame):
    """Chart month-over-month comparison"""
    if len(df) < 2:
        st.warning("Need at least 2 months of data for comparison")
        return
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=["Revenue Comparison", "EBITDA Comparison", "Opex Comparison", "Gross Margin %"],
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    months = [row['period'].strftime('%B %Y') for _, row in df.iterrows()]
    
    # Revenue
    fig.add_trace(go.Bar(x=months, y=df['revenue'], name="Revenue", marker_color='#5E81AC'), row=1, col=1)
    
    # EBITDA
    colors = ['#A3BE8C' if x >= 0 else '#BF616A' for x in df['ebitda']]
    fig.add_trace(go.Bar(x=months, y=df['ebitda'], name="EBITDA", marker_color=colors), row=1, col=2)
    
    # Opex
    fig.add_trace(go.Bar(x=months, y=df['opex'], name="Opex", marker_color='#D08770'), row=2, col=1)
    
    # Gross Margin %
    fig.add_trace(go.Bar(x=months, y=df['gross_margin_pct'], name="Gross Margin %", marker_color='#EBCB8B'), row=2, col=2)
    
    fig.update_layout(**PLOTLY_THEME['layout'], title="Month-over-Month Financial Comparison", showlegend=False)
    fig.update_yaxes(tickformat='$,.0f', row=1, col=1)
    fig.update_yaxes(tickformat='$,.0f', row=1, col=2)
    fig.update_yaxes(tickformat='$,.0f', row=2, col=1)
    fig.update_yaxes(ticksuffix='%', row=2, col=2)
    
    st.plotly_chart(fig, use_container_width=True, key="monthly_comparison")

def chart_budget_variance(df: pd.DataFrame):
    """Chart budget variance analysis"""
    if len(df) == 0:
        st.warning("No variance data available")
        return
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=["Budget vs Actual", "Variance %"],
        specs=[[{"secondary_y": False}, {"secondary_y": False}]]
    )
    
    # Budget vs Actual
    fig.add_trace(go.Bar(x=df['category'], y=df['actual'], name="Actual", marker_color='#5E81AC'), row=1, col=1)
    fig.add_trace(go.Bar(x=df['category'], y=df['budget'], name="Budget", marker_color='#E5E7EB'), row=1, col=1)
    
    # Variance %
    colors = ['#A3BE8C' if x >= 0 else '#BF616A' for x in df['variance_pct']]
    fig.add_trace(go.Bar(x=df['category'], y=df['variance_pct'], name="Variance %", marker_color=colors), row=1, col=2)
    
    fig.update_layout(
        title=f"Budget Variance Analysis - {df['period'].iloc[0]}",
        **PLOTLY_THEME['layout']
    )
    fig.update_yaxes(tickformat='$,.0f', row=1, col=1)
    fig.update_yaxes(ticksuffix='%', row=1, col=2)
    
    st.plotly_chart(fig, use_container_width=True, key="budget_variance")

def chart_revenue_growth(df: pd.DataFrame):
    """Chart revenue growth analysis"""
    if len(df) == 0:
        st.warning("No revenue growth data available")
        return
    
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=["Revenue Trend", "Growth Rates"],
        row_heights=[0.6, 0.4]
    )
    
    # Revenue trend
    fig.add_trace(go.Scatter(
        x=df['period'], y=df['amount_usd'],
        mode='lines+markers', name="Monthly Revenue",
        line=dict(color='#5E81AC', width=3)
    ), row=1, col=1)
    
    fig.add_trace(go.Scatter(
        x=df['period'], y=df['revenue_3m_avg'],
        mode='lines', name="3M Rolling Avg",
        line=dict(color='#A3BE8C', width=2, dash='dash')
    ), row=1, col=1)
    
    # Growth rates
    fig.add_trace(go.Scatter(
        x=df['period'], y=df['mom_growth_pct'],
        mode='lines+markers', name="MoM Growth %",
        line=dict(color='#EBCB8B', width=2)
    ), row=2, col=1)
    
    fig.add_hline(y=0, line_dash="dash", line_color="#BF616A", row=2, col=1)
    
    fig.update_layout(
        title="Revenue Growth Analysis",
        **PLOTLY_THEME['layout']
    )
    fig.update_yaxes(tickformat='$,.0f', row=1, col=1)
    fig.update_yaxes(ticksuffix='%', row=2, col=1)
    
    st.plotly_chart(fig, use_container_width=True, key="revenue_growth")