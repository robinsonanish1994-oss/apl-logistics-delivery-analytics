"""KPI definitions used by both the analysis script and the Streamlit app."""
from __future__ import annotations

import pandas as pd


def headline(df: pd.DataFrame) -> dict:
    n = len(df)
    if n == 0:
        return dict(orders=0, on_time_rate=float("nan"), avg_delay=float("nan"),
                    avg_delay_late=float("nan"), late_ratio=float("nan"),
                    early_rate=float("nan"), exact_rate=float("nan"))
    return dict(
        orders=n,
        on_time_rate=df["Within SLA"].mean() * 100,           # delivered within scheduled time
        avg_delay=df["Delay Gap"].mean(),                     # mean actual - scheduled (days)
        avg_delay_late=df.loc[df["Is Late"] == 1, "Delay Gap"].mean(),
        late_ratio=df["Late_delivery_risk"].mean(),           # proportion of delayed shipments
        early_rate=(df["Delivery Class"] == "Early").mean() * 100,
        exact_rate=(df["Delivery Class"] == "On-time").mean() * 100,
    )


def group_kpis(df: pd.DataFrame, by: str, min_orders: int = 0) -> pd.DataFrame:
    """Per-group delivery KPIs + a Delay Index (group late ratio / overall late ratio)."""
    overall_late = df["Is Late"].mean()
    overall_gap = df["Delay Gap"].mean()
    g = (df.groupby(by, observed=True)
           .agg(Orders=("Is Late", "size"),
                Late_Orders=("Is Late", "sum"),
                Late_Ratio=("Is Late", "mean"),
                On_Time_Rate=("Within SLA", "mean"),
                Avg_Delay_Gap=("Delay Gap", "mean"),
                Avg_Real_Days=("Days for shipping (real)", "mean"),
                Avg_Sched_Days=("Days for shipment (scheduled)", "mean"),
                Sales=("Sales", "sum"))
           .reset_index())
    g = g[g["Orders"] >= min_orders]
    g["On_Time_Rate"] *= 100
    g["Late_Ratio_%"] = g["Late_Ratio"] * 100
    # Efficiency/Delay index: 1.00 = network average; >1 = worse than average
    g["Delay_Index"] = g["Late_Ratio"] / overall_late if overall_late else float("nan")
    g["Gap_vs_Network"] = g["Avg_Delay_Gap"] - overall_gap
    return g.sort_values("Late_Ratio", ascending=False).reset_index(drop=True)
