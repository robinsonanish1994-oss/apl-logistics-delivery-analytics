"""Reproducible EDA for the research paper.

Run from the repository root:
    python -m analysis.run_analysis

Writes summary tables to reports/tables/ and figures to reports/figures/.
"""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from src.data_prep import build_clean_file, load_clean, MODE_ORDER, RAW_PATH
    from src.kpis import headline, group_kpis
    ROOT = Path(__file__).resolve().parents[1]
except ImportError:  # flat layout
    from data_prep import build_clean_file, load_clean, MODE_ORDER, RAW_PATH
    from kpis import headline, group_kpis
    ROOT = Path(__file__).resolve().parent
FIG = ROOT / "reports" / "figures"
TAB = ROOT / "reports" / "tables"
FIG.mkdir(parents=True, exist_ok=True)
TAB.mkdir(parents=True, exist_ok=True)

# Palette (validated reference palette; status colours for delivery classes)
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
GOOD, CRIT = "#0ca30c", "#d03b3b"
CLASS_COL = {"Early": BLUE, "On-time": GOOD, "Delayed": CRIT}
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": GRID,
    "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
    "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
    "axes.titlesize": 12, "axes.titleweight": "bold", "axes.titlecolor": INK,
    "figure.dpi": 160, "savefig.bbox": "tight",
})


def save(fig, name):
    fig.savefig(FIG / name, facecolor="white")
    plt.close(fig)


