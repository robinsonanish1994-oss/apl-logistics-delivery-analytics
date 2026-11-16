"""APL Logistics - Delivery Performance & Delay Risk Dashboard (Streamlit).

Run locally:  streamlit run app.py
"""
from __future__ import annotations

import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

try:  # folder layout: src/data_prep.py
    from src.data_prep import load_clean, MODE_ORDER
    from src.kpis import headline, group_kpis
except ImportError:  # flat layout: all files at the repository root
    from data_prep import load_clean, MODE_ORDER
    from kpis import headline, group_kpis

st.set_page_config(page_title="APL Logistics | Delivery Performance", page_icon="🚚",
                   layout="wide", initial_sidebar_state="expanded")

# ---------- palette (validated reference palette + reserved status colours) ----------
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
GOOD, CRIT = "#0ca30c", "#d03b3b"
CLASS_COLORS = {"Early": BLUE, "On-time": GOOD, "Delayed": CRIT}
MODE_COLORS = {"Same Day": BLUE, "First Class": ORANGE, "Second Class": AQUA, "Standard Class": YELLOW}
SEQ = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]
DIV = ["#2a78d6", "#86b6ef", "#f0efec", "#f19a99", "#d03b3b"]

st.markdown("""
<style>
.block-container {padding-top: 1.6rem;}
div[data-testid="stMetric"] {background: rgba(127,127,127,0.06); border: 1px solid rgba(127,127,127,0.18);
  border-radius: 10px; padding: 12px 16px;}
div[data-testid="stMetricLabel"] p {font-size: 0.85rem;}
.small-note {color: #8a8984; font-size: 0.82rem;}
</style>""", unsafe_allow_html=True)


@st.cache_data(show_spinner="Loading and cleaning shipment data...")
def get_data() -> pd.DataFrame:
    df = load_clean()
    df["Shipping Mode"] = pd.Categorical(df["Shipping Mode"].astype(str), MODE_ORDER, ordered=True)
    for c in ["Market", "Order Region", "Customer Segment", "Order Country", "Delivery Status"]:
        df[c] = df[c].astype(str)
    return df


def style_fig(fig, height=380):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=90, b=10),
                      font=dict(family="Inter, Segoe UI, sans-serif", size=13),
                      legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="left", x=0, title=None),
                      title=dict(y=0.98, yanchor="top", x=0, xanchor="left"),
                      plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      hoverlabel=dict(font_size=12))
    fig.update_xaxes(showgrid=True, gridcolor="rgba(127,127,127,0.18)", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="rgba(127,127,127,0.18)", zeroline=False)
    return fig


df_all = get_data()

# ======================= SIDEBAR FILTERS =======================
st.sidebar.title("🚚 APL Logistics")
st.sidebar.caption("Delivery Performance & Delay Risk")
st.sidebar.header("Filters")


def multiselect_all(label, options, key):
    sel = st.sidebar.multiselect(label, options, default=[], key=key, placeholder="All")
    return sel or list(options)


modes = multiselect_all("Shipping mode", MODE_ORDER, "mode")
markets = multiselect_all("Market", sorted(df_all["Market"].unique()), "market")
region_pool = sorted(df_all.loc[df_all["Market"].isin(markets), "Order Region"].unique())
regions = multiselect_all("Order region", region_pool, "region")
segments = multiselect_all("Customer segment", sorted(df_all["Customer Segment"].unique()), "segment")

# Date range selector: the source extract may or may not carry an order date.
date_range = None
if "Order Date" in df_all.columns and df_all["Order Date"].notna().any():
    dmin, dmax = df_all["Order Date"].min().date(), df_all["Order Date"].max().date()
    date_range = st.sidebar.date_input("Order date range", (dmin, dmax), min_value=dmin, max_value=dmax)
else:
    st.sidebar.date_input("Order date range", value=(), disabled=True,
                          help="The supplied APL extract has no order-date column. "
                               "Add 'order date (DateOrders)' to data/ and the selector activates automatically.")
    st.sidebar.markdown("<span class='small-note'>Date range unavailable: the provided dataset has no order-date "
                        "field. Use the scheduled-SLA filter below instead.</span>", unsafe_allow_html=True)

sla_days = st.sidebar.select_slider("Scheduled SLA (days)", options=[0, 1, 2, 4], value=(0, 4))

