# Final Project Big Data dan Lakehouse

Membuat Sales Prediction untuk mengetahui potensi penjualan di masa depan

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

- Struktur Folder

```
olist-lakehouse/
├── data/
│   ├── raw/                 ← Dataset Olist (.csv)
│   ├── bronze/              ← Disalin dari raw atau hasil landing
│   ├── silver/              ← Hasil cleaning & join
│   └── gold/                ← Hasil feature engineering (untuk ML)
│
├── docker/
│   ├── spark/
│   │   └── etl_pipeline.py  ← ETL script
│   ├── mlflow/
│   │   └── train_model.py   ← ML model training
│   ├── fastapi/
│   │   └── main.py          ← API serving model
│   └── streamlit/
│       └── ui.py            ← Client UI
│
├── minio_data/                    ← Folder backend untuk penyimpanan MinIO (object storage)
    │   ├── raw/                       ← Mirroring data mentah (format internal MinIO)
    │   ├── bronze/
    │   ├── silver/
    │   └── gold/
    │
    └── mlruns/                        ← Log dan metadata eksperimen MLflow
        └── [experiment_id]/
            ├── meta.yaml              ← Metadata eksperimen
            └── [run_id]/
                ├── artifacts/
                │   └── model/
                │       ├── model.pkl              ← Model hasil training
                │       ├── MLmodel                ← Metadata model
                │       └── requirements.txt       ← Dependensi model
                ├── metrics/                       ← Metrik evaluasi (MAE, RMSE, dll)
                ├── params/                        ← Parameter training (max_depth, n_estimators, dll)
                └── tags/                          ← Metadata tambahan MLflow
└── docker-compose.yml
```

- WorkFlow dari projectnya
![Image](https://github.com/user-attachments/assets/d82d4ea1-56a9-4f4a-acba-bb3e02536981)

- End-to-end Arsitektur Data Lakehouse
![End-to-End data lakehouse architecture](https://github.com/user-attachments/assets/34be8cbc-c9f1-46c6-a64a-a66e2c94cf9b)

## Cara menjalankan:
1. Gunakan `docker-compose up -d` untuk menjalankan seluruh service.
2. Upload data yang ada di directory `./data/raw` ke bucket raw yang ada di MinIO yang dapat diakses di `http://localhost:9001`. Pastikan juga seluruh bucket (raw, bronze, silver, gold) sudah dibuat.
   ![image](https://github.com/user-attachments/assets/936f8f0c-a70a-4364-b762-6508354c802c)
   ![image](https://github.com/user-attachments/assets/89edf5d1-70a7-4234-8937-6955efd4e6b3)
3. Jalankan ETL pipeline yang ada di service Spark dengan command `docker-compose exec spark spark-submit /app/etl_pipeline.py`.
4. Setelah menjalankan ETL, lakukan training model pada MLflow dengan command `docker-compose exec mlflow python /app/train_model.py`.
5. Setelah training model, model prediksi dapat diakses melalui `http://localhost:8501/`.

## Dokumentasi
- UI Client
 ![WhatsApp Image 2025-06-13 at 08 04 53_213db181](https://github.com/user-attachments/assets/701184b6-ca15-41bf-b1f3-c620c57e3dad)





