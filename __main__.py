"""An AWS Python Pulumi program"""

import json

import boto3
import pulumi

from infra.get_django_aws import build_stack

STACK = pulumi.get_stack()

config = pulumi.Config()
constant_config = config.require("constant-config")

aws_config = pulumi.Config("aws")
aws_region = aws_config.require("region")
aws_session = boto3.session.Session()

client = aws_session.client(
    service_name="secretsmanager",
    region_name=aws_region,
)
constant_secrets = json.loads(
    client.get_secret_value(SecretId=constant_config)["SecretString"]
)

project_slug = "bmc"
artifacts = build_stack(
    project_slug, "skagit-bmc-dev/dev-dump.json", constant_secrets, "lambda.Dockerfile"
)