mask = (df_all["Shipping Mode"].astype(str).isin(modes) & df_all["Market"].isin(markets)
        & df_all["Order Region"].isin(regions) & df_all["Customer Segment"].isin(segments)
        & df_all["Days for shipment (scheduled)"].between(*sla_days))
if date_range and len(date_range) == 2:
    mask &= df_all["Order Date"].dt.date.between(*date_range)
df = df_all[mask]

st.sidebar.markdown("---")
st.sidebar.metric("Orders in view", f"{len(df):,}", f"{len(df)/len(df_all):.0%} of delivered orders",
                  delta_color="off", delta_arrow="off")
st.sidebar.caption("Cancelled shipments (7,754) are excluded: they never completed delivery.")

# ======================= HEADER =======================
st.title("Delivery Performance, Delay Risk & Logistics Efficiency")
st.caption("APL Logistics (KWE Group) · global order-level shipping data · "
           "Delay Gap = actual shipping days − scheduled shipping days")

if df.empty:
    st.warning("No orders match the current filters. Widen your selection in the sidebar.")
    st.stop()

k = headline(df)
k_all = headline(df_all)

tabs = st.tabs(["📊 Delivery Performance Overview", "⚠️ Delay Risk Analysis", "🚛 Shipping Mode Comparison",
                "🌍 Regional & Market Heatmaps"])

# ------------------------------------------------------------------ 1. OVERVIEW
with tabs[0]:
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("On-Time Delivery Rate", f"{k['on_time_rate']:.1f}%",
              f"{k['on_time_rate']-k_all['on_time_rate']:+.1f} pp vs network", delta_color="normal")
    c2.metric("Late Delivery Risk Ratio", f"{k['late_ratio']:.3f}",
              f"{(k['late_ratio']-k_all['late_ratio'])*100:+.1f} pp vs network", delta_color="inverse")
    c3.metric("Avg Delivery Delay", f"{k['avg_delay']:+.2f} days",
              f"{k['avg_delay']-k_all['avg_delay']:+.2f} d vs network", delta_color="inverse",
              help="Mean of (actual − scheduled) shipping days")
    c4.metric("Avg Delay (late orders)", f"{k['avg_delay_late']:.2f} days",
              help="Mean delay gap among orders that arrived late")
    c5.metric("Orders Analysed", f"{k['orders']:,}")

    left, right = st.columns([1, 1.25])
    with left:
        cls = df["Delivery Class"].value_counts().reindex(["Early", "On-time", "Delayed"]).reset_index()
        cls.columns = ["Delivery Class", "Orders"]
        fig = px.pie(cls, names="Delivery Class", values="Orders", hole=0.58, color="Delivery Class",
                     color_discrete_map=CLASS_COLORS, title="On-time vs late deliveries")
        fig.update_traces(textinfo="label+percent", sort=False,
                          marker=dict(line=dict(color="white", width=2)),
                          hovertemplate="%{label}: %{value:,} orders (%{percent})<extra></extra>")
        fig.update_layout(showlegend=False)
        st.plotly_chart(style_fig(fig), width="stretch")
    with right:
        sm = group_kpis(df, "Shipping Mode").set_index("Shipping Mode").reindex(
            [m for m in MODE_ORDER if m in df["Shipping Mode"].astype(str).unique()]).reset_index()
        fig = go.Figure()
        fig.add_bar(y=sm["Shipping Mode"].astype(str), x=sm["On_Time_Rate"], orientation="h", name="Within SLA",
                    marker_color=GOOD, text=sm["On_Time_Rate"].map("{:.1f}%".format), textposition="inside",
                    hovertemplate="%{y}: %{x:.1f}% within SLA<extra></extra>")
        fig.add_bar(y=sm["Shipping Mode"].astype(str), x=sm["Late_Ratio_%"], orientation="h", name="Late",
                    marker_color=CRIT, text=sm["Late_Ratio_%"].map("{:.1f}%".format), textposition="inside",
                    hovertemplate="%{y}: %{x:.1f}% late<extra></extra>")
        fig.update_layout(barmode="stack", title="Average delay scorecard by shipping mode",
                          xaxis_title="% of orders", yaxis=dict(autorange="reversed"))
        fig.update_traces(marker_line_color="white", marker_line_width=1.5)
        st.plotly_chart(style_fig(fig), width="stretch")

    st.subheader("KPI scorecard")
    score = pd.DataFrame({
        "KPI": ["On-Time Delivery Rate (%)", "Average Delivery Delay (days)", "Late Delivery Risk Ratio",
                "Early deliveries (%)", "Exactly on schedule (%)"],
        "Current view": [f"{k['on_time_rate']:.2f}", f"{k['avg_delay']:+.3f}", f"{k['late_ratio']:.4f}",
                         f"{k['early_rate']:.2f}", f"{k['exact_rate']:.2f}"],
        "Network baseline": [f"{k_all['on_time_rate']:.2f}", f"{k_all['avg_delay']:+.3f}",
                             f"{k_all['late_ratio']:.4f}", f"{k_all['early_rate']:.2f}", f"{k_all['exact_rate']:.2f}"],
        "Definition": ["Share of orders with actual ≤ scheduled days",
                       "Mean of (actual − scheduled) shipping days",
                       "Proportion of orders flagged Late_delivery_risk = 1",
                       "Actual < scheduled", "Actual = scheduled"]})
    st.dataframe(score, hide_index=True, width="stretch")

