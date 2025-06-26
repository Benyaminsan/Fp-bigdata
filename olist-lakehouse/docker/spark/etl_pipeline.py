from pyspark.sql import SparkSession
from pyspark.sql.functions import col, to_date, datediff, rand
import os

# Ambil konfigurasi MinIO dari environment variables
minio_endpoint = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
minio_access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
minio_secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")

# Path S3A untuk bucket
raw_bucket = "s3a://raw"
bronze_bucket = "s3a://bronze"
silver_bucket = "s3a://silver"
gold_bucket = "s3a://gold"

# Inisialisasi SparkSession dengan konfigurasi S3A untuk MinIO
spark_builder = SparkSession.builder \
    .appName("OlistETL") \
    .config("spark.sql.adaptive.enabled", "true") \
    .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
    .config("spark.hadoop.fs.s3a.endpoint", minio_endpoint) \
    .config("spark.hadoop.fs.s3a.access.key", minio_access_key) \
    .config("spark.hadoop.fs.s3a.secret.key", minio_secret_key) \
    .config("spark.hadoop.fs.s3a.path.style.access", "true") \
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem") \
    .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262") # Versi bisa disesuaikan

spark = spark_builder.getOrCreate()

# Hapus os.makedirs dan chmod, MinIO akan handle ini.

try:
    # Load data dari raw layer (MinIO bucket 'raw')
    print(f"Loading data from raw layer: {raw_bucket}...")
    orders = spark.read.csv(f"{raw_bucket}/olist_orders_dataset.csv", header=True, inferSchema=True)
    items = spark.read.csv(f"{raw_bucket}/olist_order_items_dataset.csv", header=True, inferSchema=True)
    products = spark.read.csv(f"{raw_bucket}/olist_products_dataset.csv", header=True, inferSchema=True)
    reviews = spark.read.csv(f"{raw_bucket}/olist_order_reviews_dataset.csv", header=True, inferSchema=True)

    print(f"Saving to bronze layer: {bronze_bucket}...")
    orders.coalesce(1).write.mode("overwrite").parquet(f"{bronze_bucket}/orders")
    print("Orders saved to bronze layer")
    
    items.coalesce(1).write.mode("overwrite").parquet(f"{bronze_bucket}/items")
    print("Items saved to bronze layer")
    
    products.coalesce(1).write.mode("overwrite").parquet(f"{bronze_bucket}/products")
    print("Products saved to bronze layer")
    
    reviews.coalesce(1).write.mode("overwrite").parquet(f"{bronze_bucket}/reviews")
    print("Reviews saved to bronze layer")

    # === SILVER LAYER === #
    print(f"Processing silver layer to {silver_bucket}...")
    df = orders.join(items, on="order_id", how="inner") \
               .join(products, on="product_id", how="left") \
               .join(reviews, on="order_id", how="left")

    df = df.withColumn("order_approved_at", to_date("order_approved_at")) \
           .withColumn("order_delivered_customer_date", to_date("order_delivered_customer_date")) \
           .withColumn("delivery_days", datediff("order_delivered_customer_date", "order_approved_at"))

    df = df.filter(col("price").isNotNull() & col("freight_value").isNotNull())
    df = df.withColumn("price", col("price").cast("float"))

    #df = df.withColumn("cost_price", (col("price") * 0.7).cast("float"))

    df = df.withColumn("cost_price_ratio", (rand() * 0.3 + 0.5)) # Untuk inspeksi jika perlu
    df = df.withColumn("cost_price", (col("price") * col("cost_price_ratio")).cast("float"))

    df.coalesce(1).write.mode("overwrite").parquet(f"{silver_bucket}/olist_cleaned")
    print("Data saved to silver layer")

    # === GOLD LAYER === #
    print(f"Processing gold layer to {gold_bucket}...")
    gold_df = df.select(
        "cost_price", "freight_value", "price", "delivery_days", "review_score", "product_category_name"
    )

    gold_df.coalesce(1).write.mode("overwrite").parquet(f"{gold_bucket}/olist_features") # direktori, bukan file
    print("Features saved to gold layer")

    print("ETL selesai.")

except Exception as e:
    print(f"Error occurred: {str(e)}")
    import traceback
    traceback.print_exc() # Cetak traceback untuk debug lebih detail
    raise e
finally:
    spark.stop()