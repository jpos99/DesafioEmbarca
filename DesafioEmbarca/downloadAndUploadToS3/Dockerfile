FROM public.ecr.aws/lambda/python:3.9

# Copie o código do projeto para o contêiner
COPY ./lambda_functions ${LAMBDA_TASK_ROOT}/lambda_functions
COPY ./bootstrap /var/runtime/bootstrap
COPY requirements.txt .

# Instale as dependências
RUN pip install -r requirements.txt
RUN chmod -R 755 /var/runtime/bootstrap ${LAMBDA_TASK_ROOT}/lambda_functions

WORKDIR ${LAMBDA_TASK_ROOT}

# Define o handler
CMD ["lambda_functions.download_and_upload_to_s3.lambda_handler"]
