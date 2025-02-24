import json
from time import sleep

import httpx
import pulumi
import pulumi_aws as aws
import pulumi_random
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

config = pulumi.Config()


def _healthy(api_key: str, ref: str):
    services = httpx.get(
        f"https://api.supabase.com/v1/projects/{ref}/health",
        headers={"Authorization": f"Bearer {api_key}"},
        params={"services": ["auth", "db", "pooler", "realtime", "rest", "storage"]},
        timeout=30,
    )
    services.raise_for_status()
    return all(service["status"] == "ACTIVE_HEALTHY" for service in services.json())


def wait_for_supabase_deployment(api_key: str, ref: str, timeout: int = 300):
    healthy = _healthy(api_key, ref)
    with Progress(
        SpinnerColumn(),
        TextColumn("DB Status: [progress.description]{task.description}"),
        TimeElapsedColumn(),
    ) as progress:
        progress.add_task("Working", total=None)
        for _ in range(timeout):
            if healthy:
                break
            sleep(2)
            healthy = _healthy(api_key, ref)


def get_supabase_db(
    resource_name, db_password: pulumi_random.RandomPassword, protect: bool
) -> tuple[pulumi.Output[str], pulumi.Resource]:
    """
    To use supabase db run:
    pulumi package add terraform-provider supabase/supabase
    """
    import pulumi_supabase

    supabase_slug = config.require("supabase-slug")
    supabase_config = pulumi.Config("supabase")
    supabase_config.require_secret("accessToken")
    stack = pulumi.get_stack()

    supabase_db = pulumi_supabase.Project(
        resource_name,
        database_password=db_password.result,
        organization_id=supabase_slug,
        region="us-west-1",
        name=f"{resource_name}_{stack}",
        opts=pulumi.ResourceOptions(protect=protect),
    )
    pulumi_supabase.Settings(
        f"{resource_name}_supabase_settings",
        project_ref=supabase_db.id,
        api=json.dumps(
            {
                "db_schema": "",
                "db_extra_search_path": "",
                "max_rows": 1000,
            }
        ),
        opts=pulumi.ResourceOptions(protect=protect),
    )
    db_url = pulumi.Output.concat(
        "postgres://postgres.",
        supabase_db.id,
        ":",
        supabase_db.database_password,
        "@aws-0-",
        supabase_db.region,
        ".pooler.supabase.com:6543/postgres",
    )
    return db_url, supabase_db


def get_aws_serverless_db(
    db_password: pulumi_random.RandomPassword, protect: bool
) -> tuple[pulumi.Output[str], pulumi.Resource]:
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
        master_username="postgres",
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
        opts=pulumi.ResourceOptions(protect=protect),
    )

    serverless_postgres_cluster_instance = aws.rds.ClusterInstance(
        "serverless-postgres-cluster-instance",
        cluster_identifier=serverless_postgres_cluster.id,
        instance_class="db.serverless",
        engine=serverless_postgres_cluster.engine,
        engine_version=serverless_postgres_cluster.engine_version,
        publicly_accessible=True,
        opts=pulumi.ResourceOptions(protect=protect),
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
    return db_url, serverless_postgres_cluster_instance


def get_aws_db_instance(
    db_password: pulumi_random.RandomPassword, protect: bool
) -> tuple[pulumi.Output[str], pulumi.Resource]:
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

    database = aws.rds.Instance(
        "aws-database-instance",
        engine="postgres",
        instance_class="db.t4g.micro",
        allocated_storage=10,
        db_name="mydatabase",
        username="postgres",
        password=db_password.result,
        publicly_accessible=True,
        skip_final_snapshot=True,
        vpc_security_group_ids=[database_security_group.id],
        opts=pulumi.ResourceOptions(protect=protect),
    )

    db_url = pulumi.Output.concat(
        "postgres://",
        database.username,
        ":",
        database.password,
        "@",
        database.endpoint,
        "/",
        database.db_name,
    )
    return db_url, database


def create_management_event(
    project_slug, stack, management_lambda_function, name, schedule, command
):
    event_rule = aws.cloudwatch.EventRule(
        name,
        name=f"{project_slug}_{name}_{stack}",
        schedule_expression=schedule,
    )

    aws.cloudwatch.EventTarget(
        f"{name}_target",
        rule=event_rule.name,
        arn=management_lambda_function.arn,
        input=json.dumps({"command": command}),
    )

    aws.lambda_.Permission(
        f"{name}_permission",
        action="lambda:InvokeFunction",
        function=management_lambda_function.name,
        principal="events.amazonaws.com",
        source_arn=event_rule.arn,
    )
