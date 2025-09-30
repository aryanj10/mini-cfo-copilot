import io
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_pdf import PdfPages
import numpy as np
import streamlit as st

from agent.tools import (
    revenue_vs_budget, cash_runway_months,
    gross_margin_trend, ebitda_proxy, opex_breakdown
)
from utils.formatting import format_currency


def generate_dashboard_pdf():
    """Generate Executive Dashboard PDF and return as BytesIO buffer."""
    # Corporate colors
    colors = {
        'primary': '#5E81AC',
        'success': '#A3BE8C', 
        'warning': '#EBCB8B',
        'danger': '#BF616A',
        'secondary': '#D08770',
        'text': '#2E3440',
        'light_gray': '#E5E7EB'
    }

    # matplotlib styling
    plt.style.use('default')
    plt.rcParams.update({
        'font.family': 'Arial',
        'font.size': 10,
        'axes.labelcolor': colors['text'],
        'axes.edgecolor': colors['light_gray'],
        'axes.linewidth': 0.8,
        'axes.grid': True,
        'grid.color': colors['light_gray'],
        'grid.linewidth': 0.5,
        'grid.alpha': 0.7,
        'xtick.color': colors['text'],
        'ytick.color': colors['text'],
        'text.color': colors['text'],
        'figure.facecolor': 'white',
        'axes.facecolor': 'white'
    })

    # fetch financial data
    a, b, label = revenue_vs_budget(None)
    variance = a - b
    variance_pct = (variance / b * 100) if b != 0 else 0
    cash_usd, runway = cash_runway_months()
    gm_df = gross_margin_trend(6)
    latest_gm = gm_df['gm_pct'].iloc[-1] if len(gm_df) > 0 else 0
    ebitda_df = ebitda_proxy()
    latest_ebitda = ebitda_df['ebitda_proxy_usd'].iloc[-1] if len(ebitda_df) > 0 else 0
    df_ox = opex_breakdown(None)

    # PDF buffer
    pdf_buffer = io.BytesIO()

    with PdfPages(pdf_buffer) as pdf:
                # Create figure
                fig = plt.figure(figsize=(11.7, 8.3))  # A4 landscape
                
                # Add header
                fig.suptitle('Executive Financial Dashboard', 
                           fontsize=20, fontweight='bold', color=colors['text'], y=0.95)
                
                date_str = datetime.now().strftime("%B %d, %Y")
                fig.text(0.85, 0.92, f"Generated: {date_str}", 
                        fontsize=10, color=colors['text'], ha='right')
                
                # KPI Section
                ax_kpi = fig.add_axes([0.05, 0.75, 0.9, 0.15])
                ax_kpi.set_xlim(0, 4)
                ax_kpi.set_ylim(0, 2)
                ax_kpi.axis('off')
                
                # KPI boxes
                kpis = [
                    ("Revenue", format_currency(a), f"{variance_pct:+.1f}% vs Budget", 
                     colors['success'] if variance >= 0 else colors['danger']),
                    ("Gross Margin", f"{latest_gm:.1f}%", "Latest Month", colors['primary']),
                    ("EBITDA", format_currency(latest_ebitda), "Current", colors['secondary']),
                    ("Cash Runway", "∞ months" if runway == float('inf') else f"{runway:.1f} months", 
                     format_currency(cash_usd), colors['warning'] if runway != float('inf') and runway < 12 else colors['success'])
                ]
                
                for i, (title, value, subtitle, color) in enumerate(kpis):
                    x = i * 1.0
                    rect = patches.Rectangle((x, 0.2), 0.9, 1.6, linewidth=1, 
                                           edgecolor=color, facecolor='white', alpha=0.8)
                    ax_kpi.add_patch(rect)
                    ax_kpi.text(x + 0.45, 1.5, title, ha='center', va='center', 
                               fontsize=10, fontweight='bold', color=color)
                    ax_kpi.text(x + 0.45, 1.0, value, ha='center', va='center', 
                               fontsize=14, fontweight='bold', color=colors['text'])
                    ax_kpi.text(x + 0.45, 0.5, subtitle, ha='center', va='center', 
                               fontsize=8, color=colors['text'])
                
                # Revenue vs Budget Chart
                ax1 = fig.add_axes([0.05, 0.45, 0.4, 0.25])
                categories = ['Budget', 'Actual']
                values = [b, a]
                chart_colors = [colors['secondary'], colors['primary']]
                
                bars = ax1.bar(categories, values, color=chart_colors, alpha=0.8, edgecolor='white', linewidth=2)
                for bar, value in zip(bars, values):
                    height = bar.get_height()
                    ax1.text(bar.get_x() + bar.get_width()/2., height + max(values)*0.01,
                            format_currency(value), ha='center', va='bottom', fontweight='bold')
                
                variance_color = colors['success'] if variance >= 0 else colors['danger']
                ax1.text(0.5, max(values) * 0.8, 
                        f"Variance: {format_currency(variance)}\n({variance_pct:+.1f}%)",
                        ha='center', va='center', fontsize=11, fontweight='bold',
                        bbox=dict(boxstyle="round,pad=0.3", facecolor=variance_color, alpha=0.7, edgecolor='white'))
                
                ax1.set_title(f'Revenue vs Budget - {label}', fontsize=12, fontweight='bold', pad=20)
                ax1.set_ylabel('Amount (USD)', fontweight='bold')
                ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: format_currency(x)))
                
                # Gross Margin Trend
                ax2 = fig.add_axes([0.55, 0.45, 0.4, 0.25])
                if len(gm_df) > 0:
                    dates = [d.strftime('%b %Y') for d in gm_df['period']]
                    ax2.plot(dates, gm_df['gm_pct'], marker='o', linewidth=3, 
                            markersize=8, color=colors['primary'])
                    
                    target = 80
                    ax2.axhline(y=target, color=colors['success'], linestyle='--', alpha=0.7, linewidth=2)
                    ax2.text(len(dates)-1, target + 1, f'Target: {target}%', 
                           color=colors['success'], fontweight='bold')
                    
                    if len(gm_df) >= 2:
                        trend = gm_df['gm_pct'].iloc[-1] - gm_df['gm_pct'].iloc[0]
                        trend_symbol = "↗" if trend > 0 else "↘" if trend < 0 else "→"
                        ax2.text(0.02, 0.98, f'{trend_symbol} {trend:+.1f}pp', 
                               transform=ax2.transAxes, fontsize=11, fontweight='bold',
                               bbox=dict(boxstyle="round,pad=0.3", facecolor=colors['light_gray'], alpha=0.8))
                
                ax2.set_title('Gross Margin Trend (6 Months)', fontsize=12, fontweight='bold', pad=20)
                ax2.set_ylabel('Gross Margin (%)', fontweight='bold')
                plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
                
                # Operating Expenses Pie Chart
                ax3 = fig.add_axes([0.05, 0.05, 0.4, 0.35])
                if len(df_ox) > 0:
                    top_expenses = df_ox.head(5)
                    colors_list = [colors['primary'], colors['success'], colors['warning'], 
                                  colors['danger'], colors['secondary']][:len(top_expenses)]
                    
                    wedges, texts, autotexts = ax3.pie(top_expenses['amount_usd'], 
                                                     labels=top_expenses.iloc[:, 0],
                                                     colors=colors_list,
                                                     autopct='%1.1f%%',
                                                     startangle=90,
                                                     pctdistance=0.85)
                    
                    for autotext in autotexts:
                        autotext.set_color('white')
                        autotext.set_fontweight('bold')
                        autotext.set_fontsize(10)
                    
                    for text in texts:
                        text.set_fontsize(9)
                        text.set_fontweight('bold')
                    
                    total = df_ox['amount_usd'].sum()
                    ax3.text(0, 0, f'Total OpEx\n{format_currency(total)}', 
                           ha='center', va='center', fontsize=11, fontweight='bold',
                           bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.9))
                
                ax3.set_title('Operating Expenses Breakdown', fontsize=12, fontweight='bold', pad=20)
                
                # Cash Runway Visualization
                ax4 = fig.add_axes([0.55, 0.05, 0.4, 0.35])
                if runway == float('inf'):
                    ax4.text(0.5, 0.6, '∞', ha='center', va='center', fontsize=60, 
                           color=colors['success'], fontweight='bold')
                    ax4.text(0.5, 0.3, 'Infinite Runway\n(Profitable)', ha='center', va='center', 
                           fontsize=14, fontweight='bold', color=colors['success'])
                else:
                    angles = np.linspace(0, np.pi, 100)
                    ax4.plot(np.cos(angles), np.sin(angles), color=colors['light_gray'], linewidth=8)
                    
                    if runway <= 6:
                        color = colors['danger']
                        status = "Critical"
                    elif runway <= 12:
                        color = colors['warning'] 
                        status = "Warning"
                    else:
                        color = colors['success']
                        status = "Healthy"
                    
                    runway_proportion = min(runway / 24, 1.0)
                    runway_angles = angles[:int(len(angles) * runway_proportion)]
                    ax4.plot(np.cos(runway_angles), np.sin(runway_angles), color=color, linewidth=8)
                    
                    ax4.text(0, -0.3, f'{runway:.1f} months', ha='center', va='center', 
                           fontsize=18, fontweight='bold', color=color)
                    ax4.text(0, -0.5, status, ha='center', va='center', 
                           fontsize=12, fontweight='bold', color=color)
                
                ax4.text(0, -0.7, f'Cash: {format_currency(cash_usd)}', ha='center', va='center', 
                       fontsize=10, fontweight='bold', color=colors['text'])
                
                ax4.set_xlim(-1.2, 1.2)
                ax4.set_ylim(-0.8, 1.2)
                ax4.set_aspect('equal')
                ax4.axis('off')
                ax4.set_title('Cash Runway', fontsize=12, fontweight='bold', pad=20)
                
                # Add footer
                fig.text(0.5, 0.02, f'Generated by Mini CFO Copilot | {datetime.now().strftime("%Y-%m-%d %H:%M")}', 
                        ha='center', fontsize=8, color=colors['text'], style='italic')
                
                # Save to PDF
                pdf.savefig(fig, bbox_inches='tight', dpi=300)
                plt.close()
            
    pdf_buffer.seek(0)
    return pdf_buffer