def main():
    audit = build_clean_file() if RAW_PATH.exists() else {"note": "raw CSV not present; using cleaned parquet"}
    df = load_clean()
    raw_late_ratio = 98977 / 180519  # reference: includes cancelled rows

    out = {"audit": audit, "headline": headline(df)}

    # ---- Delivery class distribution --------------------------------------
    cls = df["Delivery Class"].value_counts().reindex(["Early", "On-time", "Delayed"])
    out["class_counts"] = cls.to_dict()
    gap_dist = df["Delay Gap"].value_counts().sort_index()
    out["gap_distribution"] = {int(k): int(v) for k, v in gap_dist.items()}

    # ---- Group KPI tables ----------------------------------------------------
    tables = {
        "shipping_mode": group_kpis(df, "Shipping Mode"),
        "market": group_kpis(df, "Market"),
        "order_region": group_kpis(df, "Order Region"),
        "order_country": group_kpis(df, "Order Country", min_orders=500),
        "customer_segment": group_kpis(df, "Customer Segment"),
        "department": group_kpis(df, "Department Name"),
        "payment_type": group_kpis(df, "Type"),
    }
    for k, t in tables.items():
        t.to_csv(TAB / f"{k}.csv", index=False)
        out[k] = t.round(4).to_dict(orient="records")

    # Mode x delivery class crosstab (share of rows)
    mx = pd.crosstab(df["Shipping Mode"], df["Delivery Class"], normalize="index") * 100
    mx.round(2).to_csv(TAB / "mode_by_class.csv")
    out["mode_by_class"] = mx.round(2).to_dict(orient="index")
    # Mode x delay gap
    mg = pd.crosstab(df["Shipping Mode"], df["Delay Gap"])
    mg.to_csv(TAB / "mode_by_gap.csv")
    out["mode_by_gap"] = {str(i): {int(c): int(v) for c, v in r.items()} for i, r in mg.iterrows()}
    # Segment x mode late ratio
    sm = df.pivot_table(index="Customer Segment", columns="Shipping Mode",
                        values="Is Late", aggfunc="mean", observed=True) * 100
    sm.round(2).to_csv(TAB / "segment_by_mode.csv")
    out["segment_by_mode"] = sm.round(2).to_dict(orient="index")
    # Market x mode late ratio
    mm = df.pivot_table(index="Market", columns="Shipping Mode",
                        values="Is Late", aggfunc="mean", observed=True) * 100
    mm.round(2).to_csv(TAB / "market_by_mode.csv")
    out["market_by_mode"] = mm.round(2).to_dict(orient="index")
    # Mode mix per market (share of orders)
    mix = pd.crosstab(df["Market"], df["Shipping Mode"], normalize="index") * 100
    out["market_mode_mix"] = mix.round(2).to_dict(orient="index")
    # Sales exposure for late orders by segment
    out["late_sales_share"] = float(df.loc[df["Is Late"] == 1, "Sales"].sum() / df["Sales"].sum())
    out["late_sales_value"] = float(df.loc[df["Is Late"] == 1, "Sales"].sum())
    out["total_sales"] = float(df["Sales"].sum())
    # Profit comparison
    out["profit_by_class"] = df.groupby("Delivery Class", observed=True)["Order Profit Per Order"].mean().round(2).to_dict()
    # Counterfactual: if First Class shipped in its 2-day real time with a 2-day SLA
    fc = df["Shipping Mode"] == "First Class"
    out["first_class_all_gap1"] = bool((df.loc[fc, "Delay Gap"] == 1).all())
    sim = df.copy()
    sim.loc[fc, "Days for shipment (scheduled)"] = 2
    sim["Delay Gap"] = sim["Days for shipping (real)"] - sim["Days for shipment (scheduled)"]
    out["sim_on_time_if_first_class_sla_2d"] = float((sim["Delay Gap"] <= 0).mean() * 100)
    # Same day SLA set to 1 day
    sd = df["Shipping Mode"] == "Same Day"
    sim.loc[sd, "Days for shipment (scheduled)"] = 1
    sim["Delay Gap"] = sim["Days for shipping (real)"] - sim["Days for shipment (scheduled)"]
    out["sim_on_time_if_fc2_sd1"] = float((sim["Delay Gap"] <= 0).mean() * 100)
    # Standard/Second variance: real days are ~uniform
    out["real_days_std_by_mode"] = df.groupby("Shipping Mode", observed=True)["Days for shipping (real)"].std().round(3).to_dict()
    out["raw_late_ratio_incl_cancelled"] = raw_late_ratio
    # spread of late ratio across geographies
    for k in ("market", "order_region", "order_country"):
        t = tables[k]
        out[f"{k}_late_ratio_range"] = [float(t["Late_Ratio_%"].min()), float(t["Late_Ratio_%"].max())]

    # Chi-square test of independence + Cramer's V for each dimension vs lateness
    rows = []
    for c in ["Shipping Mode", "Order Country", "Order Region", "Market", "Department Name", "Type", "Customer Segment"]:
        ct = pd.crosstab(df[c], df["Is Late"])
        chi2, p, dof, _ = chi2_contingency(ct)
        v = float(np.sqrt(chi2 / (ct.values.sum() * (min(ct.shape) - 1))))
        rows.append({"Dimension": c, "chi2": round(chi2, 1), "dof": dof, "p_value": p, "cramers_v": round(v, 3)})
    chi = pd.DataFrame(rows)
    chi.to_csv(TAB / "chi_square_tests.csv", index=False)
    out["chi_square"] = chi.to_dict(orient="records")

    with open(TAB / "summary.json", "w") as f:
        json.dump(out, f, indent=2, default=str)

    # ======================= FIGURES =========================================
    # Fig 1: delivery class split
    fig, ax = plt.subplots(figsize=(7, 2.2))
    left = 0
    tot = cls.sum()
    for k, v in cls.items():
        ax.barh([0], [v], left=left, color=CLASS_COL[k], height=0.5, edgecolor="white", linewidth=2)
        ax.text(left + v / 2, 0, f"{k}\n{v/tot:.1%}", ha="center", va="center", color="white", fontsize=10, weight="bold")
        left += v
    ax.set_yticks([]); ax.set_xlim(0, tot); ax.grid(False)
    ax.set_xlabel("Delivered orders"); ax.set_title("Fig. 1 - Delivery outcome vs scheduled shipping time", loc="left")
    save(fig, "fig1_delivery_class.png")

    # Fig 2: delay-gap histogram
    fig, ax = plt.subplots(figsize=(7, 3.2))
    cols = [BLUE if g < 0 else GOOD if g == 0 else CRIT for g in gap_dist.index]
    ax.bar(gap_dist.index, gap_dist.values, color=cols, width=0.7)
    for x, y in gap_dist.items():
        ax.text(x, y, f"{y/len(df):.1%}", ha="center", va="bottom", fontsize=8.5, color=INK2)
    ax.set_xlabel("Delay gap (actual - scheduled days)"); ax.set_ylabel("Orders")
    ax.set_title("Fig. 2 - Distribution of delivery delay gap", loc="left")
    save(fig, "fig2_delay_gap_hist.png")

    # Fig 3: late ratio by shipping mode + avg gap
    t = tables["shipping_mode"].set_index("Shipping Mode").reindex(MODE_ORDER)
    fig, ax = plt.subplots(figsize=(7, 3))
    ax.barh(t.index.astype(str), t["Late_Ratio_%"], color=BLUE, height=0.55)
    for i, (r, g) in enumerate(zip(t["Late_Ratio_%"], t["Avg_Delay_Gap"])):
        ax.text(r + 1, i, f"{r:.1f}% late  |  avg gap {g:+.2f} d", va="center", fontsize=9, color=INK)
    ax.set_xlim(0, 125); ax.invert_yaxis(); ax.set_xlabel("Late delivery ratio (%)")
    ax.set_title("Fig. 3 - Late delivery ratio by shipping mode", loc="left")
    save(fig, "fig3_mode_late_ratio.png")

    # Fig 4: scheduled vs actual days by mode
    fig, ax = plt.subplots(figsize=(7, 3))
    y = range(len(t))
    ax.barh([i - 0.18 for i in y], t["Avg_Sched_Days"], height=0.34, color=AQUA, label="Scheduled (SLA) days")
    ax.barh([i + 0.18 for i in y], t["Avg_Real_Days"], height=0.34, color=ORANGE, label="Actual days (mean)")
    ax.set_yticks(list(y)); ax.set_yticklabels(t.index.astype(str)); ax.invert_yaxis()
    ax.set_xlabel("Days"); ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.22), ncol=2)
    ax.set_title("Fig. 4 - Planned vs actual shipping days by mode", loc="left")
    save(fig, "fig4_sched_vs_real.png")

    # Fig 5: market late ratio
    tm = tables["market"].sort_values("Late_Ratio_%")
    fig, ax = plt.subplots(figsize=(7, 2.8))
    ax.barh(tm["Market"], tm["Late_Ratio_%"], color=BLUE, height=0.55)
    for i, (r, n) in enumerate(zip(tm["Late_Ratio_%"], tm["Orders"])):
        ax.text(r + 0.3, i, f"{r:.2f}%  (n={n:,})", va="center", fontsize=9)
    ax.set_xlim(50, 62); ax.set_xlabel("Late delivery ratio (%)")
    ax.set_title("Fig. 5 - Late delivery ratio by market (axis starts at 50%)", loc="left")
    save(fig, "fig5_market.png")

    # Fig 6: region late ratio
    tr = tables["order_region"].sort_values("Late_Ratio_%")
    fig, ax = plt.subplots(figsize=(7, 5.5))
    overall = df["Is Late"].mean() * 100
    ax.barh(tr["Order Region"], tr["Late_Ratio_%"],
            color=[CRIT if v > overall else BLUE for v in tr["Late_Ratio_%"]], height=0.6)
    ax.axvline(overall, color=INK2, lw=1, ls="--"); ax.text(overall + 0.1, -0.9, f"network avg {overall:.1f}%", fontsize=8.5, color=INK2)
    ax.set_xlim(50, 63); ax.set_xlabel("Late delivery ratio (%)")
    ax.set_title("Fig. 6 - Late delivery ratio by order region (red = above average)", loc="left")
    save(fig, "fig6_region.png")

    # Fig 7: top countries (>=500 orders)
    tc = tables["order_country"].head(15).sort_values("Late_Ratio_%")
    fig, ax = plt.subplots(figsize=(7, 4.6))
    ax.barh(tc["Order Country"], tc["Late_Ratio_%"], color=CRIT, height=0.6)
    for i, (r, n) in enumerate(zip(tc["Late_Ratio_%"], tc["Orders"])):
        ax.text(r + 0.2, i, f"{r:.1f}%  (n={n:,})", va="center", fontsize=8.5)
    ax.set_xlim(50, 68); ax.set_xlabel("Late delivery ratio (%)")
    ax.set_title("Fig. 7 - 15 highest-risk countries (min. 500 orders)", loc="left")
    save(fig, "fig7_countries.png")

    # Fig 8: segment x mode heat table
    fig, ax = plt.subplots(figsize=(7, 2.6))
    sm2 = sm[MODE_ORDER]
    im = ax.imshow(sm2.values, cmap="Blues", vmin=30, vmax=100, aspect="auto")
    ax.set_xticks(range(len(sm2.columns))); ax.set_xticklabels(sm2.columns)
    ax.set_yticks(range(len(sm2.index))); ax.set_yticklabels(sm2.index); ax.grid(False)
    for i in range(sm2.shape[0]):
        for j in range(sm2.shape[1]):
            v = sm2.values[i, j]
            ax.text(j, i, f"{v:.1f}%", ha="center", va="center", color="white" if v > 70 else INK, fontsize=9.5)
    ax.set_title("Fig. 8 - Late ratio by customer segment x shipping mode", loc="left")
    save(fig, "fig8_segment_mode.png")

    print(json.dumps({"audit": audit, "headline": out["headline"]}, indent=2, default=str))


if __name__ == "__main__":
    main()
