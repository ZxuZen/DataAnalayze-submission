import streamlit as st
import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

@st.cache_data
def load_data():
    main_data = pd.read_csv(BASE_DIR / "main_data.csv")
    categories = pd.read_csv(BASE_DIR / "categories.csv")
    return main_data, categories

try:
    main_data, categories = load_data()
except Exception as e:
    st.error(
        "Gagal memuat data. Pastikan file main_data.csv dan categories.csv "
        f"berada satu folder dengan dashboard.py. Detail: {e}"
    )
    st.stop()

st.set_page_config(page_title="Olist E-Commerce Dashboard", page_icon="🛒", layout="wide")

st.title("Olist E-Commerce Dashboard")
st.caption("Periode analisis: Jan 2017 - Agu 2018 | Sumber: Olist Brazilian E-Commerce Dataset")

st.sidebar.header("Filter Data")
months = sorted(main_data["order_month"].unique())
states = sorted(main_data["customer_state"].dropna().unique())
statuses = sorted(main_data["delivery_status"].unique())
segments = sorted(main_data["segment"].dropna().unique())

sel_months = st.sidebar.multiselect("Bulan", months, default=months)
sel_states = st.sidebar.multiselect("State Pelanggan", states, default=states)
sel_status = st.sidebar.multiselect("Status Pengiriman", statuses, default=statuses)
sel_segment = st.sidebar.multiselect("Segmen RFM", segments, default=segments)

df = main_data[
    main_data["order_month"].isin(sel_months)
    & main_data["customer_state"].isin(sel_states)
    & main_data["delivery_status"].isin(sel_status)
    & main_data["segment"].isin(sel_segment)
]

if df.empty:
    st.warning("Kombinasi filter tidak menghasilkan data. Silakan longgarkan filter.")
    st.stop()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Pesanan", f"{len(df):,}")
c2.metric("Total Revenue (BRL)", f"{df['order_value'].sum():,.0f}")
c3.metric("Rata-rata Review Score", f"{df['review_score'].mean():.2f}")
c4.metric("Tingkat Keterlambatan", f"{(df['delivery_status'] == 'Late').mean() * 100:.1f}%")

st.markdown("---")

st.subheader("1. Top 10 Kategori Produk dengan Revenue Tertinggi")
top10 = categories.head(10).set_index("product_category_name_english")["total_revenue"]
st.bar_chart(top10)
st.caption(
    "**Insight:** health_beauty, watches_gifts, dan bed_bath_table adalah tiga kontributor "
    "pendapatan terbesar (±25,9% dari total revenue periode Jan 2017 - Agu 2018)."
)

st.subheader("2. Dampak Keterlambatan Pengiriman terhadap Review Score")
delay_order = ["Tepat Waktu / Lebih Cepat", "Telat 1-3 Hari", "Telat 4-7 Hari", "Telat > 7 Hari"]
delay_score = df.groupby("delay_category")["review_score"].mean().reindex(delay_order).dropna()
st.bar_chart(delay_score)
st.caption(
    "**Insight:** Semakin parah keterlambatan, semakin rendah review score "
    "(4,29 tepat waktu → 1,70 untuk telat > 7 hari)."
)

st.subheader("3. Tren Revenue & Jumlah Pesanan per Bulan")
monthly = df.groupby("order_month").agg(
    Revenue=("order_value", "sum"),
    Jumlah_Pesanan=("order_id", "count"),
)
st.line_chart(monthly)

st.subheader("4. Distribusi Pelanggan per Segmen RFM")
seg = df.groupby("segment").agg(
    Jumlah_Pelanggan=("customer_unique_id", "nunique"),
    Rata_Monetary=("order_value", "mean"),
).sort_values("Jumlah_Pelanggan", ascending=False)
st.bar_chart(seg["Jumlah_Pelanggan"])
st.dataframe(seg.round(2))
st.caption(
    "**Insight:** 97% pelanggan hanya berbelanja sekali; segmen pelanggan berulang "
    "(Champions/Loyal/At Risk) memiliki rata-rata monetary hampir 2× lipat."
)