# ------------------------------------------------------------------ 2. DELAY RISK
with tabs[1]:
    c1, c2 = st.columns(2)
    with c1:
        risk = df["Late_delivery_risk"].map({0: "No risk (0)", 1: "Late (1)"}).value_counts().reset_index()
        risk.columns = ["Late_delivery_risk", "Orders"]
        fig = px.bar(risk, x="Late_delivery_risk", y="Orders", color="Late_delivery_risk", text="Orders",
                     color_discrete_map={"No risk (0)": GOOD, "Late (1)": CRIT},
                     title="Late_delivery_risk distribution")
        fig.update_traces(texttemplate="%{y:,}", hovertemplate="%{x}: %{y:,} orders<extra></extra>")
        fig.update_layout(showlegend=False, xaxis_title=None)
        st.plotly_chart(style_fig(fig), width="stretch")
    with c2:
        gap = df.groupby("Delay Gap").size().reset_index(name="Orders")
        gap["Class"] = gap["Delay Gap"].map(lambda g: "Early" if g < 0 else "On-time" if g == 0 else "Delayed")
        gap["Share"] = gap["Orders"] / gap["Orders"].sum()
        fig = px.bar(gap, x="Delay Gap", y="Orders", color="Class", color_discrete_map=CLASS_COLORS,
                     title="Delay gap histogram (actual − scheduled days)", custom_data=["Share"])
        fig.update_traces(hovertemplate="Gap %{x:+d} days: %{y:,} orders (%{customdata[0]:.1%})<extra></extra>")
        fig.update_layout(xaxis=dict(dtick=1, title="Delay gap (days)"), bargap=0.15)
        st.plotly_chart(style_fig(fig), width="stretch")

    st.subheader("Delay gap by shipping mode")
    box = df.groupby(["Shipping Mode", "Delay Gap"], observed=True).size().reset_index(name="Orders")
    box["Share"] = box["Orders"] / box.groupby("Shipping Mode", observed=True)["Orders"].transform("sum") * 100
    fig = px.bar(box, x="Delay Gap", y="Share", facet_col="Shipping Mode", facet_col_spacing=0.03,
                 category_orders={"Shipping Mode": MODE_ORDER}, color_discrete_sequence=[BLUE])
    fig.update_traces(hovertemplate="Gap %{x:+d} d: %{y:.1f}% of mode's orders<extra></extra>")
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    fig.update_yaxes(title=None); fig.update_yaxes(title="% of orders", col=1)
    fig.update_xaxes(dtick=1, title=None)
    st.plotly_chart(style_fig(fig, 320), width="stretch")
    st.info("**Reading the pattern:** First Class always arrives in 2 days against a 1-day promise (100% late). "
            "Second and Standard Class have the *same* actual-days distribution (uniform 2–6 days), so the tighter "
            "2-day Second Class promise is missed ~80% of the time.")

    st.subheader("Late ratio by delivery status & order status")
    c1, c2 = st.columns(2)
    with c1:
        ds = df.groupby("Delivery Status").agg(Orders=("Is Late", "size"), Avg_Gap=("Delay Gap", "mean")).reset_index()
        st.dataframe(ds.style.format({"Orders": "{:,}", "Avg_Gap": "{:+.2f}"}), hide_index=True,
                     width="stretch")
    with c2:
        os_ = group_kpis(df, "Order Status")[["Order Status", "Orders", "Late_Ratio_%", "Avg_Delay_Gap"]]
        st.dataframe(os_.style.format({"Orders": "{:,}", "Late_Ratio_%": "{:.1f}%", "Avg_Delay_Gap": "{:+.2f}"}),
                     hide_index=True, width="stretch")

