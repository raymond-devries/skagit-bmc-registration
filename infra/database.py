import pulumi
import pulumi_aws as aws
import pulumi_random

config = pulumi.Config()


def get_supabase_db(db_password: pulumi_random.RandomPassword) -> pulumi.Output[str]:
    """
    To use supabase db run:
    pulumi package add terraform-provider supabase/supabase
    """
    import pulumi_supabase

    supabase_slug = config.require("supabase-slug")
    supabase_config = pulumi.Config("supabase")
    supabase_config.require_secret("accessToken")

    supabase_db = pulumi_supabase.Project(
        "bmc-db",
        database_password=db_password.result,
        organization_id=supabase_slug,
        region="us-west-1",
        name="bmc-test",
    )
    db_url = pulumi.Output.concat(
        "postgres://postgres:",
        supabase_db.database_password,
        "@db.",
        supabase_db.id,
        ".supabase.co/postgres",
    )
    return db_url


def get_aws_serverless_db(
    db_password: pulumi_random.RandomPassword,
) -> pulumi.Output[str]:
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
    return db_url


def get_aws_db_instance(
    db_password: pulumi_random.RandomPassword,
) -> pulumi.Output[str]:
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
    return db_url
