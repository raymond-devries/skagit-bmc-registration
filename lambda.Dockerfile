FROM public.ecr.aws/lambda/python:3.11

COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt

COPY registration ${LAMBDA_TASK_ROOT}/registration
COPY SkagitRegistration ${LAMBDA_TASK_ROOT}/SkagitRegistration
COPY static ${LAMBDA_TASK_ROOT}/static
COPY templates ${LAMBDA_TASK_ROOT}/templates

CMD [ "SkagitRegistration.asgi.handler" ]