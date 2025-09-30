# 💼 Mini CFO Copilot

> **AI-Powered Financial Analysis & Reporting Platform**

A sophisticated Streamlit application that transforms raw financial data into actionable insights through natural language queries and executive-ready visualizations.

## 🌟 Overview

Mini CFO Copilot is an intelligent financial analysis platform that allows finance professionals to interact with their data using natural language. Simply ask questions about your financial performance, and get instant insights with professional charts and metrics.

**🎯 Perfect for:**
- **CFOs & Finance Teams** - Quick financial health checks and variance analysis
- **Board Presentations** - Executive dashboards and professional PDF reports  
- **FP&A Analysts** - Trend analysis and budget performance monitoring
- **Startups & SMEs** - Cash runway analysis and burn rate tracking

## ✨ Key Features

### 📊 **Interactive Financial Analytics**
- **Revenue Performance**: Budget vs actual analysis with variance indicators
- **Profitability Analysis**: Gross margin trends with benchmark tracking
- **Cost Management**: Operating expense breakdowns with category analysis
- **Cash Management**: Runway calculations with burn rate monitoring
- **EBITDA Tracking**: Profitability trends and monthly comparisons

### 🤖 **Natural Language Interface**
- **Chat-like Experience**: Ask questions in plain English
- **Smart Intent Recognition**: Automatically understands financial queries
- **Contextual Responses**: Get relevant charts and insights instantly

### 📈 **Professional Visualizations**
- **Interactive Charts**: Hover tooltips, zoom, and pan capabilities
- **Trend Analysis**: Moving averages and growth indicators
- **Variance Indicators**: Visual budget vs actual comparisons
- **Executive Dashboards**: Comprehensive KPI overviews

### 📄 **Executive Reporting**
- **One-Click PDF Export**: Professional financial summaries
- **Board-Ready Formats**: Executive dashboard layouts
- **Corporate Styling**: Professional color schemes and branding

### 🔧 **Robust Data Processing**
- **Multi-Currency Support**: Automatic FX conversion to USD
- **Flexible Data Formats**: CSV and Excel compatibility
- **Smart Date Parsing**: Handles various date formats automatically
- **Data Validation**: Built-in error handling and data quality checks

## 🏗️ Architecture

```
mini_cfo_copilot/
├── 🚀 main.py                    # Main Streamlit application
├── 🤖 agent/                    # AI & Analytics Engine
│   ├── intent.py               # Natural language processing
│   └── tools.py                # Financial analysis functions
├── 📊 exporters/               # PDF & Report Generation
│   └── pdf_report.py           # Executive dashboard export
├── 🧪 tests/                   # Comprehensive Test Suite
│   ├── test_metrics.py         # Core metrics testing
│   ├── test_currency_conversion.py
│   ├── test_burn_rate.py
│   └── test_eur_conversion.py
├── 📁 fixtures/                # Sample Financial Data
│   ├── actuals.csv             # Monthly actuals
│   ├── budget.csv              # Budget data
│   ├── fx.csv                  # FX rates
│   └── cash.csv                # Cash balances
└── ⚙️ requirements.txt         # Dependencies
```

## 🚀 Quick Start

### Prerequisites
- Python 3.9+ 
- pip or uv package manager

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd mini_cfo_copilot

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
# or with uv:
uv sync

# Launch the application
streamlit run main.py
```

### 🔗 Access the App
Open your browser and navigate to: `http://localhost:8501`

## 💬 Sample Queries

### 📈 **Performance Analysis**
```
💡 "What was June 2025 revenue vs budget in USD?"
💡 "Show me revenue growth trends"
💡 "Give me month over month comparison"
💡 "Show me year over year performance"
```

### 💰 **Profitability & Margins**
```
💡 "Show Gross Margin % trend for the last 6 months"
💡 "What's our EBITDA this month?"
💡 "Show me EBITDA trends and analysis"
💡 "Give me P&L statement for June 2025"
```

### 💸 **Cost & Expense Analysis**
```
💡 "Break down Opex by category for June"
💡 "Show me top expense categories"
💡 "What's our cost structure?"
💡 "Show me budget variance analysis"
```

### 🏦 **Cash & Liquidity**
```
💡 "What is our cash runway right now?"
💡 "Show me burn rate analysis"
💡 "What's our monthly burn trends?"
💡 "Show me cash flow analysis"
```

### 📊 **Executive Dashboards**
```
💡 "Show me the dashboard"
💡 "Give me financial health metrics"
💡 "Show quarterly financial summary"
💡 "Show me financial health metrics"
```

## 📁 Data Requirements

### 📄 **File Formats**
Place your financial data in the `fixtures/` directory as CSV files:

#### `actuals.csv` & `budget.csv`
| Column | Description | Example |
|--------|-------------|---------|
| `date` / `period` | Time period | `2025-06-01` or `June 2025` |
| `entity` | Business unit (optional) | `US Operations` |
| `account` | Chart of accounts | `Revenue`, `COGS`, `Opex:Marketing` |
| `currency` | Currency code | `USD`, `EUR`, `GBP` |
| `amount` | Financial amount | `150000` |

