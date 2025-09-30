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

from features.intents import handle_intent
from exporters.pdf_report import generate_dashboard_pdf
from datetime import datetime

st.set_page_config(page_title="Mini CFO Copilot", page_icon="💼", layout="wide")

st.title("💼 Mini CFO Copilot")
st.caption("Ask questions about monthly financials (actuals, budget, FX, cash).")

# Sample Questions Block
sample_questions()



user_q = st.chat_input("Ask e.g. 'What was June 2025 revenue vs budget in USD?'")

if "history" not in st.session_state:
    st.session_state["history"] = []

for role, content in st.session_state["history"]:
    with st.chat_message(role):
        st.markdown(content)


if user_q:
    st.session_state["history"].append(("user", user_q))
    with st.chat_message("user"):
        st.markdown(user_q)

    intent = classify_intent(user_q)
    with st.chat_message("assistant"):
        handle_intent(intent)

# PDF Export using matplotlib (no Kaleido dependency)
with st.sidebar:
    st.subheader("Export")
    if st.button("Generate Executive Dashboard PDF"):
        try:
            pdf_buffer = generate_dashboard_pdf()
            
            st.success("✅ Executive Dashboard PDF generated successfully!")
            st.download_button(
                label="📄 Download Executive Dashboard PDF",
                data=pdf_buffer.getvalue(),
                file_name=f"executive_dashboard_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf"
            )
            
        except ImportError as e:
            st.error(f"❌ Missing required package: {str(e)}")
            st.info("💡 Install matplotlib with: `uv add matplotlib` or `pip install matplotlib`")
        except Exception as e:
            st.error(f"❌ Error generating PDF: {str(e)}")
            st.info("💡 Try refreshing the page and ensuring all data is loaded properly.")
