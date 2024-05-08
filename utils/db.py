from sqlalchemy import create_engine
from google.cloud import storage
import pandas as pd
import os


class DataBaseConfig:
    def __init__(self,table_name:str,url:str,bucket_name:str,blob_name:str):
        self.table_name = table_name
        self.url = url
        self.bucket_name = bucket_name
        self.blob_name = blob_name


class DataBaseHandler:
    def __init__(self,config):
        self.table_name = config.table_name
        self.init_google_conn(config)
        self.init_db(config)

    def init_google_conn(self,config):
        # Google Cloud Storage Initializations
        client = storage.Client()
        bucket = client.get_bucket(config.bucket_name)
        self.blob = bucket.blob(config.blob_name)

    def init_db(self,config):
        self.download_db()

        self.engine = create_engine(config.url)

    def download_db(self):
        if self.blob.exists():
            self.blob.download_to_filename("temp_db_file.db")

    def push_to_db(self,df:pd.DataFrame):
        df.to_sql(self.table_name,con=self.engine,if_exists='append',index=False)

    def upload_blob(self):
        self.blob.upload_from_filename("temp_db_file.db")

        os.remove("temp_db_file.db")