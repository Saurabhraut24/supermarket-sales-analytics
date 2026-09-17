# SuperMarket Sales Analytics Dashboard

![Python](https://img.shields.io/badge/Python-3.9%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32%2B-red)
![Plotly](https://img.shields.io/badge/Plotly-5.18%2B-green)

## Project Overview

A professional, interactive business intelligence dashboard built with Python and Streamlit for analysing supermarket sales data. The dashboard provides comprehensive analytics including KPI tracking, sales trends, product performance, customer behaviour, payment analysis, gross income / financial analysis, and automated business insights — all calculated dynamically from the dataset.

Built as part of the **AICTE | IBM SkillsBuild Data Analytics with AI Internship 2026 | BharatCares** programme.

**Student:** Saurabh Raut  
**Institute:** Walchand Institute of Technology, Solapur  
**Dept:** Electronics and Computer Engineering

## Objectives

- Provide real-time KPI monitoring (Total Sales, Gross Income, Transactions, Avg Rating)
- Identify top and bottom performing product lines
- Analyse customer behaviour by type, gender, and payment preference
- Surface peak sales hours, days, and months
- Perform gross income and financial (COGS / margin) analysis
- Enable branch and city-level performance comparison
- Perform customer rating analysis across product lines and branches
- Support CSV upload for reuse with different compatible datasets
- Generate dynamic business insights automatically from data

## Dataset

**File:** `data/SuperMarket Analysis.csv`  
**Source:** [Kaggle — Supermarket Sales](https://www.kaggle.com/datasets/faresashraf1001/supermarket-sales)  
**Records:** 1,000 transactions | **Period:** January – March 2019

| Column | Description |
|--------|-------------|
| Invoice ID | Unique transaction identifier |
| Branch | Branch code (A, B, C) |
| City | City name (Yangon, Naypyitaw, Mandalay) |
| Customer type | Member or Normal |
| Gender | Male or Female |
| Product line | Product category (6 lines) |
| Unit price | Price per unit ($) |
| Quantity | Number of units |
| Tax 5% | 5% tax applied to COGS |
| Sales | Total sales including tax |
| Date | Transaction date |
| Time | Transaction time |
| Payment | Payment method (Cash, Ewallet, Credit card) |
| cogs | Cost of goods sold |
| gross margin percentage | Gross margin % (dynamically calculated) |
| gross income | Gross income earned (= Tax 5%) |
| Rating | Customer satisfaction rating (1–10) |

## Technologies

| Component | Technology |
|-----------|-----------|
| Language  | Python 3.9+ |
| Dashboard | Streamlit |
| Charts    | Plotly Express + Graph Objects |
| Data      | Pandas, NumPy |

## Project Structure

```
supermarket-analytics/
│
├── submission/
│   └── Saurabh_Supermarket_Analytics.py   ← Self-contained submission file
│
├── data/
│   └── SuperMarket Analysis.csv
│
├── charts/
│   ├── __init__.py
│   └── visualizations.py
│
├── utils/
│   ├── __init__.py
│   ├── analytics.py
│   ├── data_cleaning.py
│   ├── data_loader.py
│   └── insights.py
│
├── reports/
│   └── Saurabh_Supermarket_Sales_ProjectReport.docx
│
├── app.py
├── requirements.txt
├── README.md
└── .gitignore
```

## Installation

```bash
# 1. Clone or download the project
cd supermarket-analytics

# 2. Create a virtual environment (recommended)
python -m venv venv
.\venv\Scripts\activate   # Windows

# 3. Install dependencies
python -m pip install -r requirements.txt
```

## Run the Original Modular Dashboard

```bash
# From the supermarket-analytics/ directory
streamlit run app.py
```

## Run the Submission Version

```bash
# Self-contained — no external module dependencies
streamlit run submission/Saurabh_Supermarket_Analytics.py
```

The submission file is completely self-contained. It does **not** depend on `utils/`, `charts/`, or `app.py`. All logic is embedded in the single file.

## Features

- **Interactive Filters:** Date range, Branch, City, Customer Type, Gender, Product Line, Payment Method
- **8 Dynamic KPIs:** Total Sales, Gross Income, Transactions, Quantity, Avg Order Value, Avg Unit Price, Gross Margin %, Avg Rating
- **11 Analytics Tabs:**

| Tab | Content |
|-----|---------|
| 📊 Overview | KPIs, daily sales trend, product share, business insights |
| 📈 Sales Analytics | Time series, by branch/city/product/gender/payment |
| 📦 Product Analytics | Top/bottom performers, Pareto chart, avg price |
| 👥 Customer Analytics | Member vs Normal, gender analysis, ratings by type |
| 💰 Gross Income Analysis | Gross income trend, COGS, margin %, by product/branch |
| 🕐 Time Analysis | Peak hours, best day/month, hourly patterns |
| 💳 Payment Analysis | Method distribution, avg transaction by payment |
| 🏪 Branch & Location | Branch comparison, city performance |
| ⭐ Ratings | Distribution, by product/branch/gender, vs sales |
| 🔬 Advanced | Correlation matrix, Pareto, contribution % |
| 🗃️ Data Explorer | Raw data, stats, quality report, download |

- **Auto Business Insights:** Dynamically generated text insights from filtered data
- **CSV Upload:** Upload any compatible supermarket CSV
- **Data Export:** Download filtered dataset as CSV
- **Data Quality Report:** Missing values, duplicates, cleaning log

## Project Report

Full written project report:  
`reports/Saurabh_Supermarket_Sales_ProjectReport.docx`

## Code Submission

Official submission file:  
`submission/Saurabh_Supermarket_Analytics.py`

## Dataset Source

[https://www.kaggle.com/datasets/faresashraf1001/supermarket-sales](https://www.kaggle.com/datasets/faresashraf1001/supermarket-sales)

## GitHub Repository

GitHub Repository: [https://github.com/Saurabhraut24/supermarket-analytics](https://github.com/Saurabhraut24/supermarket-analytics)

## Uploading Another CSV

1. In the sidebar, click **"Upload Supermarket CSV"**
2. Select a compatible CSV file
3. The dashboard updates automatically with the new data

**Compatible CSV:** Must contain columns similar to the default dataset. Missing columns are derived automatically where possible; incompatible columns are handled gracefully with warnings.

## Future Improvements

- Forecasting using time-series models (Prophet, ARIMA)
- Multi-store comparison with uploaded datasets
- Export analytics reports to PDF
- Real-time database connectivity
- Mobile-responsive layout improvements
- Inventory integration

## Author

**Saurabh Raut**  
Walchand Institute of Technology, Solapur  
AICTE | IBM SkillsBuild Data Analytics with AI Internship 2026 | BharatCares
