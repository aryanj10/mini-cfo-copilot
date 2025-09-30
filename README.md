# Mini CFO Copilot

A Streamlit app that answers financial questions from CSV data using natural language queries.

## Features

- **Natural Language Queries**: Ask questions like "What was June 2025 revenue vs budget?"
- **Financial Analytics**: Revenue vs budget, gross margin trends, EBITDA analysis, cash runway
- **Interactive Charts**: Professional visualizations with variance indicators
- **Executive Dashboard**: Comprehensive KPI overview with multiple charts
- **PDF Export**: Generate professional financial reports
- **Multi-Currency Support**: Automatic FX conversion to USD

## Project Structure

```
mini_cfo_copilot/
├── main.py                     # Main Streamlit application
├── show_dashboard.py           # Dashboard display module  
├── agent/                      # Analytics engine
│   ├── intent.py              # Query classification
│   ├── tools.py               # Financial calculations
│   └── __init__.py
├── exporters/                  # Report generation
│   └── pdf_report.py          # PDF export functionality
├── utils/                      # Utility functions
│   └── formatting.py          # Currency formatting
├── tests/                      # Test suite (23 tests)
│   ├── test_metrics.py        
│   ├── test_currency_conversion.py
│   ├── test_burn_rate.py
│   ├── test_eur_conversion.py
│   ├── test_aggregation.py
│   ├── test_enhanced.py
│   └── test_enhanced_functions.py
├── fixtures/                   # Sample data
│   ├── actuals.csv            # Monthly actuals
│   ├── budget.csv             # Budget data  
│   ├── fx.csv                 # Exchange rates
│   └── cash.csv               # Cash balances
├── requirements.txt            # Python dependencies
└── pyproject.toml             # Project configuration
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run main.py
```

## Sample Questions

**Revenue & Performance:**
- "What was June 2025 revenue vs budget in USD?"
- "Show me revenue growth trends"
- "Give me month over month comparison"

**Profitability:**
- "Show Gross Margin % trend for the last 6 months"
- "What's our EBITDA this month?"
- "Show me EBITDA trends and analysis"

**Costs & Expenses:**
- "Break down Opex by category for June"
- "Show me top expense categories"
- "Show me budget variance analysis"

**Cash & Liquidity:**
- "What is our cash runway right now?"
- "Show me burn rate analysis"

**Executive Overview:**
- "Show me the dashboard"
- "Give me financial health metrics"

## Data Format

Place CSV files in the `fixtures/` directory:

**actuals.csv & budget.csv:**
- `date`/`period` - Time period (e.g., "2025-06-01")
- `account` - Account name (e.g., "Revenue", "COGS", "Opex:Marketing")
- `currency` - Currency code (e.g., "USD", "EUR")
- `amount` - Financial amount

**fx.csv:**
- `date`/`period` - Time period
- `currency` - Currency code
- `rate_to_usd` - Exchange rate to USD

**cash.csv:**
- `date`/`period` - Time period
- `amount`/`balance` - Cash balance

## Testing

```bash
# Run all tests
pytest -q

# Run specific test file
pytest tests/test_metrics.py -v
```

## Key Metrics

- **Revenue vs Budget**: Actual vs planned revenue with variance %
- **Gross Margin**: (Revenue - COGS) / Revenue * 100
- **EBITDA**: Revenue - COGS - Operating Expenses
- **Cash Runway**: Current Cash / Average Monthly Burn Rate
- **Burn Rate**: Monthly revenue minus total expenses