# ------------------------------------------------------------------ 3. SHIPPING MODE
with tabs[2]:
    sm = group_kpis(df, "Shipping Mode")
    sm["Shipping Mode"] = sm["Shipping Mode"].astype(str)
    sm = sm.set_index("Shipping Mode").reindex([m for m in MODE_ORDER if m in sm["Shipping Mode"].values]).reset_index()
    cols = st.columns(len(sm))
    for col, (_, r) in zip(cols, sm.iterrows()):
        col.metric(f"{r['Shipping Mode']} · SLA met", f"{r['On_Time_Rate']:.1f}%",
                   f"Efficiency index {r['Delay_Index']:.2f}", delta_color="off", delta_arrow="off")
    st.caption("Shipping Mode Efficiency Index = mode late ratio ÷ network late ratio "
               "(1.00 = average; above 1 = less efficient).")

    c1, c2 = st.columns(2)
    with c1:
        long = sm.melt(id_vars="Shipping Mode", value_vars=["Avg_Sched_Days", "Avg_Real_Days"],
                       var_name="Measure", value_name="Days")
        long["Measure"] = long["Measure"].map({"Avg_Sched_Days": "Scheduled (SLA)", "Avg_Real_Days": "Actual (mean)"})
        fig = px.bar(long, y="Shipping Mode", x="Days", color="Measure", barmode="group", orientation="h",
                     color_discrete_map={"Scheduled (SLA)": AQUA, "Actual (mean)": ORANGE},
                     title="Planned vs actual shipping days")
        fig.update_traces(hovertemplate="%{y}: %{x:.2f} days<extra></extra>")
        fig.update_layout(yaxis=dict(autorange="reversed", title=None))
        st.plotly_chart(style_fig(fig), width="stretch")
    with c2:
        fig = px.bar(sm, y="Shipping Mode", x="Delay_Index", orientation="h", color="Shipping Mode",
                     color_discrete_map=MODE_COLORS, title="Shipping Mode Efficiency Index (lower is better)",
                     text=sm["Delay_Index"].map("{:.2f}".format))
        fig.add_vline(x=1, line_dash="dash", line_color="#8a8984", annotation_text="network avg")
        fig.update_traces(hovertemplate="%{y}: index %{x:.2f}<extra></extra>")
        fig.update_layout(showlegend=False, yaxis=dict(autorange="reversed", title=None),
                          xaxis_title="Late ratio ÷ network late ratio")
        st.plotly_chart(style_fig(fig), width="stretch")

    st.subheader("SLA compliance by mode and market")
    piv = df.pivot_table(index="Shipping Mode", columns="Market", values="Within SLA", aggfunc="mean",
                         observed=True) * 100
    fig = px.imshow(piv, text_auto=".1f", color_continuous_scale=SEQ, aspect="auto",
                    labels=dict(color="% within SLA"))
    fig.update_traces(hovertemplate="%{y} · %{x}: %{z:.1f}% within SLA<extra></extra>")
    st.plotly_chart(style_fig(fig, 320), width="stretch")

    st.dataframe(sm[["Shipping Mode", "Orders", "Late_Orders", "On_Time_Rate", "Late_Ratio_%", "Avg_Delay_Gap",
                     "Avg_Sched_Days", "Avg_Real_Days", "Delay_Index"]]
                 .style.format({"Orders": "{:,}", "Late_Orders": "{:,}", "On_Time_Rate": "{:.1f}%",
                                "Late_Ratio_%": "{:.1f}%", "Avg_Delay_Gap": "{:+.2f}", "Avg_Sched_Days": "{:.2f}",
                                "Avg_Real_Days": "{:.2f}", "Delay_Index": "{:.2f}"}),
                 hide_index=True, width="stretch")

