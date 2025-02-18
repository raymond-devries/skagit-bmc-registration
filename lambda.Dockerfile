FROM public.ecr.aws/lambda/python:3.13

ARG MANAGEMENT=false

RUN if [ "$MANAGEMENT" = "true" ]; then \
    dnf install postgresql15 -y ; \
fi

COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt

COPY registration ${LAMBDA_TASK_ROOT}/registration
COPY SkagitRegistration ${LAMBDA_TASK_ROOT}/SkagitRegistration
COPY static ${LAMBDA_TASK_ROOT}/static
COPY templates ${LAMBDA_TASK_ROOT}/templates
COPY infra/management_lambdas.py ${LAMBDA_TASK_ROOT}/infra/management_lambdas.py
