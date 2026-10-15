# ShopSphere E-Commerce Analytics

An end-to-end portfolio project that demonstrates data cleaning, exploratory analysis, business-focused aggregation, and an interactive dashboard using a **synthetic** e-commerce dataset for 2025.

> **Data disclaimer:** ShopSphere and all records in this project are fictional/synthetic. The results are for analytics demonstration only and do not describe a real business.

## Project Highlights

- Assessed and cleaned missing values, duplicate records, inconsistent city/status labels, missing unit prices, and invalid quantities.
- Engineered date fields and profit margin.
- Analyzed revenue, profit, product performance, customer value, city performance, discounts, order status, and weekday trends.
- Built a separate interactive Streamlit dashboard with date and category filters, KPI cards, and Plotly charts.
- Exported cleaned data and summary tables for reuse.

## Key Results

The reproducible notebook run in this repository produces the following cleaned-data totals:

| KPI | Result |
|---|---:|
| Cleaned order records | 14,980 |
| Unique customers | 2,000 |
| Total revenue | ₹647.97M |
| Total profit | ₹178.15M |
| Overall profit margin | 27.49% |
| Average order value | ₹43,255.96 |
| Units sold | 45,168 |

These totals include all order statuses because the source data assigns revenue and profit to Completed, Cancelled, and Returned records. They should **not** be interpreted as verified net sales. A real business analysis would reconcile payment, fulfillment, cancellation, and refund information first.

## Repository Structure

```text
shopsphere_portfolio/
├── ECommerce_Analysis.ipynb
├── dashboard.py
├── requirements.txt
├── README.md
├── .gitignore
├── data/
│   ├── ecommerce_orders.csv
│   └── cleaned_ecommerce_orders.csv
└── outputs/
    ├── city_sales.csv
    ├── customer_segments.csv
    ├── monthly_sales.csv
    ├── order_status.csv
    ├── payment_methods.csv
    └── product_sales.csv
```

## Run the Notebook

Use Python 3.10 or newer.

1. Download or clone this repository.
2. Open a terminal in the project folder.
3. Create and activate a virtual environment (recommended).
4. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. Start Jupyter:

   ```bash
   jupyter notebook
   ```

6. Open `ECommerce_Analysis.ipynb` and run the notebook from top to bottom.

The notebook reads `data/ecommerce_orders.csv`, creates a reproducible messy copy in memory, performs the quality checks and cleaning, then writes the cleaned dataset and summary tables to `data/` and `outputs/`.

## Run the Interactive Dashboard

After running the notebook at least once:

```bash
streamlit run dashboard.py
```

The dashboard opens in your browser. Use the sidebar to filter by date range, city, product category, order status, and payment method. The KPI cards and charts update to match the selected filters.

## Main Tools

- Python
- Pandas and NumPy
- Matplotlib
- Jupyter Notebook
- Streamlit and Plotly
- Git and GitHub

## Important Methodology Notes

- The dataset is synthetic and intentionally includes simulated data-quality problems during the notebook workflow.
- Missing unit prices are estimated using `Revenue / (Quantity × (1 − Discount))`, rounded to two decimal places.
- Records with non-positive quantities are excluded from the cleaned analysis.
- Customer segments are defined for this project as one-time (1 order), occasional (2–4 orders), and frequent (5+ orders).
- The product priority score combines revenue, profit, and margin ranks with equal weight. It is a simple screening method, not a validated decision model.
- Discount comparisons are descriptive; they do not prove that discounts cause changes in revenue or profit.

## Future Improvements

- Add a validated SQL analysis layer.
- Build a Power BI version of the dashboard if Power BI is part of the intended portfolio.
- Add tests for data-quality rules and financial reconciliation.
- Use real order lifecycle and refund fields to calculate net sales more accurately.