# ------------------------------------------------------------------ 4. REGIONAL
with tabs[3]:
    metric_choice = st.radio("Map metric", ["Late ratio (%)", "Avg delay gap (days)", "Regional Delay Index"],
                             horizontal=True)
    min_n = st.slider("Minimum orders per country (filters out small-sample noise)", 0, 2000, 200, 50)
    cty = group_kpis(df, "Order Country", min_orders=min_n)
    iso = df.drop_duplicates("Order Country").set_index("Order Country")["ISO3"]
    cty["ISO3"] = cty["Order Country"].map(iso)
    col = {"Late ratio (%)": "Late_Ratio_%", "Avg delay gap (days)": "Avg_Delay_Gap",
           "Regional Delay Index": "Delay_Index"}[metric_choice]
    fig = px.choropleth(cty, locations="ISO3", color=col, hover_name="Order Country",
                        hover_data={"Orders": ":,", "Late_Ratio_%": ":.1f", "Avg_Delay_Gap": ":+.2f",
                                    "Delay_Index": ":.3f", "ISO3": False},
                        color_continuous_scale=SEQ, title=f"Geographic delay visualisation · {metric_choice}",
                        labels={"Late_Ratio_%": "Late ratio (%)", "Avg_Delay_Gap": "Avg gap (days)",
                                "Delay_Index": "Delay index"})
    fig.update_geos(showframe=False, showcoastlines=False, projection_type="natural earth",
                    projection_rotation=dict(lon=0, lat=0), lataxis_range=[-58, 85],
                    bgcolor="rgba(0,0,0,0)", showcountries=True, countrycolor="rgba(127,127,127,0.3)")
    # Map base layers load from Plotly's CDN by default; TOPOJSON_URL can point to a self-hosted copy.
    map_cfg = {"topojsonURL": os.environ["TOPOJSON_URL"]} if os.environ.get("TOPOJSON_URL") else {}
    st.plotly_chart(style_fig(fig, 470), width="stretch", config=map_cfg)

    c1, c2 = st.columns(2)
    with c1:
        mk = group_kpis(df, "Market").sort_values("Late_Ratio_%")
        fig = px.bar(mk, x="Late_Ratio_%", y="Market", orientation="h", color_discrete_sequence=[BLUE],
                     title="Market-wise logistics efficiency (late ratio %)",
                     text=mk["Late_Ratio_%"].map("{:.2f}%".format))
        fig.update_traces(hovertemplate="%{y}: %{x:.2f}% late<extra></extra>")
        lo = max(0, mk["Late_Ratio_%"].min() - 5)
        fig.update_xaxes(range=[lo, min(100, mk["Late_Ratio_%"].max() + 3)], title="Late ratio (%) - axis not at zero")
        fig.update_yaxes(title=None)
        st.plotly_chart(style_fig(fig), width="stretch")
    with c2:
        rg = group_kpis(df, "Order Region")
        overall = df["Is Late"].mean() * 100
        rg["vs avg"] = rg["Late_Ratio_%"] - overall
        rg = rg.sort_values("vs avg")
        fig = px.bar(rg, x="vs avg", y="Order Region", orientation="h", color="vs avg",
                     color_continuous_scale=DIV, color_continuous_midpoint=0,
                     title="Regional Delay Index · pp above/below network late ratio")
        fig.update_traces(hovertemplate="%{y}: %{x:+.2f} pp vs average<extra></extra>")
        fig.update_layout(coloraxis_showscale=False); fig.update_yaxes(title=None)
        fig.update_xaxes(title="Percentage points vs network average")
        st.plotly_chart(style_fig(fig, 560), width="stretch")

    st.subheader("Region × shipping mode heatmap (% late)")
    heat = df.pivot_table(index="Order Region", columns="Shipping Mode", values="Is Late", aggfunc="mean",
                          observed=True) * 100
    fig = px.imshow(heat, text_auto=".1f", color_continuous_scale=SEQ, aspect="auto", labels=dict(color="% late"))
    fig.update_traces(hovertemplate="%{y} · %{x}: %{z:.1f}% late<extra></extra>")
    st.plotly_chart(style_fig(fig, 620), width="stretch")

    st.subheader("Highest-risk countries")
    st.dataframe(cty.drop(columns=["ISO3"]).head(25)[["Order Country", "Orders", "Late_Ratio_%", "On_Time_Rate",
                                                       "Avg_Delay_Gap", "Delay_Index", "Sales"]]
                 .style.format({"Orders": "{:,}", "Late_Ratio_%": "{:.1f}%", "On_Time_Rate": "{:.1f}%",
                                "Avg_Delay_Gap": "{:+.2f}", "Delay_Index": "{:.3f}", "Sales": "${:,.0f}"}),
                 hide_index=True, width="stretch")
