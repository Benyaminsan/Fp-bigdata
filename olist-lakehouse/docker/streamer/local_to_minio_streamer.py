# local_to_minio_streamer.py

import time
import os
import boto3
from watchdog.observers.polling import PollingObserver # Impor PollingObserver
from watchdog.events import FileSystemEventHandler
import logging
import shutil

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_RAW_BUCKET = os.getenv("MINIO_RAW_BUCKET", "raw") # Nama bucket tujuan

HOST_DATA_ROOT_IN_CONTAINER = os.getenv("LOCAL_DATA_PATH", "/monitored_source_data")
SUBDIR_TO_MONITOR = "raw"
PATH_TO_MONITOR_INSIDE_CONTAINER = os.path.join(HOST_DATA_ROOT_IN_CONTAINER, SUBDIR_TO_MONITOR)

SUPPORTED_EXTENSIONS = ('.csv', '.jpg', '.jpeg', '.png', '.gif', '.parquet', '.json')

try:
    s3_client = boto3.client(
        's3',
        endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        config=boto3.session.Config(retries={'max_attempts': 3, 'mode': 'standard'})
    )
    s3_client.list_buckets()
    logging.info(f"Successfully connected to MinIO endpoint: {MINIO_ENDPOINT}")
except Exception as e:
    logging.error(f"Failed to connect to MinIO endpoint {MINIO_ENDPOINT}: {e}")
    s3_client = None

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, monitored_base_path, target_bucket):
        self.monitored_base_path = monitored_base_path
        self.target_bucket = target_bucket
        super().__init__()

    def _should_process(self, src_path):
        if s3_client is None:
            logging.warning("S3 client not initialized. Cannot process file.")
            return False
        if os.path.isdir(src_path) or not src_path.lower().endswith(SUPPORTED_EXTENSIONS):
            return False
        return True

    def process_event(self, event_type, src_path):
        if not self._should_process(src_path):
            return

        logging.info(f"File event '{event_type}' detected for: {src_path}")
        self.upload_to_minio(src_path)

    def on_created(self, event):
        self.process_event("created", event.src_path)

    def on_modified(self, event):
        self.process_event("modified", event.src_path)

    def upload_to_minio(self, file_path):
        if not os.path.exists(file_path):
            logging.warning(f"File {file_path} not found for upload.")
            return

        # Ambil hanya nama file untuk S3 object key, agar flat di bucket
        #file_name = os.path.basename(file_path)
        #s3_object_name = file_name

        s3_object_name = os.path.relpath(file_path, self.monitored_base_path).replace("\\", "/")

        try:
            logging.info(f"Attempting to upload {file_path} to MinIO bucket '{self.target_bucket}' as '{s3_object_name}'...")
            s3_client.upload_file(file_path, self.target_bucket, s3_object_name)
            logging.info(f"Successfully uploaded {s3_object_name} to {self.target_bucket}/{s3_object_name}")
            # Opsional: Pindahkan file setelah upload
            # processed_dir = os.path.join(os.path.dirname(file_path), "processed_by_streamer")
            # os.makedirs(processed_dir, exist_ok=True)
            # shutil.move(file_path, os.path.join(processed_dir, file_name))
            # logging.info(f"Local file {file_path} moved to {processed_dir}.")
        except FileNotFoundError:
            logging.error(f"File not found during upload attempt: {file_path}.")
        except Exception as e:
            logging.error(f"Failed to upload {file_path} to MinIO: {e}")

    # Jadikan initial_scan_and_upload sebagai method dari class ini
    def initial_scan_and_upload(self):
        """Scan direktori yang dipantau dan upload hanya ke bucket target."""
        if s3_client is None:
            logging.warning("S3 client not initialized. Cannot perform initial scan.")
            return

        logging.info(f"Performing initial scan of {self.monitored_base_path} and uploading to bucket '{self.target_bucket}'")

        for root, _, files in os.walk(self.monitored_base_path):
            for filename in files:
                file_path = os.path.join(root, filename)
                if not file_path.lower().endswith(SUPPORTED_EXTENSIONS):
                    continue
                if not os.path.isfile(file_path): # Pastikan itu file
                    continue

                # Ambil hanya nama file untuk S3 object key, agar flat di bucket
                # Ini akan membuat semua file dari PATH_TO_MONITOR_INSIDE_CONTAINER (termasuk subdirektorinya)
                # ditempatkan langsung di bawah bucket target.
                #s3_object_name = os.path.basename(file_path)
                s3_object_name = os.path.relpath(file_path, self.monitored_base_path).replace("\\", "/")

                try:
                    logging.info(f"Initial scan: Uploading {file_path} to bucket '{self.target_bucket}' as '{s3_object_name}'")
                    s3_client.upload_file(file_path, self.target_bucket, s3_object_name)
                    logging.info(f"Initial scan: Uploaded {s3_object_name} to {self.target_bucket}/{s3_object_name}")
                except Exception as e:
                    logging.error(f"Initial scan: Failed to upload {file_path} to bucket {self.target_bucket}: {e}")

if __name__ == "__main__":
    logging.info(f"Script starting. HOST_DATA_ROOT_IN_CONTAINER: {HOST_DATA_ROOT_IN_CONTAINER}")
    logging.info(f"Script starting. SUBDIR_TO_MONITOR: {SUBDIR_TO_MONITOR}")
    logging.info(f"Script starting. Final PATH_TO_MONITOR_INSIDE_CONTAINER: {PATH_TO_MONITOR_INSIDE_CONTAINER}")
    logging.info(f"Script starting. Target MinIO Bucket: {MINIO_RAW_BUCKET}")
    
    if s3_client is None:
        logging.error("Exiting script: MinIO connection could not be established.")
        exit(1)

    if not os.path.exists(PATH_TO_MONITOR_INSIDE_CONTAINER):
        try:
            os.makedirs(PATH_TO_MONITOR_INSIDE_CONTAINER, exist_ok=True)
            logging.info(f"Monitored directory created/ensured: {PATH_TO_MONITOR_INSIDE_CONTAINER}")
        except Exception as e:
            logging.error(f"Could not create monitored directory {PATH_TO_MONITOR_INSIDE_CONTAINER}: {e}")
            # Tidak exit di sini, karena jika ini adalah mount point, seharusnya sudah ada.
            # Jika tidak ada, Watchdog akan error saat start.

    event_handler = FileChangeHandler(
        monitored_base_path=PATH_TO_MONITOR_INSIDE_CONTAINER,
        target_bucket=MINIO_RAW_BUCKET
    )

    event_handler.initial_scan_and_upload()

    observer = PollingObserver()
    observer.schedule(event_handler, PATH_TO_MONITOR_INSIDE_CONTAINER, recursive=True)

    logging.info(f"Starting to monitor directory: {PATH_TO_MONITOR_INSIDE_CONTAINER} for new/modified files...")
    observer.start()
    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt received, stopping observer...")
    except Exception as e:
        logging.error(f"An unexpected error occurred in the main loop: {e}")
    finally:
        observer.stop()
        observer.join()
        logging.info("Observer stopped. Exiting script.")