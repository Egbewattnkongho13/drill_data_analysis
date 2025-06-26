FROM public.ecr.aws/lambda/python:3.12

RUN python -m pip install pip~=23.0 \
    --upgrade --no-cache-dir --disable-pip-version-check --no-compile && \ 
    python -m pip install poetry~=1.8.0 \
    --no-cache-dir --disable-pip-version-check --no-compile

RUN poetry export --output=requirements.txt --without-hashes --only=main

COPY requirements.txt ${LAMBDA_TASK_ROOT}


RUN pip install -r requirements.txt


COPY ./clean ${LAMBDA_TASK_ROOT}


CMD [ "clean.lambda_handler" ]