FROM bitnami/spark:3.4

USER root

# Install Python dependencies
RUN pip install pyspark pandas pyarrow

# Copy ETL script
COPY etl_pipeline.py /opt/bitnami/spark/

USER 1001

CMD ["/opt/bitnami/scripts/spark/entrypoint.sh", "/opt/bitnami/scripts/spark/run.sh"]