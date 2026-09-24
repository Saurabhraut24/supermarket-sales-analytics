# Supermarket Sales Analytics Dashboard

## Project Overview
An interactive Streamlit dashboard built as part of the **AICTE | IBM SkillsBuild Data Analytics with AI Internship 2026 (BharatCares)** programme.  
The dashboard performs end-to-end analysis of a supermarket's sales data — from data cleaning to advanced visualizations and business insights.


## Live Demo

https://supermarket-sales-analytics-hq5hhidaobpoagh5r2byrf.streamlit.app/

**Student:** Saurabh Raut  
**Institute:** Walchand Institute of Technology, Solapur  
**Department:** Electronics and Computer Engineering

---

## Dataset
- **File:** `SuperMarket Analysis.csv`  
- **Source:** [Kaggle – Supermarket Sales Dataset](https://www.kaggle.com/datasets/aungpyaeap/supermarket-sales)  
- **Size:** ~1,000 rows × 17 columns  
- **Features:** Invoice ID, Branch, City, Customer type, Gender, Product line, Unit price, Quantity, Tax 5%, Sales, Date, Time, Payment, COGS, Gross margin percentage, Gross income, Rating

---

## Technologies Used
| Library | Purpose |
|---|---|
| Python 3.9+ | Core language |
| Streamlit | Interactive web dashboard |
| Pandas | Data manipulation & cleaning |
| NumPy | Numerical computations |
| Plotly | Interactive charts & visualizations |
| Scikit-learn | Machine learning (predictive analysis) |

---

## Features
- **Data Overview** – Dataset summary, shape, types, and missing value report
- **Sales Analysis** – Revenue trends, branch comparisons, peak hours
- **Product Analysis** – Best/worst product lines, profitability breakdown
- **Customer Analysis** – Gender, customer type, and payment preference insights
- **Predictive Insights** – Sales forecasting and rating prediction using ML
- **File Upload** – Supports custom CSV datasets with schema validation

---

## Setup & Run Instructions

### 1. Clone / Download the project
Place these files in a single folder:
```
Saurabh_Supermarket_Analytics.py
SuperMarket Analysis.csv
requirements.txt
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the dashboard
```bash
streamlit run Saurabh_Supermarket_Analytics.py
```

The app will open automatically at `http://localhost:8501`

---

## Key Insights
- **Branch C** generates the highest gross income on average
- **Food and Beverages** is the top-selling product line
- **E-wallet** is the most preferred payment method
- **Peak sales hours** are between 7 PM – 9 PM
- Customer **ratings average 6.97** across all branches

---

## Submission Files
| File | Description |
|---|---|
| `Saurabh_Supermarket_Analytics.py` | Complete project code (single self-contained script) |
| `SuperMarket Analysis.csv` | Dataset used for analysis |
| `requirements.txt` | Python dependencies |
| `README.md` | This file – project overview |
| `Saurabh_Supermarket_Sales_ProjectReport.docx` | Detailed project report |

---

*AICTE \| IBM SkillsBuild Data Analytics with AI Internship 2026 \| BharatCares*
