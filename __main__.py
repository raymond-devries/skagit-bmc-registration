"""An AWS Python Pulumi program"""

import json

import boto3
import pulumi
import pulumi_aws as aws
import pulumi_awsx as awsx
import pulumi_command
import pulumi_random

from infra.autotag import register_auto_tags
from infra.database import get_supabase_db

STACK = pulumi.get_stack()

register_auto_tags(
    {
        "user:Project": pulumi.get_project(),
        "user:Stack": STACK,
    }
)

config = pulumi.Config()
constant_config = config.require("constant-config")
domain_name = config.require("domain_name")
seed_data_on_startup = config.get_bool("seed_data_on_startup", False)
protect_data = config.get_bool("protect_data", True)

aws_config = pulumi.Config("aws")
aws_region = aws_config.require("region")

supabase_slug = config.require("supabase-slug")
supabase_api_key = pulumi.Config("supabase").get_secret("accessToken")

aws_session = boto3.session.Session()
client = aws_session.client(
    service_name="secretsmanager",
    region_name=aws_region,
)
constant_secrets = json.loads(
    client.get_secret_value(SecretId=constant_config)["SecretString"]
)

secret_config = aws.secretsmanager.Secret(
    "secret-config", name_prefix=f"bmc/server/{STACK}"
)

# db
db_password = pulumi_random.RandomPassword("db_password", length=50, special=False)
db_url, database = get_supabase_db("bmc_db", db_password, protect_data)

db_backup_bucket = aws.s3.BucketV2(
    "db_backup_bucket",
    force_destroy=True,
    bucket_prefix=f"dbbackupbucket{STACK}",
    opts=pulumi.ResourceOptions(protect=protect_data),
)

static_files_bucket = aws.s3.BucketV2(
    "static_files_bucket", force_destroy=True, bucket_prefix=f"bmcstatic{STACK}"
)

static_files_bucket_public_access_block = aws.s3.BucketPublicAccessBlock(
    "static_files_bucket_public_access_block",
    bucket=static_files_bucket.bucket,
    block_public_acls=False,
    block_public_policy=False,
    ignore_public_acls=False,
    restrict_public_buckets=False,
)

static_files_bucket_policy = aws.s3.BucketPolicy(
    "static_files_bucket_policy",
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
    "api_gateway",
    name=f"bmc_api_gateway_{STACK}",
    protocol_type="HTTP",
    route_selection_expression="$request.method $request.path",
)

# email
domain_identity = aws.ses.get_domain_identity(domain="skagitalpineclub.com")

email_user = aws.iam.User(f"bmc_email_user", name=f"bmc_email_user_{STACK}")

email_user_policy = aws.iam.UserPolicy(
    "email_user_policy",
    user=email_user.id,
    name=f"bmc_email_user_policy_{STACK}",
    policy=pulumi.Output.json_dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": "ses:SendRawEmail",
                    "Resource": "*",
                }
            ],
        }
    ),
)

email_access_key = aws.iam.AccessKey("email_access_key", user=email_user.name)

secret_config_version = aws.secretsmanager.SecretVersion(
    "secret_config_version",
    secret_id=secret_config.id,
    secret_string=pulumi.Output.json_dumps(
        {
            "ALLOWED_HOSTS": domain_name,
            "DATABASE_URL": db_url,
            "DB_BACKUP_BUCKET": db_backup_bucket.bucket,
            "STATIC_FILES_BUCKET_NAME": static_files_bucket.bucket,
            "EMAIL_HOST_USER": email_access_key.id,
            "EMAIL_HOST_PASSWORD": email_access_key.ses_smtp_password_v4,
            "DJANGO_SECRET_KEY": pulumi_random.RandomPassword(
                "django_secret_key", length=50
            ).result,
            **constant_secrets,
        }
    ),
)

collectstatic_command = pulumi_command.local.Command(
    "collectstatic_command",
    create="python manage.py collectstatic --no-input",
    opts=pulumi.ResourceOptions(
        depends_on=[static_files_bucket, secret_config_version]
    ),
    environment={"AWS_SECRETS_CONFIG_NAME": secret_config.name},
)

check_db_command = pulumi_command.local.Command(
    "check_db_command",
    create=pulumi.Output.all(supabase_api_key, database.id).apply(
        lambda args: f"python infra/check_supabase_deployment.py {args[0]} {args[1]}"
    ),
    opts=pulumi.ResourceOptions(depends_on=[database]),
)

migrate_command = pulumi_command.local.Command(
    "migrate_command",
    create="python manage.py migrate --no-input",
    opts=pulumi.ResourceOptions(
        depends_on=[database, secret_config_version, check_db_command]
    ),
    environment={"AWS_SECRETS_CONFIG_NAME": secret_config.name},
)

if seed_data_on_startup:
    pulumi_command.local.Command(
        "seed_data_on_startup_command",
        create="aws s3 cp s3://skagit-bmc-dev/dev-dump.json - | python manage.py loaddata --format=json -",
        update='echo "Data already seeded"',
        opts=pulumi.ResourceOptions(depends_on=[migrate_command]),
        environment={"AWS_SECRETS_CONFIG_NAME": secret_config.name},
    )

