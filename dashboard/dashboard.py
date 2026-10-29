import pandas as pd
import seaborn as sns
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(page_title="Olist E-Commerce Dashboard", layout="wide")

@st.cache_data
def load_data():
    orders = pd.read_csv("../data/olist_orders_dataset.csv")
    order_items = pd.read_csv("../data/olist_order_items_dataset.csv")
    reviews = pd.read_csv("../data/olist_order_reviews_dataset.csv")
    products = pd.read_csv("../data/olist_products_dataset.csv")
    category_tr = pd.read_csv("../data/product_category_name_translation.csv")

    products['product_category_name'] = products['product_category_name'].fillna('unknown')

    date_columns = ['order_purchase_timestamp', 'order_approved_at', 'order_delivered_carrier_date',
                    'order_delivered_customer_date', 'order_estimated_delivery_date']
    for col in date_columns:
        if col in orders.columns:
            orders[col] = pd.to_datetime(orders[col], errors='coerce')

    orders_delivered = orders[orders['order_status'] == 'delivered'].copy()
    start_date = '2017-01-01'
    end_date = '2018-08-31'
    orders_cleaned = orders_delivered[
        (orders_delivered['order_purchase_timestamp'] >= start_date) &
        (orders_delivered['order_purchase_timestamp'] <= end_date)
    ].copy()

    df_q1 = pd.merge(orders_cleaned, order_items[['order_id', 'product_id', 'price']], on='order_id', how='inner')
    df_q1 = pd.merge(df_q1, products[['product_id', 'product_category_name']], on='product_id', how='left')
    df_q1 = pd.merge(df_q1, category_tr, on='product_category_name', how='left')
    df_q1['product_category_name_english'] = df_q1['product_category_name_english'].fillna('unknown')

    reviews_sorted = reviews.sort_values(by='review_creation_date', ascending=False)
    reviews_cleaned = reviews_sorted.drop_duplicates(subset='order_id', keep='first')
    df_q2 = pd.merge(orders_cleaned, reviews_cleaned[['order_id', 'review_score', 'review_creation_date']], on='order_id', how='inner')
    df_q2['delay_days'] = (df_q2['order_delivered_customer_date'] - df_q2['order_estimated_delivery_date']).dt.days
    df_q2 = df_q2.dropna(subset=['delay_days'])
    df_q2['delivery_status'] = df_q2['delay_days'].apply(lambda x: 'Late' if x > 0 else 'On Time')

    return df_q1, df_q2

try:
    df_q1, df_q2 = load_data()
except Exception as e:
    st.error(f"Error memuat data. Pastikan file CSV berada di dalam folder 'data/'. Detail: {e}")
    st.stop()

st.title("📊 Olist E-Commerce Public Dataset Dashboard")
st.markdown("""
Dashboard ini menampilkan hasil analisis data e-commerce Olist (Periode Jan 2017 - Agu 2018).
Analisis mencakup performa pendapatan kategori produk, pengaruh keterlambatan pengiriman terhadap kepuasan pelanggan, dan segmentasi pelanggan (RFM).
""")

st.sidebar.header("Menu Navigasi")
page = st.sidebar.radio("Pilih Visualisasi:", ["💰 Pendapatan Kategori", "⏱️ Dampak Keterlambatan", "👥 RFM Analysis"])

if page == "💰 Pendapatan Kategori":
    st.header("Kategori Produk dengan Pendapatan Tertinggi")
    revenue_per_category = df_q1.groupby('product_category_name_english')['price'].sum().reset_index()
    revenue_per_category.rename(columns={'price': 'total_revenue'}, inplace=True)
    revenue_per_category = revenue_per_category.sort_values(by='total_revenue', ascending=False).head(15)

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=revenue_per_category, x='total_revenue', y='product_category_name_english', palette='viridis', ax=ax)
    ax.set_title("Top 15 Kategori Produk Berdasarkan Revenue (BRL)", fontweight='bold')
    ax.set_xlabel("Total Revenue (BRL)")
    ax.set_ylabel("Kategori Produk")
    st.pyplot(fig)

    st.info("**Insight:** Kategori `health_beauty` dan `watches_gifts` menjadi penyumbang revenue terbesar. Disarankan untuk mempertahankan stok dan melakukan bundling pada kategori ini.")

elif page == "⏱️ Dampak Keterlambatan":
    st.header("Pengaruh Keterlambatan Terhadap Review Score")

    col1, col2 = st.columns(2)
    with col1:
        review_by_status = df_q2.groupby('delivery_status')['review_score'].mean().reset_index()
        fig1, ax1 = plt.subplots(figsize=(6, 5))
        sns.barplot(data=review_by_status, x='delivery_status', y='review_score', palette='coolwarm', ax=ax1)
        ax1.set_ylim(0, 5)
        ax1.set_title("Rata-rata Review Score: Tepat Waktu vs Terlambat", fontweight='bold')
        st.pyplot(fig1)

    with col2:
        bins = [-1000, 0, 3, 7, 1000]
        labels = ['On Time / Early', 'Late 1-3 Days', 'Late 4-7 Days', 'Late > 7 Days']
        df_q2['delay_bin'] = pd.cut(df_q2['delay_days'], bins=bins, labels=labels)
        review_by_delay = df_q2.groupby('delay_bin', observed=True)['review_score'].mean().reset_index()

        fig2, ax2 = plt.subplots(figsize=(6, 5))
        sns.barplot(data=review_by_delay, x='delay_bin', y='review_score', palette='Reds_r', ax=ax2)
        ax2.set_ylim(0, 5)
        ax2.set_title("Review Score Berdasarkan Tingkat Keterlambatan", fontweight='bold')
        plt.xticks(rotation=15)
        st.pyplot(fig2)

    st.warning("**Insight:** Keterlambatan pengiriman menurunkan skor ulasan secara signifikan (dari 4.29 menjadi 2.27). Keterlambatan > 7 hari membuat skor anjlok ke 1.70. Perlu audit mitra logistik dan kompensasi otomatis.")

elif page == "👥 RFM Analysis":
    st.header("Segmentasi Pelanggan (RFM Analysis)")
    st.markdown("Pengelompokan pelanggan berdasarkan *Recency, Frequency,* dan *Monetary* untuk strategi retensi.")

    rfm_summary = pd.DataFrame({
        'Segment': ['Sleeping / Lost', 'New Customers', 'Champions', 'At Risk', 'Loyal'],
        'Total Pelanggan': [54087, 36228, 1205, 981, 603],
        'Rata-rata Monetary (BRL)': [136.30, 140.32, 270.29, 246.52, 261.72]
    })

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=rfm_summary, x='Segment', y='Total Pelanggan', palette='Blues_d', ax=ax)
    ax.set_title("Distribusi Jumlah Pelanggan per Segmen RFM", fontweight='bold')
    st.pyplot(fig)

    st.dataframe(rfm_summary, use_container_width=True)
    st.success("**Insight:** 97% pelanggan adalah pembeli satu kali. Program konversi pembelian kedua sangat krusial untuk *New Customers*, sementara *Win-back campaign* diperlukan untuk *At Risk*.")