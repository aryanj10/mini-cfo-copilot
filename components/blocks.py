# components/blocks.py
import streamlit as st

def sample_questions():
    st.markdown("### 💡 Try asking these questions:")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        **📊 Financial Performance**
        - What was June 2025 revenue vs budget?
        - Show me gross margin trends
        - Give me month over month comparison
        - What's our EBITDA this month?
        """)

    with col2:
        st.markdown("""
        **💰 Cash & Budget Analysis**
        - What's our cash runway?
        - Show me budget variance analysis
        - What's our burn rate trends?
        - Give me quarterly financial summary
        """)

    with col3:
        st.markdown("""
        **📈 Growth & Expenses**
        - What's our revenue growth rate?
        - Show me top expense categories
        - Give me P&L statement for June 2025
        - Show me financial health metrics
        - Show me the dashboard
        """)

    st.divider()

    with st.expander("Data files (fixtures)"):
        st.write("Replace any CSVs below to use your own data.")
        st.write("Expected files in `fixtures/`: actuals.csv, budget.csv, fx.csv, cash.csv")