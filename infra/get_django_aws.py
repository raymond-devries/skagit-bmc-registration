import json
from dataclasses import dataclass

import pulumi
import pulumi_aws as aws
import pulumi_awsx as awsx
import pulumi_command
import pulumi_random

from infra.autotag import register_auto_tags
from infra.common import get_supabase_db, create_management_event


@dataclass
class DeploymentArtifacts:
    management_lambda_function: aws.lambda_.Function


def build_stack(
    project_slug: str,
    seed_data_s3_path: str | None,
    extra_secret_values: dict[str, str] | None,
    docker_file_path: str,
):
    STACK = pulumi.get_stack()

    register_auto_tags(
        {
            "user:Project": pulumi.get_project(),
            "user:Stack": STACK,
        }
    )

    config = pulumi.Config()
    domain_name = config.require("domain_name")
    seed_data_on_startup = config.get_bool("seed_data_on_startup", False)
    protect_data = config.get_bool("protect_data", True)

    supabase_api_key = pulumi.Config("supabase").get_secret("accessToken")

    secret_config = aws.secretsmanager.Secret(
        "secret-config", name_prefix=f"{project_slug}/server/{STACK}"
    )

    # db
    db_password = pulumi_random.RandomPassword("db_password", length=50, special=False)
    db_url, database = get_supabase_db("bmc_db", db_password, protect_data)

    db_backup_bucket = aws.s3.BucketV2(
        "db_backup_bucket",
        force_destroy=True,
        bucket=f"{project_slug}-db-backupbucket-{STACK}",
        opts=pulumi.ResourceOptions(protect=protect_data),
    )

    static_files_bucket = aws.s3.BucketV2(
        "static_files_bucket",
        force_destroy=True,
        bucket=f"{project_slug}-static-{STACK}",
    )

    aws.s3.BucketPublicAccessBlock(
        "static_files_bucket_public_access_block",
        bucket=static_files_bucket.bucket,
        block_public_acls=False,
        block_public_policy=False,
        ignore_public_acls=False,
        restrict_public_buckets=False,
    )

    aws.s3.BucketPolicy(
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
        name=f"{project_slug}_api_gateway_{STACK}",
        protocol_type="HTTP",
        route_selection_expression="$request.method $request.path",
    )

    # email
    email_user = aws.iam.User("email_user", name=f"{project_slug}_email_user_{STACK}")
    aws.iam.UserPolicy(
        "email_user_policy",
        user=email_user.id,
        name=f"{project_slug}_email_user_policy_{STACK}",
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
    django_secret_key = pulumi_random.RandomPassword("django_secret_key", length=50)

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
                "DJANGO_SECRET_KEY": django_secret_key.result,
                **(extra_secret_values or {}),
            }
        ),
    )

    collectstatic_command = pulumi_command.local.Command(
        "collectstatic_command",
        create="python manage.py collectstatic --no-input",
        update="python manage.py collectstatic --no-input",
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
            create=f"aws s3 cp s3://{seed_data_s3_path} - | python manage.py loaddata --format=json -",
            update='echo "Data already seeded"',
            opts=pulumi.ResourceOptions(depends_on=[migrate_command]),
            environment={"AWS_SECRETS_CONFIG_NAME": secret_config.name},
        )

    lambda_secrets_policy = aws.iam.RoleInlinePolicyArgs(
        name="secrets_policy",
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

    lambda_role: aws.iam.Role = aws.iam.Role(
        "lambda_role",
        name=f"{project_slug}_lambda_role_{STACK}",
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
        inline_policies=[lambda_secrets_policy],
    )

    aws.iam.RolePolicyAttachment = aws.iam.RolePolicyAttachment(
        "lambda_role_policy",
        role=lambda_role.name,
        policy_arn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole",
    )

    # images
    lambda_repo: aws.ecr.Repository = aws.ecr.Repository(
        "lambda_repo",
        name=f"{project_slug}_django_app_lambda_{STACK}",
        force_delete=True,  # Makes cleanup easier for testing
        image_scanning_configuration=aws.ecr.RepositoryImageScanningConfigurationArgs(
            scan_on_push=True,
        ),
    )

    lambda_image: awsx.ecr.Image = awsx.ecr.Image(
        "lambda_image",
        repository_url=lambda_repo.repository_url,
        dockerfile=docker_file_path,  # Path to your lambda.Dockerfile
        platform="linux/amd64",  # Important for M1/M2 Mac users
        # todo change to latest
        image_tag="django",
    )

    management_image: awsx.ecr.Image = awsx.ecr.Image(
        "management_image",
        args={"MANAGEMENT": "true"},
        repository_url=lambda_repo.repository_url,
        dockerfile=docker_file_path,  # Path to your lambda.Dockerfile
        platform="linux/amd64",  # Important for M1/M2 Mac users
        image_tag="management",
    )

    lambda_function: aws.lambda_.Function = aws.lambda_.Function(
        "django_app_lambda_function",
        name=f"{project_slug}_django_app_lambda_function_{STACK}",
        package_type="Image",
        image_uri=lambda_image.image_uri,
        role=lambda_role.arn,
        timeout=30,
        memory_size=512,
        environment={"variables": {"AWS_SECRETS_CONFIG_NAME": secret_config.name}},
        image_config=aws.lambda_.FunctionImageConfigArgs(
            commands=["SkagitRegistration.asgi.handler"]
        ),
        opts=pulumi.ResourceOptions(
            depends_on=[migrate_command, collectstatic_command]
        ),
    )

    management_lambda_role = aws.iam.Role(
        "management_lambda_role",
        name=f"{project_slug}_management_lambda_role_{STACK}",
        assume_role_policy=lambda_role.assume_role_policy,
        managed_policy_arns=lambda_role.managed_policy_arns,
        inline_policies=[
            lambda_secrets_policy,
            aws.iam.RoleInlinePolicyArgs(
                name="s3_policy",
                policy=pulumi.Output.json_dumps(
                    {
                        "Version": "2012-10-17",
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Action": [
                                    "s3:GetObject",
                                    "s3:PutObject",
                                    "s3:DeleteObject",
                                    "s3:ListBucket",
                                ],
                                "Resource": [
                                    db_backup_bucket.bucket.apply(
                                        lambda bucket: f"arn:aws:s3:::{bucket}"
                                    ),
                                    db_backup_bucket.bucket.apply(
                                        lambda bucket: f"arn:aws:s3:::{bucket}/*"
                                    ),
                                ],
                            }
                        ],
                    }
                ),
            ),
        ],
    )

    management_lambda_function: aws.lambda_.Function = aws.lambda_.Function(
        "management_lambda_function",
        name=f"management_lambda_function_{STACK}",
        package_type="Image",
        image_uri=management_image.image_uri,
        role=management_lambda_role.arn,
        timeout=30,
        memory_size=512,
        environment={"variables": {"AWS_SECRETS_CONFIG_NAME": secret_config.name}},
        image_config=aws.lambda_.FunctionImageConfigArgs(
            commands=["infra.management_lambdas.management_command"]
        ),
        opts=pulumi.ResourceOptions(depends_on=[migrate_command]),
    )

    create_management_event(
        project_slug,
        STACK,
        management_lambda_function,
        "backup_db_rule",
        "cron(0 10 * * ? *)",
        "backup_db",
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

    aws.apigatewayv2.Route = aws.apigatewayv2.Route(
        "api_route",
        api_id=api_gateway.id,
        route_key="ANY /{proxy+}",
        target=lambda_integration.id.apply(lambda id: f"integrations/{id}"),
    )

    aws.lambda_.Permission(
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
    pulumi.export("url", domain_name)

    return DeploymentArtifacts(management_lambda_function=management_lambda_function)
