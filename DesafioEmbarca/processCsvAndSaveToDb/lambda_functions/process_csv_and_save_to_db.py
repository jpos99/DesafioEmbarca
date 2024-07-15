import json
import os
from io import StringIO

import boto3
import pandas as pd
import psycopg2
from sqlalchemy import create_engine


class CSVProcessor:
    def __init__(self, bucket_name, db_config):
        self.s3 = boto3.client('s3')
        self.bucket_name = bucket_name
        self.db_config = db_config

    def retrieve_csv_from_s3(self, file_name):
        csv_file = self.s3.get_object(Bucket=self.bucket_name, Key=file_name)
        return csv_file

    def process_csv(self, csv_file):
        csv_data = csv_file['Body'].read().decode('utf-8')
        csv_file = StringIO(csv_data)
        df = pd.read_csv(csv_file, header=0, sep=';', low_memory=False)
        colunas_fixas = ['data', 'horario', 'trecho', 'mortos']
        colunas_veiculos = ['automovel', 'bicicleta', 'caminhao', 'moto', 'onibus']
        df_filtered = df[colunas_fixas + colunas_veiculos]
        novos_registros = []

        for _, row in df_filtered.iterrows():
            for coluna in colunas_veiculos:
                if row[coluna] == 1:
                    novo_registro = row[colunas_fixas].to_dict()
                    novo_registro['veiculo'] = coluna
                    novos_registros.append(novo_registro)

        df_expandido = pd.DataFrame(novos_registros)
        df_expandido['created_at'] = df_expandido['data'] + ' ' + df_expandido['horario']
        df_expandido = df_expandido.drop(columns=['data', 'horario'])

        novos_nomes_colunas = {
            'created_at': 'created_at',
            'trecho': 'road_name',
            'veiculo': 'vehicle',
            'mortos': 'number_deaths',
        }

        df_expandido = df_expandido.rename(columns=novos_nomes_colunas)
        nova_ordem_colunas = ['created_at', 'road_name', 'vehicle', 'number_deaths']
        df_final = df_expandido[nova_ordem_colunas]
        print("df final", df_final.tail(30))

        return df_final

    def save_to_db(self, df):
        try:
            db_url = f"postgresql://{self.db_config['db_user']}:{self.db_config['db_password']}@{self.db_config['db_host']}:{self.db_config['db_port']}/{self.db_config['db_name']}?sslmode=require"
            engine = create_engine(db_url, echo=True)
            df.to_sql('traffic_accidents', engine, if_exists='append', index=False, schema='public')
            return {
                'statusCode': 200,
                'body': f'Successfully processed and saved {len(df)} records to the database.'
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'body': f'Error saving to database: {str(e)}'
            }

    def handler(self, event, context):
        print(f"Received event in lambda2: {event}")
        for record in event['Records']:
            if 's3' in record.keys():
                s3_key = record['s3']['object']['key']
                csv_file = self.retrieve_csv_from_s3(s3_key)
                processed_df = self.process_csv(csv_file)
                print('Processed DataFrame:', processed_df.head())
                self.save_to_db(processed_df)
                return {
                    'statusCode': 200,
                    'body': json.dumps('Data saved to database successfully')
                }


def lambda_handler(event, context):
    bucket_name = os.environ['BUCKET_NAME']
    db_config = {
        'db_host': os.environ['DB_HOST'],
        'db_user': os.environ['DB_USER'],
        'db_password': os.environ['DB_PASSWORD'],
        'db_port': os.environ['DB_PORT'],
        'db_name': os.environ['DB_NAME'],
    }
    processor = CSVProcessor(bucket_name, db_config)
    return processor.handler(event, context)
