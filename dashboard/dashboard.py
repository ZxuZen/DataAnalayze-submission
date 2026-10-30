import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

st.set_page_config(page_title="Olist E-Commerce Dashboard", layout="wide")

BASE_DIR = Path(__file__).resolve().parent

@st.cache_data
def load_data():
    main_data = pd.read_csv(BASE_DIR / "main_data.csv")
    categories = pd.read_csv(BASE_DIR / "categories.csv")
    return main_data, categories

try:
    main_data, categories = load_data()
except Exception as e:
    st.error(f"Gagal memuat data. Pastikan main_data.csv dan categories.csv ada di folder dashboard/. Detail: {e}")
    st.stop()

STATE_NAMES = {
    "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas",
    "BA": "Bahia", "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo",
    "GO": "Goiás", "MA": "Maranhão", "MT": "Mato Grosso", "MS": "Mato Grosso do Sul",
    "MG": "Minas Gerais", "PA": "Pará", "PB": "Paraíba", "PR": "Paraná",
    "PE": "Pernambuco", "PI": "Piauí", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
    "RS": "Rio Grande do Sul", "RO": "Rondônia", "RR": "Roraima", "SC": "Santa Catarina",
    "SP": "São Paulo", "SE": "Sergipe", "TO": "Tocantins",
}
main_data["state_name"] = main_data["customer_state"].map(STATE_NAMES).fillna(main_data["customer_state"])

st.title("Olist E-Commerce Dashboard")
st.markdown("Dashboard ini memungkinkan Anda untuk melakukan **eksplorasi dan manipulasi data secara langsung** menggunakan filter dan widget interaktif.")

st.sidebar.header("Filter Eksplorasi Data")
states = sorted(main_data["state_name"].dropna().unique())
sel_states = st.sidebar.multiselect(
    "Pilih Provinsi (Brazil):", 
    states, 
    default=states,
    help="Pilih satu atau beberapa provinsi untuk memfilter data secara langsung."
)

df = main_data[main_data["state_name"].isin(sel_states)]

if df.empty:
    st.warning("Tidak ada data untuk provinsi yang dipilih. Silakan ubah filter.")
    st.stop()

st.subheader("Manipulasi Visualisasi")
col1, col2 = st.columns(2)

with col1:
    viz_option = st.selectbox(
        "1. Pilih Jenis Analisis:",
        ("Pendapatan Kategori Produk", "Dampak Keterlambatan Pengiriman", "Segmentasi Pelanggan (RFM)")
    )

with col2:
    top_n = st.slider(
        "2. Atur Jumlah Data yang Ditampilkan (Top N):", 
        min_value=5, 
        max_value=20, 
        value=10, 
        step=1,
        help="Geser slider ini untuk memanipulasi jumlah kategori yang ditampilkan pada chart secara langsung."
    )

st.markdown("---")

if viz_option == "Pendapatan Kategori Produk":
    st.header(f"Top {top_n} Kategori Produk dengan Revenue Tertinggi")
    top_cats = categories.head(top_n)
    max_rev = top_cats['total_revenue'].max()

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=top_cats, x='total_revenue', y='product_category_name_english',
                palette='viridis', ax=ax,
                hue='product_category_name_english', legend=False)

    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, loc: f"{x/1000:.0f}k"))

    for bar in ax.patches:
        w = bar.get_width()
        ax.text(w + max_rev * 0.01, bar.get_y() + bar.get_height() / 2,
                f"BRL {w:,.0f}", va='center', fontsize=9)

    ax.set_xlim(0, max_rev * 1.30)   
    ax.set_title(f"Top {top_n} Kategori Produk Berdasarkan Revenue", fontweight='bold')
    ax.set_xlabel("Total Pendapatan (BRL)")
    ax.set_ylabel("Kategori Produk")
    st.pyplot(fig)
    st.info("**Insight:** health_beauty, watches_gifts, dan bed_bath_table adalah tiga kontributor revenue terbesar (±25,9% total).")

elif viz_option == "Dampak Keterlambatan Pengiriman":
    st.header("Dampak Keterlambatan Pengiriman terhadap Review Score")
    
    delay_order = ["Tepat Waktu / Lebih Cepat", "Telat 1-3 Hari", "Telat 4-7 Hari", "Telat > 7 Hari"]
    delay_score = df.groupby("delay_category")["review_score"].mean().reindex(delay_order).dropna().reset_index()
    
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.barplot(data=delay_score, x='delay_category', y='review_score', palette='magma', ax=ax, hue='delay_category', legend=False)
    ax.set_ylim(0, 5)
    ax.set_title("Rata-rata Review Score berdasarkan Kategori Keterlambatan", fontweight='bold')
    ax.set_xlabel("Status Keterlambatan")
    ax.set_ylabel("Rata-rata Review Score")
    
    for i in range(len(delay_score)):
        ax.text(i, delay_score['review_score'].iloc[i] + 0.1, f"{delay_score['review_score'].iloc[i]:.2f}", ha='center', fontweight='bold')
        
    st.pyplot(fig)
    st.warning("**Insight:** Keterlambatan > 7 hari membuat skor anjlok drastis ke 1.70.")

elif viz_option == "Segmentasi Pelanggan (RFM)":
    st.header("Distribusi Pelanggan per Segmen RFM")
    
    seg = df.groupby("segment").agg(
        Jumlah_Pelanggan=("customer_unique_id", "nunique"),
        Rata_Monetary=("order_value", "mean"),
    ).sort_values("Jumlah_Pelanggan", ascending=False).reset_index()
    
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=seg, x='segment', y='Jumlah_Pelanggan', palette='Blues_d', ax=ax, hue='segment', legend=False)
    ax.set_title("Jumlah Pelanggan per Segmen RFM", fontweight='bold')
    st.pyplot(fig)
    
    st.dataframe(seg.round(2), use_container_width=True)
    st.success("💡 **Insight:** 97% pelanggan adalah pembeli satu kali. Fokuskan retensi pada segmen Champions dan At Risk.")