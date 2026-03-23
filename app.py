import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="Urban Vista", layout="wide", page_icon="")

# ---------- SESSION STATE ----------
if "menu_open" not in st.session_state:
    st.session_state["menu_open"] = False
if "page" not in st.session_state:
    st.session_state["page"] = "Compare Cities"

# ---------- GLOBAL STYLES ----------
st.markdown("""
<style>
:root{
  --uv-bg: #f4f8fb;
  --uv-accent: #2e86de;
  --uv-dark: #0b132b;
}
.stApp {
    background: linear-gradient(180deg, var(--uv-bg) 0%, #e9f2fa 100%);
    color: var(--uv-dark);
    font-family: "Segoe UI", "Inter", sans-serif;
}

/* ---------- HERO TITLE ---------- */
.hero-container {
    width: 100%;
    text-align: center;
    margin: -2rem 0 3rem 0;
}
.uv-header {
    font-size: 8rem;
    font-weight: 900;
    letter-spacing: 2px;
    line-height: 1;
    background: linear-gradient(90deg, #2e86de, #0b132b);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-shadow: 0 6px 20px rgba(46,134,222,0.25);
    animation: fadeInScale 1.8s ease-out both;
}
.uv-sub {
    font-size: 2rem;
    color: var(--uv-accent);
    font-weight: 600;
    margin-top: 1rem;
    margin-bottom: 2rem;
    animation: fadeInUp 2.3s ease both;
}

/* --- Card design --- */
.uv-card {
    background: linear-gradient(180deg, rgba(255,255,255,0.9), rgba(245,247,250,0.95));
    border-radius: 10px;
    padding: 16px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.08);
    transition: all .25s ease;
}
.uv-card:hover {
    box-shadow: 0 6px 20px rgba(46,134,222,0.15);
    transform: translateY(-3px);
}

/* --- Misc --- */
.menu-panel { border-radius: 0 12px 12px 0; }
footer { visibility: hidden; }
.js-plotly-plot .plotly .main-svg { background: transparent !important; }

/* --- Slider labels --- */
.stSlider label, .stSlider span, .stSlider div {
    color: var(--uv-dark) !important;
    font-weight: 600;
}

/* --- Animations --- */
@keyframes fadeInScale {
  0% { opacity: 0; transform: scale(0.85); }
  100% { opacity: 1; transform: scale(1); }
}
@keyframes fadeInUp {
  0% { opacity: 0; transform: translateY(25px); }
  100% { opacity: 1; transform: translateY(0); }
}
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
header_col1, header_col2, header_col3 = st.columns([1, 10, 1])
with header_col1:
    if st.button("☰", key="menu_button"):
        st.session_state["menu_open"] = not st.session_state["menu_open"]
with header_col2:
    st.markdown("""
    <div class='hero-container'>
        <div class='uv-header'>Urban Vista 🌆</div>
        <div class='uv-sub'>City Livability Analyzer</div>
    </div>
    """, unsafe_allow_html=True)

# ---------- SIDEBAR ----------
if st.session_state["menu_open"]:
    with st.container():
        st.markdown("""
        <div class="menu-panel" style="background: linear-gradient(180deg,#f4f9ff 0%, #d9e8fa 100%);
                    padding:18px; box-shadow: 4px 0 14px rgba(46,134,222,0.15);">
        """, unsafe_allow_html=True)
        st.markdown("### Urban Vista")
        st.write("#### Navigate:")
        if st.button("Compare Cities"):
            st.session_state["page"] = "Compare Cities"
            st.session_state["menu_open"] = False
            st.rerun()
        if st.button("Summary Insights"):
            st.session_state["page"] = "Summary Insights"
            st.session_state["menu_open"] = False
            st.rerun()
        if st.button("About"):
            st.session_state["page"] = "About"
            st.session_state["menu_open"] = False
            st.rerun()
        st.divider()
        if st.button("Close Menu"):
            st.session_state["menu_open"] = False
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

# ---------- LOAD DATA ----------
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("Final_Dataset_Deploy.csv")
    except FileNotFoundError:
        st.error("Dataset not found. Make sure 'Final_Dataset_Deploy.csv' is in the same folder.")
        st.stop()
    df_norm = df.copy()
    num_cols = ['Cost of Living', 'Purchasing Power Index', 'Safety Index', 'Pollution', 'Healthcare', 'Transportation']
    for col in num_cols:
        rng = df[col].max() - df[col].min()
        df_norm[col + "_Norm"] = (df[col] - df[col].min()) / rng if rng != 0 else 0.5
    return df, df_norm

df, df_norm = load_data()

PARAMS = {
    "Cost of Living": {"col": "Cost of Living_Norm", "sign": -1, "df_col": "Cost of Living"},
    "Purchasing Power": {"col": "Purchasing Power Index_Norm", "sign": 1, "df_col": "Purchasing Power Index"},
    "Safety": {"col": "Safety Index_Norm", "sign": 1, "df_col": "Safety Index"},
    "Healthcare": {"col": "Healthcare_Norm", "sign": 1, "df_col": "Healthcare"},
    "Pollution": {"col": "Pollution_Norm", "sign": -1, "df_col": "Pollution"},
    "Transportation": {"col": "Transportation_Norm", "sign": 1, "df_col": "Transportation"},
}

def score_city(city_norm, weights):
    total = 0.0
    for name, p in PARAMS.items():
        w = weights.get(name, 0) / 100.0
        total += float(city_norm[p["col"]].iloc[0]) * p["sign"] * w
    return total * 10

# ---------- PAGE: COMPARE CITIES ----------
def page_compare(df, df_norm):
    st.subheader("Compare Cities")

    st.markdown("<div class='uv-card'>Select Cities</div>", unsafe_allow_html=True)
    defaults = [c for c in ["London", "New York", "Sydney", "Aachen"] if c in df["City_Name"].unique()]
    selected = st.multiselect("Cities:", options=df["City_Name"].unique(), default=defaults)

    if len(selected) < 2:
        st.info("Select at least two cities to compare.")
        return

    sliders_col, score_col = st.columns([2, 1])
    with sliders_col:
        st.markdown("<div class='uv-card'>Adjust Parameter Weights (0–10)</div>", unsafe_allow_html=True)
        weights = {p: st.slider(p, 0, 10, 5, key=f"w_{p}") for p in PARAMS.keys()}

    with st.spinner("Analyzing your preferences..."):
        time.sleep(0.6)

    results = []
    for city in selected:
        norm = df_norm[df_norm["City_Name"] == city]
        upls = score_city(norm, weights)
        row = df[df["City_Name"] == city].iloc[0]
        results.append({
            "City": city,
            "Country": row["Country"],
            "UPLS Score": round(upls, 4),
            "Safety Index": float(row["Safety Index"]),
            "Healthcare": float(row["Healthcare"]),
            "Pollution": float(row["Pollution"]),
            "Cost of Living": float(row["Cost of Living"]),
            "Transportation": float(row["Transportation"]),
            "Purchasing Power Index": float(row["Purchasing Power Index"])
        })

    df_res = pd.DataFrame(results).sort_values("UPLS Score", ascending=False).reset_index(drop=True)
    top = df_res.iloc[0]

    with score_col:
        st.markdown(f"""
        <div class='uv-card' style='text-align:center; padding:18px; margin-top:22px;'>
            <h4 style='margin-bottom:0.25rem;'>Top City</h4>
            <h4 style='color: var(--uv-accent); margin-bottom:0.5rem;'>{top['City']}, {top['Country']}</h4>
            <div style="
                display:inline-block;
                width:140px; height:140px;
                border-radius:50%;
                border:5px solid var(--uv-accent);
                color: var(--uv-dark);
                font-size:2.4rem;
                font-weight:700;
                line-height:130px;
                background: radial-gradient(circle at 30% 30%, rgba(46,134,222,0.15), rgba(255,255,255,0.95));
                box-shadow: 0 0 18px rgba(46,134,222,0.12);
                margin-top:8px;
            ">
                {top['UPLS Score']:.2f}
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ---------- FIXED BAR CHART ----------
    fig_bar = px.bar(
        df_res,
        x="City",
        y="UPLS Score",
        color="City",
        color_discrete_sequence=px.colors.sequential.Blues,
        text_auto=".2f"
    )
    fig_bar.update_traces(
        textfont_size=14,
        textposition="outside",
        cliponaxis=False
    )
    fig_bar.update_layout(
        title={"text": "User Prioritized Livability Score (UPLS)", "x": 0.5, "xanchor": "center"},
        xaxis_title="City",
        yaxis_title="UPLS Score",
        xaxis=dict(showgrid=False, tickfont=dict(size=14, color="#0b132b")),
        yaxis=dict(showgrid=True, gridcolor="rgba(0,0,0,0.1)", tickfont=dict(size=14, color="#0b132b")),
        legend=dict(
            title="Cities",
            orientation="h",
            yanchor="bottom",
            y=1.05,
            xanchor="center",
            x=0.5,
            font=dict(size=12, color="#0b132b")
        ),
        plot_bgcolor="white",
        paper_bgcolor="rgba(255,255,255,0.8)",
        bargap=0.3,
        margin=dict(t=80, b=60, l=60, r=40),
        font=dict(color="#0b132b", family="Segoe UI")
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # ---------- RADAR CHART ----------
    radar_fig = go.Figure()
    categories = ["Safety", "Healthcare", "Cleanliness", "Affordability", "Transport"]
    for _, row in df_res.iterrows():
        radar_fig.add_trace(go.Scatterpolar(
            r=[row["Safety Index"], row["Healthcare"], max(0, 100 - row["Pollution"]),
               max(0, 100 - row["Cost of Living"]), row["Transportation"]],
            theta=categories, fill='toself', name=row["City"]
        ))
    radar_fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100], gridcolor='rgba(0,0,0,0.1)')),
        showlegend=True,
        title_text="City Comparison Across Key Metrics",
        title_x=0.5,
        paper_bgcolor="rgba(255,255,255,0.8)",
        plot_bgcolor="white",
        font=dict(color="#0b132b")
    )
    st.plotly_chart(radar_fig, use_container_width=True)

    # ---------- SUMMARY ----------
    st.markdown(
        f"<div class='uv-card'><b>Urban Vista Recommends:</b> Based on your selected weights, <b>{top['City']}</b> offers the best livability balance.</div>",
        unsafe_allow_html=True)

    param_cols = ["Safety Index", "Healthcare", "Pollution", "Cost of Living", "Transportation", "Purchasing Power Index"]
    mean_vals = df_res[param_cols].mean()
    top_vals = df_res.iloc[0][param_cols]
    strengths = [p for p in param_cols if top_vals[p] > mean_vals[p] * 1.05]
    weaknesses = [p for p in param_cols if top_vals[p] < mean_vals[p] * 0.95]
    clean = {"Safety Index": "Safety", "Healthcare": "Healthcare", "Pollution": "Environmental Cleanliness",
             "Cost of Living": "Affordability", "Transportation": "Transport Efficiency",
             "Purchasing Power Index": "Purchasing Power"}
    strengths = [clean.get(p, p) for p in strengths]
    weaknesses = [clean.get(p, p) for p in weaknesses]

    st.markdown(
        f"<div class='uv-card'><b>Summary:</b> {top['City']} excels in <b>{', '.join(strengths) if strengths else 'overall balance'}</b> and can improve in <b>{', '.join(weaknesses) if weaknesses else 'no major weaknesses'}</b>.</div>",
        unsafe_allow_html=True)

    with st.expander("View Detailed Data Table"):
        st.dataframe(df_res, use_container_width=True)

# ---------- OTHER PAGES ----------
def page_insights(df):
    st.subheader("Summary Insights")
    st.dataframe(df.describe(), use_container_width=True)

def page_about():
    st.subheader("About Urban Vista")
    st.markdown("Urban Vista helps analyze and compare cities based on livability metrics like cost of living, safety, healthcare, and pollution.")

# ---------- ROUTING ----------
if st.session_state["page"] == "Compare Cities":
    page_compare(df, df_norm)
elif st.session_state["page"] == "Summary Insights":
    page_insights(df)
elif st.session_state["page"] == "About":
    page_about()
