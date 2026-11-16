"""Data cleaning, validation and feature engineering for the APL Logistics dataset.

Pipeline (mirrors the project methodology):
1. Load raw CSV (latin-1 encoded).
2. Validate shipping-duration values (non-negative integers, plausible range).
3. Remove inconsistent / missing delivery records (cancelled shipments never
   completed delivery, so they are excluded from delivery-performance KPIs).
4. Standardise region, market and country naming.
5. Compute Delay Gap = Days for shipping (real) - Days for shipment (scheduled)
   and classify each delivery as Early / On-time / Delayed.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

try:  # package layout (src/country_map.py)
    from .country_map import COUNTRY_MAP, CUSTOMER_COUNTRY_MAP
except ImportError:  # flat layout (country_map.py next to this file)
    from country_map import COUNTRY_MAP, CUSTOMER_COUNTRY_MAP

HERE = Path(__file__).resolve().parent
# Works whether files sit in src/ + data/ folders or all at the repository root.
SEARCH_DIRS = [HERE, HERE / "data", HERE.parent / "data", HERE.parent]


def _find(*names: str) -> Path:
    for d in SEARCH_DIRS:
        for n in names:
            if (d / n).exists():
                return d / n
    return SEARCH_DIRS[0] / names[0]


RAW_PATH = _find("APL_Logistics.csv.gz", "APL_Logistics.csv")   # original dataset
CLEAN_PATH = _find("apl_logistics_clean.parquet")                # cleaned dataset used by the app

REAL = "Days for shipping (real)"
SCHED = "Days for shipment (scheduled)"

# Columns kept for the dashboard. Customer PII (name, street, zipcode) is dropped.
KEEP_COLS = [
    "Type", REAL, SCHED, "Benefit per order", "Sales per customer",
    "Delivery Status", "Late_delivery_risk", "Category Name",
    "Customer City", "Customer Country", "Customer Segment", "Customer State",
    "Department Name", "Latitude", "Longitude", "Market", "Order City",
    "Order Country", "Order Item Discount", "Order Item Discount Rate",
    "Order Item Product Price", "Order Item Profit Ratio", "Order Item Quantity",
    "Sales", "Order Item Total", "Order Profit Per Order", "Order Region",
    "Order State", "Order Status", "Product Name", "Product Price",
    "Shipping Mode",
]

# Optional date columns: used by the dashboard's date-range selector when present.
DATE_CANDIDATES = ["order date (DateOrders)", "Order Date", "order_date"]

MODE_ORDER = ["Same Day", "First Class", "Second Class", "Standard Class"]
CLASS_ORDER = ["Early", "On-time", "Delayed"]


def load_raw(path: Path | str = RAW_PATH) -> pd.DataFrame:
    return pd.read_csv(path, encoding="latin-1")


def clean(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Return (clean dataframe, audit log of what was removed/changed)."""
    log: dict = {"raw_rows": len(raw)}
    df = raw.copy()

    date_col = next((c for c in DATE_CANDIDATES if c in df.columns), None)
    cols = KEEP_COLS + ([date_col] if date_col else [])
    df = df[[c for c in cols if c in df.columns]]

    # --- 1. Validate shipping duration values -------------------------------
    for c in (REAL, SCHED):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    invalid = df[REAL].isna() | df[SCHED].isna() | (df[REAL] < 0) | (df[SCHED] < 0) \
        | (df[REAL] > 60) | (df[SCHED] > 60)
    log["invalid_duration_rows"] = int(invalid.sum())
    df = df[~invalid]

    # --- 2. Remove missing / inconsistent delivery records ------------------
    missing = df[["Delivery Status", "Shipping Mode", "Market", "Order Region",
                  "Order Country", "Late_delivery_risk"]].isna().any(axis=1)
    log["missing_key_field_rows"] = int(missing.sum())
    df = df[~missing]

    dups = df.duplicated()
    log["duplicate_rows"] = int(dups.sum())
    df = df[~dups]

    cancelled = df["Delivery Status"].eq("Shipping canceled")
    log["cancelled_rows_removed"] = int(cancelled.sum())
    df = df[~cancelled]

    # Late_delivery_risk must agree with the recorded delivery status
    inconsistent = (df["Late_delivery_risk"].eq(1) != df["Delivery Status"].eq("Late delivery"))
    log["risk_status_conflicts"] = int(inconsistent.sum())
    df = df[~inconsistent]

    # --- 3. Standardise naming ---------------------------------------------
    for c in df.select_dtypes(include=["object", "string"]).columns:
        df[c] = df[c].astype("string").str.strip().str.replace(r"\s+", " ", regex=True)
    df["Order Region"] = df["Order Region"].replace({"South of USA": "South of USA"})
    df["Market"] = df["Market"].replace({"USCA": "USCA (US & Canada)"})
    df["Order Country (ES)"] = df["Order Country"]
    df["Order Country"] = df["Order Country (ES)"].map(lambda x: COUNTRY_MAP.get(x, (x, None))[0])
    df["ISO3"] = df["Order Country (ES)"].map(lambda x: COUNTRY_MAP.get(x, (x, None))[1])
    df["Customer Country"] = df["Customer Country"].replace(CUSTOMER_COUNTRY_MAP)
    df["Order Status"] = df["Order Status"].str.replace("_", " ").str.title()
    log["unmapped_countries"] = sorted(df.loc[df["ISO3"].isna(), "Order Country"].unique().tolist())

    if date_col:
        df["Order Date"] = pd.to_datetime(df[date_col], errors="coerce")
        if date_col != "Order Date":
            df = df.drop(columns=[date_col])

    # --- 4. Delivery gap + classification -----------------------------------
    df["Delay Gap"] = (df[REAL] - df[SCHED]).astype(int)
    df["Delivery Class"] = np.select(
        [df["Delay Gap"] < 0, df["Delay Gap"] == 0], ["Early", "On-time"], "Delayed")
    df["Delivery Class"] = pd.Categorical(df["Delivery Class"], CLASS_ORDER, ordered=True)
    df["Is Late"] = (df["Delay Gap"] > 0).astype(int)
    df["Within SLA"] = 1 - df["Is Late"]
    df["Shipping Mode"] = pd.Categorical(df["Shipping Mode"], MODE_ORDER, ordered=True)

    log["clean_rows"] = len(df)
    return df.reset_index(drop=True), log


def build_clean_file(raw_path=RAW_PATH, out_path=CLEAN_PATH) -> dict:
    df, log = clean(load_raw(raw_path))
    df.to_parquet(out_path, index=False, compression="zstd")
    return log


def load_clean(path: Path | str = CLEAN_PATH) -> pd.DataFrame:
    if not Path(path).exists():
        build_clean_file(out_path=path)
    return pd.read_parquet(path)


if __name__ == "__main__":
    import json
    print(json.dumps(build_clean_file(), indent=2))
