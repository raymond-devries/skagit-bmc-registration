"""An AWS Python Pulumi program"""
import json

import boto3
import pulumi
import pulumi_aws as aws
import pulumi_awsx as awsx
import pulumi_random

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

secret_config = aws.secretsmanager.Secret("secret-config")

db_password = pulumi_random.RandomPassword("db-password", length=16, special=False)

database_security_group = aws.ec2.SecurityGroup(
    "database-security-group",
    egress=[
        {
            "cidr_blocks": ["0.0.0.0/0"],
            "from_port": 0,
            "protocol": "-1",
            "to_port": 0,
        }
    ],
    ingress=[
        {
            "cidr_blocks": ["0.0.0.0/0"],
            "from_port": 0,
            "protocol": "-1",
            "to_port": 0,
        }
    ],
)

# database
serverless_postgres_cluster = aws.rds.Cluster(
    "serverless-postgres-cluster",
    database_name="bmcdata",
    engine=aws.rds.EngineType.AURORA_POSTGRESQL,
    engine_mode=aws.rds.EngineMode.PROVISIONED,
    engine_version="16.6",
    master_username="superuser",
    master_password=db_password.result,
    storage_encrypted=True,
    serverlessv2_scaling_configuration={
        "max_capacity": 4,
        "min_capacity": 0,
        "seconds_until_auto_pause": 300,
    },
    # todo remove
    vpc_security_group_ids=[database_security_group.id],
    skip_final_snapshot=True,
)

serverless_postgres_cluster_instance = aws.rds.ClusterInstance(
    "serverless-postgres-cluster-instance",
    cluster_identifier=serverless_postgres_cluster.id,
    instance_class="db.serverless",
    engine=serverless_postgres_cluster.engine,
    engine_version=serverless_postgres_cluster.engine_version,
    publicly_accessible=True,
)

db_url = pulumi.Output.concat(
    "postgres://",
    serverless_postgres_cluster.master_username,
    ":",
    serverless_postgres_cluster.master_password,
    "@",
    serverless_postgres_cluster.endpoint,
    "/",
    serverless_postgres_cluster.database_name,
)

static_files_bucket = aws.s3.BucketV2("static-files-bucket", force_destroy=True)

static_files_bucket_public_access_block = aws.s3.BucketPublicAccessBlock(
    "static-files-bucket-public-access-block",
    bucket=static_files_bucket.bucket,
    block_public_acls=False,
    block_public_policy=False,
    ignore_public_acls=False,
    restrict_public_buckets=False,
)

static_files_bucket_policy = aws.s3.BucketPolicy(
    "static-files-bucket-policy",
    bucket=static_files_bucket.bucket,
    policy=pulumi.Output.json_dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": static_files_bucket.bucket.apply(
                        lambda bucket_name: f"arn:aws:s3:::{bucket_name}/*"
                    ),
                }
            ],
        }
    ),
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

lambda_secret_policy = aws.iam.Policy(
    "lambdaSecretReadPolicy",
    policy=pulumi.Output.json_dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": ["secretsmanager:GetSecretValue"],
                    "Resource": [secret_config.arn],
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

lambda_role_secret_policy_attach = aws.iam.RolePolicyAttachment(
    "lambdaSecretReadPolicyAttachment",
    role=lambda_role.name,
    policy_arn=lambda_secret_policy.arn,
)

# images
repository: aws.ecr.Repository = aws.ecr.Repository(
    "bmc-django-repo",
    name="bmc-django-app-lambda",
    force_delete=True,  # Makes cleanup easier for testing
    image_scanning_configuration=aws.ecr.RepositoryImageScanningConfigurationArgs(
        scan_on_push=True,
    ),
)

image: awsx.ecr.Image = awsx.ecr.Image(
    "bmc-django-lambda-image",
    repository_url=repository.repository_url,
    dockerfile="lambda.Dockerfile",  # Path to your lambda.Dockerfile
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
    environment={"variables": {"AWS_SECRETS_CONFIG_NAME": secret_config.name}},
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

secret_config_version = aws.secretsmanager.SecretVersion(
    "secret-config-version",
    secret_id=secret_config.id,
    secret_string=pulumi.Output.json_dumps(
        {
            "ALLOWED_HOSTS": api_gateway.api_endpoint.apply(
                lambda api_endpoint: api_endpoint.replace("https://", "")
            ),
            "DATABASE_URL": db_url,
            "STATIC_FILES_BUCKET_NAME": static_files_bucket.bucket,
            **constant_secrets,
        }
    ),
)

pulumi.export("secret config name", secret_config.name)
pulumi.export("bucket_name", static_files_bucket.bucket)
pulumi.export("cluster_url", serverless_postgres_cluster.endpoint)
pulumi.export("url", api_gateway.api_endpoint)
