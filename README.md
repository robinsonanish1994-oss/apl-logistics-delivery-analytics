# 🚚 Delivery Performance, Delay Risk & Logistics Efficiency Analysis
### Global Supply Chain Operations · APL Logistics (KWE Group) · Unified Mentor Internship Project

An end-to-end diagnostic analytics project that measures on-time delivery performance, explains the drivers of
`Late_delivery_risk`, and finds high-risk shipping modes, regions, markets and customer segments. It includes an
interactive **Streamlit dashboard**.

**🔗 Live dashboard:** `<your-app>.streamlit.app` &nbsp;|&nbsp; **📄 Research paper:** [research_paper.pdf](research_paper.pdf) &nbsp;|&nbsp; **📝 Executive summary:** [executive_summary.pdf](executive_summary.pdf) &nbsp;|&nbsp;

---

## Key findings

| KPI | Value |
|---|---|
| Orders analysed (after cleaning) | **172,765** (7,754 cancelled shipments removed from 180,519) |
| On-Time Delivery Rate | **42.7%** (24.1% early + 18.6% exactly on time) |
| Late Delivery Risk Ratio | **0.573** |
| Average Delivery Delay | **+0.57 days** overall · **+1.62 days** for late orders |
| Sales on late orders | **$20.1M** of $35.2M (57.2%) |

| Shipping mode | Scheduled | Actual (mean) | Late ratio | Efficiency index |
|---|---|---|---|---|
| First Class | 1 day | 2.00 days | **100.0%** | 1.75 |
| Second Class | 2 days | 3.99 days | **79.8%** | 1.39 |
| Same Day | 0 days | 0.48 days | 47.9% | 0.84 |
| Standard Class | 4 days | 3.99 days | 39.8% | 0.69 |

1. **Shipping mode is the main driver of delay** (Cramér's V = 0.48). First Class always takes 2 days against a 1-day
   promise. Second Class has the *same* 2–6 day transit distribution as Standard Class.
2. **Market, customer segment, department and payment type have no meaningful effect** (V ≤ 0.007).
3. **Regional differences are real but small**: Canada has the lowest late ratio (51.6%) and Central Africa the
   highest (60.1%). Western Europe/Germany combines above-average delay with high volume.
4. **Realigning promises with true capability** lifts the on-time rate from 42.7% to 58–68%. **Fixing premium-lane
   execution** could reach about 74%.

## Dashboard modules
| Module | Contents |
|---|---|
| 📊 Delivery Performance Overview | On-time vs late KPIs, delay scorecards, KPI table vs network baseline |
| ⚠️ Delay Risk Analysis | `Late_delivery_risk` distribution, delay-gap histogram, gap by mode, status tables |
| 🚛 Shipping Mode Comparison | Planned vs actual days, Shipping Mode Efficiency Index, SLA compliance by mode × market |
| 🌍 Regional & Market Heatmaps | World choropleth, market efficiency, Regional Delay Index, region × mode heatmap, top-risk countries |

**Filters:** shipping mode · market · order region · customer segment · scheduled-SLA band · order-date range.
The date selector activates automatically if the data contains an order-date column. The supplied extract has none.

## Methodology
1. **Cleaning & validation:** shipping durations validated; missing and duplicate records checked; *Shipping canceled*
   rows removed; `Late_delivery_risk` cross-checked against `Delivery Status` (0 conflicts).
2. **Standardisation:** Spanish country names mapped to English and ISO-3 codes; region whitespace fixed; customer PII dropped.
3. **Delay Gap** = `Days for shipping (real)` − `Days for shipment (scheduled)` → Early / On-time / Delayed.
4. **KPIs:** On-Time Delivery Rate, Average Delivery Delay, Late Delivery Risk Ratio, Shipping Mode Efficiency Index,
   Regional Delay Index (group late ratio ÷ network late ratio).
5. **Statistics:** chi-square tests of independence and Cramér's V for each dimension.

## Repository structure
| File(s) | Purpose |
|---|---|
| `app.py` | Streamlit dashboard |
| `requirements.txt` | Python dependencies |
| `data_prep.py` | Cleaning, validation, standardisation, delay-gap calculation |
| `kpis.py` | KPI and index definitions (shared by the dashboard and the paper) |
| `country_map.py` | Spanish → English country names + ISO-3 codes |
| `run_analysis.py` | Reproduces every table and figure in the paper |
| `apl_logistics_clean.parquet` | Cleaned dataset (172,765 delivered orders) used by the app |
| `APL_Logistics.csv.gz` | Original raw dataset (180,519 records, gzip-compressed) |
| `research_paper.pdf` / `.html` | Research paper (EDA, insights, recommendations) |
| `executive_summary.pdf` / `.html` | Executive summary for government stakeholders |
| `fig*.png`, `dashboard_*.png` | Figures and dashboard screenshots used in the paper |
| `*.csv`, `summary.json` | KPI tables produced by `run_analysis.py` |
| `.streamlit/config.toml` | Dashboard colour theme |

## Run locally
```bash
git clone https://github.com/robinsonanish1994-oss/apl-logistics-delivery-analytics.git
cd apl-logistics-delivery-analytics
pip install -r requirements.txt
streamlit run app.py                 # dashboard at http://localhost:8501
python run_analysis.py               # regenerate paper figures and tables (optional)
```

## Tech stack
Python · pandas · NumPy · Plotly · Streamlit · SciPy · Matplotlib

## Author
**Anish R**, Data Analytics Intern, Unified Mentor · Project with APL Logistics (KWE Group)