#### `fx.csv`
| Column | Description | Example |
|--------|-------------|---------|
| `date` / `period` | Time period | `2025-06-01` |
| `currency` | Currency code | `EUR` |
| `rate_to_usd` | Exchange rate | `1.085` |

#### `cash.csv`
| Column | Description | Example |
|--------|-------------|---------|
| `date` / `period` | Time period | `2025-06-01` |
| `currency` | Currency code (optional) | `USD` |
| `amount` / `balance` | Cash balance | `2500000` |

### 🔄 **Data Processing Features**
- **Flexible Column Names**: Case-insensitive matching
- **Multiple Date Formats**: Automatic parsing of various date formats
- **Multi-Currency Support**: Automatic conversion to USD using FX rates
- **Missing Data Handling**: Graceful handling of incomplete data

## 🧪 Testing

### Run All Tests
```bash
# Quick test run
pytest -q

# Verbose output
pytest -v

# Test specific functionality
pytest tests/test_metrics.py
pytest tests/test_currency_conversion.py
```

### 📋 **Test Coverage**
- ✅ **Core Metrics** - Revenue, EBITDA, margins, cash runway
- ✅ **Currency Conversion** - Multi-currency FX processing
- ✅ **Burn Rate Analysis** - Cash flow and runway calculations  
- ✅ **Data Aggregation** - Financial statement generation
- ✅ **Enhanced Functions** - Advanced analytics and reporting

## 🎨 Features in Detail

### 🤖 **Natural Language Processing**
- **Intent Classification**: Regex-based pattern matching for financial queries
- **Contextual Understanding**: Recognizes financial terminology and time periods
- **Extensible Architecture**: Easy to upgrade to LLM-based processing

### 📊 **Financial Metrics**
- **Revenue vs Budget**: Variance analysis with percentage calculations
- **Gross Margin**: `(Revenue - COGS) / Revenue * 100`
- **EBITDA Proxy**: `Revenue - COGS - Operating Expenses`
- **Cash Runway**: `Current Cash / Average Monthly Burn Rate`
- **Burn Rate**: `Revenue - Total Expenses` (monthly)

### 📈 **Advanced Analytics**
- **Trend Analysis**: Moving averages and growth calculations
- **Variance Analysis**: Budget vs actual performance tracking
- **Seasonality Detection**: Month-over-month and year-over-year comparisons
- **Forecasting**: Basic trend extrapolation

### 🎯 **Executive Dashboards**
- **KPI Cards**: Key metrics with variance indicators
- **Multi-Chart Layouts**: Comprehensive financial overviews
- **Interactive Elements**: Drill-down capabilities and filtering
- **Professional Styling**: Corporate color schemes and typography

## 🚀 Advanced Usage

### 📄 **PDF Export**
Generate professional financial reports:
1. Navigate to the sidebar
2. Click "Generate Executive Dashboard PDF"
3. Download your board-ready financial summary

### 🔧 **Customization**
- **Color Themes**: Modify `PLOTLY_THEME` in `app.py`
- **Metrics**: Add custom calculations in `agent/tools.py`
- **Intent Recognition**: Extend patterns in `agent/intent.py`

### 🔌 **Integration**
- **Data Sources**: Easy to connect to databases or APIs
- **Export Formats**: Extend to Excel, PowerBI, or other formats
- **Scheduling**: Add automated report generation

## 🛠️ Development

### 🏗️ **Architecture Principles**
- **Modular Design**: Separated concerns for analytics, UI, and data processing
- **Testable Code**: Comprehensive test suite with 23+ test cases
- **Extensible Framework**: Easy to add new metrics and visualizations
- **Professional Standards**: Type hints, documentation, and error handling

### 🔧 **Technology Stack**
- **Frontend**: Streamlit for interactive web interface
- **Data Processing**: Pandas for financial data manipulation
- **Visualizations**: Plotly for interactive charts
- **PDF Generation**: Matplotlib for executive reports
- **Testing**: Pytest for comprehensive test coverage

## 📖 Documentation

### 🎓 **Learning Resources**
- **Financial Metrics**: Understanding CFO-level KPIs
- **Data Analysis**: Financial statement analysis techniques  
- **Visualization**: Best practices for executive reporting

### 🔍 **Troubleshooting**
- **Data Issues**: Check CSV format and column names
- **Performance**: Monitor large dataset processing
- **Dependencies**: Ensure all packages are installed correctly

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines for:
- **Code Standards**: Python PEP 8 compliance
- **Testing Requirements**: Add tests for new features
- **Documentation**: Update README for new functionality

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Financial Data Standards**: Following industry best practices
- **Open Source Libraries**: Built on excellent Python ecosystem
- **Community Feedback**: Continuous improvement based on user needs

---

**💡 Questions or Need Help?**
- 📧 Create an issue for bugs or feature requests
- 📚 Check the documentation for detailed guides
- 🤝 Contribute to make it even better!

**🚀 Ready to transform your financial analysis? Get started now!**
