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
│   ├── raw/                 ← 🔹 Dataset Olist (.csv)
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
├── mlruns/                  ← MLflow tracking
└── docker-compose.yml
```

- Pipeline diagramnya
![Diagram Pipeline lakehouse](https://github.com/user-attachments/assets/e24670b4-d6e6-4e07-bccb-5325bd5fe4ac)

- End-to-end Arsitektur Data Lakehouse
![End-to-End data lakehouse architecture](https://github.com/user-attachments/assets/34be8cbc-c9f1-46c6-a64a-a66e2c94cf9b)



