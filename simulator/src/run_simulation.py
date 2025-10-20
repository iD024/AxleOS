import os
import logging
import uuid # For generating unique simulation IDs
import pandas as pd
import boto3 # AWS SDK for Python
from botocore.exceptions import ClientError, Config
import pika # RabbitMQ client library
from io import BytesIO # For in-memory byte streams

# ---- CONFIGURE ----
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

#MINNIO CONFIG
MINIO_ENDPOINT = os.getenv('MINIO_ENDPOINT', 'http://minio:9000')
MINIO_ACCESS_KEY = os.getenv('MINIO_ACCESS_KEY', 'mrid_admin')
MINIO_SECRET_KEY = os.getenv('MINIO_SECRET_KEY', 'mrid_admin12345')

# creates a s3 client to interact with minio
s3 = boto3.client('s3',
                        endpoint_url=MINIO_ENDPOINT,
                        aws_access_key_id=MINIO_ACCESS_KEY,
                        aws_secret_access_key=MINIO_SECRET_KEY,
                        config=boto3.session.Config(signature_version='s3v4'))


#bucket 
MINIO_BUCKET = os.getenv('MINIO_BUCKET', 'raw-telemetry')

# RABBITMQ CONFIG
RABBITMQ_HOST = os.getenv('RABBITMQ_HOST', 'rabbitmq')

SIMULATION_ID = str(uuid.uuid4())


def main():
    logging.info(f"Starting simulation with ID: {SIMULATION_ID}")

    try:
        #first we create fake data to test the pipeline
        logging.info("Generating fake telemetry data...")
        data = {
            'timestamp': [1.0, 1.1, 1.2, 1.3],
            'speed': [0, 5, 10, 15],
            'rpm': [800, 1200, 1500, 1800],
            'throttle': [0.0, 0.2, 0.4, 0.6]
        }
        df = pd.DataFrame(data)
        logging.info(f"Generated fake data")

        # Convert DataFrame to CSV in-memory
        logging.info("Converting DataFrame to Store in memory not in disk")
        parquet_buffer = BytesIO()
        df.to_parquet(parquet_buffer, index=False)
        parquet_buffer.seek(0) # after writing, move the cursor to the beginning of the stream

        #now we upload the data to minio
        logging.info("Uploading data to MinIO...")
        
        data_path= f"simulations/{SIMULATION_ID}/data.parquet"
        logging.info(f"Uploading data to bucket '{MINIO_BUCKET}' at path '{data_path}'")


        s3.upload_fileobj(parquet_buffer, MINIO_BUCKET, data_path)
        logging.info("Upload complete.")


        # after uploading the data we send a message to rabbitmq
        logging.info("Connecting to RabbitMQ...")
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBITMQ_HOST))
        channel = connection.channel()

        channel.queue_declare(queue='data_ready')
        message = f"New data available: bucket={MINIO_BUCKET}, path={data_path}"

        channel.basic_publish(exchange='',
                              routing_key='data_ready',
                              body=message)
        connection.close()
        logging.info("Message sent to RabbitMQ successfully.")


        logging.info("Simulation pipeline completed successfully.")


    except Exception as e:
        logging.error(f"An error occurred in the simulation pipeline: {e}")
        raise