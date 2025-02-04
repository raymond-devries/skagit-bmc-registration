"""An AWS Python Pulumi program"""
import json

import boto3
import pulumi
import pulumi_aws as aws
import pulumi_awsx as awsx

ENV_SECRETS_ID = "bmc/prod"
AWS_REGION = "us-west-2"
aws_session = boto3.session.Session()
client = aws_session.client(
    service_name="secretsmanager",
    region_name=AWS_REGION,
)
django_secrets = json.loads(
    client.get_secret_value(SecretId=ENV_SECRETS_ID)["SecretString"]
)


api_gateway: aws.apigatewayv2.Api = aws.apigatewayv2.Api(
    "skagit",
    name="BMC Lambda API",
    protocol_type="HTTP",
    route_selection_expression="$request.method $request.path",
)

lambda_role: aws.iam.Role = aws.iam.Role(
    "bmc-lambda-role",
    assume_role_policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Action": "sts:AssumeRole",
                    "Principal": {"Service": "lambda.amazonaws.com"},
                    "Effect": "Allow",
                    "Sid": "",
                }
            ],
        }
    ),
)

lambda_role_policy: aws.iam.RolePolicyAttachment = aws.iam.RolePolicyAttachment(
    "lambda-role-policy",
    role=lambda_role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
)

repository: aws.ecr.Repository = aws.ecr.Repository(
    "bmc-django-repo",
    name="bmc-django-app-repo",
    force_delete=True,  # Makes cleanup easier for testing
    image_scanning_configuration=aws.ecr.RepositoryImageScanningConfigurationArgs(
        scan_on_push=True,
    ),
)

image: awsx.ecr.Image = awsx.ecr.Image(
    "bmc-django-app-image",
    repository_url=repository.repository_url,
    dockerfile="Dockerfile",  # Path to your Dockerfile
    platform="linux/amd64",  # Important for M1/M2 Mac users
)

lambda_function: aws.lambda_.Function = aws.lambda_.Function(
    "bmc-django-app-lambda-function",
    name="bmc-django-app-lambda-function",
    package_type="Image",
    image_uri=image.image_uri,
    role=lambda_role.arn,
    timeout=30,
    memory_size=512,
    environment={"variables": django_secrets},
)

stage: aws.apigatewayv2.Stage = aws.apigatewayv2.Stage(
    "api-stage", api_id=api_gateway.id, name="$default", auto_deploy=True
)

integration: aws.apigatewayv2.Integration = aws.apigatewayv2.Integration(
    "lambda-integration",
    api_id=api_gateway.id,
    integration_type="AWS_PROXY",
    integration_uri=lambda_function.arn,
    integration_method="POST",
    payload_format_version="2.0",
)

route: aws.apigatewayv2.Route = aws.apigatewayv2.Route(
    "catch-all-route",
    api_id=api_gateway.id,
    route_key="ANY /{proxy+}",
    target=integration.id.apply(lambda id: f"integrations/{id}"),
)

lambda_permission: aws.lambda_.Permission = aws.lambda_.Permission(
    "api-lambda-permission",
    action="lambda:InvokeFunction",
    function=lambda_function.name,
    principal="apigateway.amazonaws.com",
    source_arn=api_gateway.execution_arn.apply(lambda arn: f"{arn}/*/*"),
)


pulumi.export("url", api_gateway.api_endpoint)
