FROM public.ecr.aws/lambda/python:3.12

RUN python -m pip install pip~=23.0 \
    --upgrade --no-cache-dir --disable-pip-version-check --no-compile && \ 
    python -m pip install poetry~=1.8.0 \
    --no-cache-dir --disable-pip-version-check --no-compile

COPY pyproject.toml ${LAMBDA_TASK_ROOT}/pyproject.toml

COPY poetry.lock ${LAMBDA_TASK_ROOT}/poetry.lock

RUN poetry export --output=requirements.txt --without-hashes --only=main

RUN rm -rf pyproject.toml poetry.lock

RUN pip install -r requirements.txt

COPY  ingest ${LAMBDA_TASK_ROOT}/ingest

CMD [ "ingest.lambda_handler" ]