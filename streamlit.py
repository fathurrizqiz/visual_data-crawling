import streamlit as st
from pymongo import MongoClient
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import pandas as pd
from collections import Counter
import re
from datetime import datetime


# Stopwords bahasa Indonesia
stopwords = set([
    "dan", "atau", "yang", "di", "ke", "dari", "untuk", "pada", "dengan", 
    "ini", "itu", "adalah", "sebuah", "kami", "kamu", "mereka", "saya", 
    "aku", "juga", "sehingga", "terhadap", "oleh", "karena"
])

# Koneksi MongoDB
client = MongoClient("mongodb+srv://username:password@cluster0.mongodb.net/detik_com?retryWrites=true&w=majority")
db = client["detik_com"]
collection = db["crawling"]


# Fungsi untuk mengekstrak bulan dan tahun dari string
def extract_month_year(date_str):
    try:
        # Split string dan ambil bagian bulan dan tahun
        parts = date_str.split()  # Memecah string berdasarkan spasi
        month_year = f"{parts[2]} {parts[3]}"  # Ambil bulan dan tahun
        return month_year
    except Exception as e:
        print(f"Error extracting month and year: {e}")
        return None

# Ambil dokumen dari database
documents = list(collection.find({}, {"description": 1, "date": 1, "_id": 0}))
text = " ".join(doc['description'] for doc in documents if 'description' in doc)

# ------------------------
# WordCloud Section
# ------------------------
st.title("Visualisasi Artikel 'Tunawicara'")
st.header("WordCloud dari Deskripsi Artikel")

width = st.slider('Pilih lebar WordCloud', 400, 1200, 800)
height = st.slider('Pilih tinggi WordCloud', 200, 800, 400)
bg_color = st.selectbox('Pilih warna latar belakang', ['white', 'black', 'blue', 'green', 'yellow'])

wordcloud = WordCloud(
    width=width,
    height=height,
    background_color=bg_color,
    stopwords=stopwords
).generate(text)

fig_wc, ax_wc = plt.subplots(figsize=(12, 6))
ax_wc.imshow(wordcloud, interpolation='bilinear')
ax_wc.axis("off")
st.pyplot(fig_wc)
plt.close(fig_wc)

# ------------------------
# Diagram Batang Horizontal 10 Kata Terpopuler
# ------------------------
st.header("10 Kata Paling Sering Muncul di Deskripsi")

words = re.findall(r'\b\w+\b', text.lower())
filtered_words = [word for word in words if word not in stopwords and len(word) > 2]

word_counts = Counter(filtered_words)
top_words = word_counts.most_common(10)
word_df = pd.DataFrame(top_words, columns=["Kata", "Jumlah"])

# Plot Diagram Batang Horizontal
fig_bar, ax_bar = plt.subplots(figsize=(10, 6))
ax_bar.barh(word_df["Kata"], word_df["Jumlah"], color="orange")  # Ganti bar menjadi horizontal (barh)
ax_bar.set_title("10 Kata Terpopuler")
ax_bar.set_xlabel("Jumlah Kemunculan")
ax_bar.set_ylabel("Kata")
st.pyplot(fig_bar)
plt.close(fig_bar)

# ------------------------
# Pie Chart Tren Kata Terpopuler Berdasarkan Bulan
# ------------------------
st.header("Pie Chart Tren Kata Terpopuler Berdasarkan Bulan")

# Buat dict: {bulan: Counter kata}
monthly_word_freq = {}
available_months = []

for doc in documents:
    if 'description' in doc and 'date' in doc:
        # Menggunakan string date untuk mengekstrak bulan dan tahun
        date_str = doc['date']
        
        # Ekstrak bulan dan tahun dari string date
        month_str = extract_month_year(date_str)  # Mengambil bulan dan tahun
        if month_str:
            available_months.append(month_str)
            words = re.findall(r'\b\w+\b', doc['description'].lower())
            filtered = [w for w in words if w not in stopwords and len(w) > 2]
                
            if month_str not in monthly_word_freq:
                monthly_word_freq[month_str] = Counter()
            monthly_word_freq[month_str].update(filtered)

# Debug: Tampilkan semua bulan yang ditemukan
st.write("Bulan yang ditemukan dalam data:", sorted(set(available_months)))

# Dropdown pemilihan bulan
selected_months = st.multiselect(
    "Pilih bulan yang ingin ditampilkan:",
    options=sorted(set(available_months)),  # Menampilkan semua bulan yang ditemukan
    default=sorted(set(available_months))  # Secara default tampilkan semua bulan
)

if selected_months:
    # Hitung total kata dari bulan yang dipilih
    total_counter = Counter()
    for month in selected_months:
        total_counter.update(monthly_word_freq.get(month, Counter()))

    # Ambil 5 kata terpopuler di bulan-bulan terpilih
    top_words_global = [word for word, _ in total_counter.most_common(5)]

    # Siapkan data untuk pie chart
    pie_data = dict(total_counter.most_common(5))

    # Plot pie chart
    fig_pie, ax_pie = plt.subplots(figsize=(7, 7))
    ax_pie.pie(pie_data.values(), labels=pie_data.keys(), autopct='%1.1f%%', startangle=90, colors=plt.cm.Paired.colors)
    ax_pie.set_title("Distribusi 5 Kata Terpopuler di Bulan Terpilih")
    st.pyplot(fig_pie)
    plt.close(fig_pie)
else:
    st.warning("Pilih minimal satu bulan untuk melihat tren kata.")
