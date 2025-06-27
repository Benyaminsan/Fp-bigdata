# Final Project Big Data dan Lakehouse

Membuat Sales Prediction untuk mengetahui potensi penjualan di masa depan yang berpihak kepada seller. Nantinya produk yang akan dikirim kepada konsumer akan memperoleh data mulai dari profit margin, price/day ratio, Gross profit(laba kotor), dan Review Sentiment. Diharapkan dengan adanya aplikasi ini bisa meningkatkan efisiensi dalam perhitungan terutama dalam Opex dan Delivery Cost. Sehingga, peningkatan produktifitas dapat terjamin untuk membuka peluang atau langkah strategi seller kedepannya.

Anggota Kelompok:

| No. | Nama | NRP |
| :-- | :--- | :--- |
| 1. | Muhammad Faqih Husain | 5027231023 |
| 2. | Furqon Aryadana | 5027231024 |
| 3. | Haidar Rafi Aqyla | 5027231029 |
| 4. | Benjamin Khawarizmi Habibi | 5027231078 |
| 5. | Radella Chesa S | 5027231064 |

- Dataset yang digunakan bersumber disini:

https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce/data

- Dataset untuk Product bergambar:

https://www.kaggle.com/datasets/fatihkgg/ecommerce-product-images-18k/data

- Struktur Folder

```
olist-lakehouse/
├── data/
│   ├── raw/                 ← Dataset Olist (.csv) + gambar
│   ├── bronze/              ← Disalin dari raw atau hasil landing
│   ├── silver/              ← Hasil cleaning & join
│   └── gold/                ← Hasil feature engineering (untuk ML)
│
├── docker/
│   ├── streamer/
│   │   ├── Dockerfile
│   │   └── local_to_minio_streamer.py  ← Streamer dari local ke MinIO
│   ├── spark/
│   │   └── etl_pipeline.py  ← ETL script
│   ├── mlflow/
│   │   └── train_model.py   ← ML model training
│   ├── fastapi/
│   │   ├── Dockerfile
│   │   ├── __pycache__
│   │   └── main.py          ← API serving model
│   └── streamlit/
│       ├── Dockerfile
│       ├── requirements.txt
│       └── ui.py            ← Client UI
│
└── docker-compose.yml
└── mlruns
        └── 525745794765050212
            ├── 4477717b16df42a680f2765ce59f7f35
            ├── 6486f32a9de64666b989f4f02f06744a
            ├── a4042ade73a74d2dbe6d8ec7854316b5
            ├── a50d24cfab964915bd975dfdad7fc551
            ├── b0340fffd7604504a8e23a4d01cac627
            ├── eeea350ff3a849bb986e8e6ca69712cc
            └── meta.yaml
```


- WorkFlow dari projectnya
![Image](https://github.com/user-attachments/assets/d82d4ea1-56a9-4f4a-acba-bb3e02536981)

- End-to-end Arsitektur Data Lakehouse
![End-to-End data lakehouse architecture](https://github.com/user-attachments/assets/34be8cbc-c9f1-46c6-a64a-a66e2c94cf9b)

## Cara menjalankan:
1. Gunakan `docker-compose up -d` untuk menjalankan seluruh service.
2. Setelah menjalankan semua service, tiap bucket di MinIO (raw, bronze, silver, gold) akan terbentuk secara otomatis. Selain itu, data dari local juga akan di-stream secara otomatis ke MinIO.
   ![image](https://github.com/user-attachments/assets/a8f260e5-647b-40f7-8fe5-19c039ac38bd)
   ![image](https://github.com/user-attachments/assets/415fc909-04e3-4b2e-be28-c46cf7863add)
4. Jalankan ETL pipeline yang ada di service Spark dengan command `docker-compose exec spark spark-submit /app/etl_pipeline.py`.
5. Setelah menjalankan ETL, lakukan training model pada MLflow dengan command `docker-compose exec mlflow python /app/train_model.py`.
6. Setelah training model, model prediksi dapat diakses melalui `http://localhost:8501/`.

## Dokumentasi
- UI Client
  ![image](https://github.com/user-attachments/assets/db754b56-2f89-48c1-8843-14a7850d1060)
  ![image](https://github.com/user-attachments/assets/eeb392e1-df64-46c0-bb01-2713bd66feae)
  ![image](https://github.com/user-attachments/assets/2cbaa772-0c1a-4fef-b581-a61d132e48c4)






