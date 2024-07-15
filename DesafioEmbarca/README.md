# Orquestração de Microsserviços com AWS Step Functions

## Visão Geral

Este projeto demonstra a orquestração de microsserviços utilizando AWS Step Functions, Lambda e S3. O projeto consiste em duas funções Lambda:

- **downloadAndUploadToS3**: Faz o download de um CSV a partir de uma URL fornecida e o envia para um bucket S3.
- **processCsvAndSaveToDb**: Recupera o CSV do S3, processa-o e salva os dados em um banco de dados relacional.

## Requisitos

- Serverless Framework
- Conta AWS
- Docker
- Banco de Dados Relacional PostgreSQL

## Configuração

1. **Instale o Serverless Framework**:
    ```sh
    npm install -g serverless
    ```

2. **Configure as credenciais da AWS**:
    ```sh
    aws configure
    ```
3. **Faca login no ECR**:
    ```sh
    aws configure
    ```
   
4. **Crie as imagens Docker das lambdas**:
    Substitua `<aws-account-id>` pelo seu ID de conta AWS.

    ```sh
    docker buildx build --platform linux/amd64 -t <aws-account-id>.dkr.ecr.us-east-2.amazonaws.com/downloadanduploadtos3image:latest ./downloadAndUploadToS3 --push
    docker buildx build --platform linux/amd64 -t <aws-account-id>.dkr.ecr.us-east-2.amazonaws.com/processcsvandsavetodbimage:latest ./processCsvAndSaveToDb --push
    ```

5. **Faça o deploy do serviço**:

    ```sh
    serverless deploy
    ```

    Será retornado a URL do endpoint da API Gateway que deve ser substituída no comando curl `<api-gateway-url>`.

6. **Configure as variáveis de ambiente SSM na AWS CLI**:

    ```sh
    aws ssm put-parameter --name "/microservices-orchestration/dev/db_host" --value "host" --type "String" --overwrite
    aws ssm put-parameter --name "/microservices-orchestration/dev/db_user" --value "user" --type "String" --overwrite
    aws ssm put-parameter --name "/microservices-orchestration/dev/db_password" --value "password" --type "SecureString" --overwrite
    aws ssm put-parameter --name "/microservices-orchestration/dev/db_port" --value "port" --type "String" --overwrite
    aws ssm put-parameter --name "/microservices-orchestration/dev/db_name" --value "name" --type "String" --overwrite
    aws ssm put-parameter --name "/microservices-orchestration/dev/bucket_name" --value "bucketembarca" --type "String" --overwrite
    ```

## Uso

1. **Acione downloadAndUploadToS3** enviando uma requisição POST com um payload JSON contendo a `csv_url`:

    ```sh
    curl -X POST <api-gateway-url>/download \
    -H "Content-Type: application/json" \
    -d '{"csv_url": "https://dados.antt.gov.br/dataset/ef0171a8-f0df-4817-a4ed-b4ff94d87194/resource/aa60ce3a-033a-4864-81dc-ae32bea866e5/download/demostrativo_acidentes_viaaraucaria.csv"}'
    ```
    - O CSV será baixado e enviado para o bucket S3 especificado.
    - A função `processCsvAndSaveToDb` será acionada automaticamente quando o CSV for criado no bucket S3.

## Estrutura do Projeto
- **downloadAndUploadToS3/lambda_functions/s3_consumer.py**: Contém a classe `S3Uploader` e seus métodos.
- **processCsvAndSaveToDb/lambda_functions/process_csv_and_save_to_db.py**: Contém a classe `CSVProcessor` e seus métodos.
- **serverless.yml**: Arquivo de configuração para o Serverless Framework.
- **Dockerfile**: Cada função tem seu arquivo Dockerfile que especifica o container e handler.
- **bootstrap**: Cada função tem seu arquivo bootstrap responsável por chamar a função dentro do container.
- **requirements.txt**: Cada função tem seu arquivo requirements responsável por especificar as dependências de cada função.

## Considerações
- Parti do pré-suposto que as estruturas e configurações necessárias dentro do AWS já estão prontas.
- Os dados obtidos serão duplicados no caso de registros que envolvam mais de um veículo alvo, isso pode gerar distorções em estatísticas de número de acidentes e de mortes.
- A coluna `created_at` do banco relacional possui o formato de string 'YYYY-MM-DD HH:MM'. Este formato foi escolhido por ter uma leitura humana mais fácil e maior flexibilidade para dados que serão armazenados e usados por diversos ambientes e plataformas.
- Acredito que para fins de avaliação de conhecimento de programação e do ambiente AWS esse desafio cumpre seus objetivos. Para uma aplicação real acredito que a abordagem da criação do datalake com suas camadas usuais (RAW, CLEANED, ENRICHED e CURATED) seria mais apropriado.