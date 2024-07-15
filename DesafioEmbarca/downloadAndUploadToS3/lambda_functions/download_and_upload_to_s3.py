import json
import os

import boto3
import requests
from botocore.exceptions import NoCredentialsError, PartialCredentialsError


class S3Uploader:
    def __init__(self, bucket_name):
        self.s3 = boto3.client('s3')
        self.bucket_name = bucket_name

    def download_csv_data(self, csv_url):
        print(f"Attempting to download CSV from {csv_url}")
        response = requests.get(csv_url, timeout=30)
        if response.status_code == 200:
            return response.text
        else:
            raise Exception(f"Failed to download CSV. Status code: {response.status_code}")

    def create_csv_file(self, csv_data):
        csv_file_path = '/tmp/csv_to_upload.csv'  # Use /tmp directory for Lambda compatibility
        with open(csv_file_path, 'w') as csv_file:
            csv_file.write(csv_data)
            csv_file.close()
        return csv_file_path

    def upload_to_s3(self, file_name, file_path):
        print(f"Attempting to upload file to S3 bucket {self.bucket_name}")
        try:
            with open(file_path, 'rb') as file:
                self.s3.put_object(Bucket=self.bucket_name, Key=file_name, Body=file)
            print(f"Successfully uploaded {file_name} to {self.bucket_name}")
        except (NoCredentialsError, PartialCredentialsError) as e:
            raise Exception(f"Error uploading to S3: {str(e)}")

    def handler(self, event, context):
        print(f"Received event in lambda1: {event}")
        try:
            if 'body' not in event:
                raise KeyError('body key is missing in the event')

            body = json.loads(event['body'])
            print(f"Parsed body: {body}")

            if 'csv_url' not in body:
                raise KeyError('csv_url key is missing in the body')

            csv_url = body['csv_url']
            print(f"CSV URL: {csv_url}")
            csv_data = self.download_csv_data(csv_url)
            csv_file_path = self.create_csv_file(csv_data)
            file_name = os.path.basename(csv_url)
            print('File name:', file_name)
            self.upload_to_s3(file_name, csv_file_path)
            '''return {
                'statusCode': 200,
                'body': file_name
            }'''
        except KeyError as e:
            return {
                'statusCode': 400,
                'body': f'Key error: {str(e)}'
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'body': str(e)
            }


def lambda_handler(event, context):
    bucket_name = os.environ['BUCKET_NAME']
    uploader = S3Uploader(bucket_name)
    return uploader.handler(event, context)