lambda_role: aws.iam.Role = aws.iam.Role(
    "lambda_role",
    name=f"bmc_lambda_role_{STACK}",
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
    "lambda_secret_policy",
    name=f"bmc_lambda_secret_policy_{STACK}",
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
    "lambda_role_policy",
    role=lambda_role.name,
    policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
)

lambda_role_secret_policy_attach = aws.iam.RolePolicyAttachment(
    "lambda_role_secret_policy_attach",
    role=lambda_role.name,
    policy_arn=lambda_secret_policy.arn,
)

# images
lambda_repo: aws.ecr.Repository = aws.ecr.Repository(
    "lambda_repo",
    name=f"bmc_django_app_lambda_{STACK}",
    force_delete=True,  # Makes cleanup easier for testing
    image_scanning_configuration=aws.ecr.RepositoryImageScanningConfigurationArgs(
        scan_on_push=True,
    ),
)

lambda_image: awsx.ecr.Image = awsx.ecr.Image(
    "lambda_image",
    repository_url=lambda_repo.repository_url,
    dockerfile="lambda.Dockerfile",  # Path to your lambda.Dockerfile
    platform="linux/amd64",  # Important for M1/M2 Mac users
    # todo change to latest
    image_tag="django",
)

management_image: awsx.ecr.Image = awsx.ecr.Image(
    "management_image",
    args={"MANAGEMENT": "true"},
    repository_url=lambda_repo.repository_url,
    dockerfile="lambda.Dockerfile",  # Path to your lambda.Dockerfile
    platform="linux/amd64",  # Important for M1/M2 Mac users
    image_tag="management",
)

lambda_function: aws.lambda_.Function = aws.lambda_.Function(
    "bmc_django_app_lambda_function",
    name=f"bmc_django_app_lambda_function_{STACK}",
    package_type="Image",
    image_uri=lambda_image.image_uri,
    role=lambda_role.arn,
    timeout=30,
    memory_size=512,
    environment={"variables": {"AWS_SECRETS_CONFIG_NAME": secret_config.name}},
    image_config=aws.lambda_.FunctionImageConfigArgs(
        commands=["SkagitRegistration.asgi.handler"]
    ),
    opts=pulumi.ResourceOptions(depends_on=[migrate_command, collectstatic_command]),
)

management_lambda_function: aws.lambda_.Function = aws.lambda_.Function(
    "management_lambda_function",
    name=f"management_lambda_function_{STACK}",
    package_type="Image",
    image_uri=management_image.image_uri,
    role=lambda_role.arn,
    timeout=30,
    memory_size=512,
    environment={"variables": {"AWS_SECRETS_CONFIG_NAME": secret_config.name}},
    image_config=aws.lambda_.FunctionImageConfigArgs(
        commands=["infra.management_lambdas.management_command"]
    ),
    opts=pulumi.ResourceOptions(depends_on=[migrate_command]),
)

event_rule = aws.cloudwatch.EventRule(
    "check_invoice_event_rule",
    name=f"bmc_check_invoice_event_rule_{STACK}",
    schedule_expression="cron(0 12 * * ? *)",
    description="Trigger Lambda function daily at 1 am PST",
)

aws.cloudwatch.EventTarget(
    "check_invoice_event_target",
    rule=event_rule.name,
    arn=management_lambda_function.arn,
    input=json.dumps({"command": "check_invoices"}),
)

aws.lambda_.Permission(
    "allowEventBridgeInvocation",
    action="lambda:InvokeFunction",
    function=management_lambda_function.name,
    principal="events.amazonaws.com",
    source_arn=event_rule.arn,
)

api_stage: aws.apigatewayv2.Stage = aws.apigatewayv2.Stage(
    "api_stage", api_id=api_gateway.id, name="$default", auto_deploy=True
)

aws.apigatewayv2.ApiMapping(
    "base_path_mapping",
    api_id=api_gateway.id,
    domain_name=domain_name,
    stage=api_stage.name,
)

lambda_integration: aws.apigatewayv2.Integration = aws.apigatewayv2.Integration(
    "lambda_integration",
    api_id=api_gateway.id,
    integration_type="AWS_PROXY",
    integration_uri=lambda_function.arn,
    integration_method="POST",
    payload_format_version="2.0",
)

api_route: aws.apigatewayv2.Route = aws.apigatewayv2.Route(
    "api_route",
    api_id=api_gateway.id,
    route_key="ANY /{proxy+}",
    target=lambda_integration.id.apply(lambda id: f"integrations/{id}"),
)

api_lambda_permission: aws.lambda_.Permission = aws.lambda_.Permission(
    "api_lambda_permission",
    action="lambda:InvokeFunction",
    function=lambda_function.name,
    principal="apigateway.amazonaws.com",
    source_arn=api_gateway.execution_arn.apply(lambda arn: f"{arn}/*/*"),
)

pulumi.export("seeding data on startup", seed_data_on_startup)
pulumi.export("protect data", protect_data)
pulumi.export("secret config name", secret_config.name)
pulumi.export("bucket_name", static_files_bucket.bucket)
pulumi.export("url", api_gateway.api_endpoint)
