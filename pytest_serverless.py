import os
import subprocess
from collections import defaultdict
from shutil import which

import boto3
import pytest
import yaml
from re import sub
from yaml.scanner import ScannerError

_serverless_yml_dict = None


def _get_property(properties, property_names):
    return {name: properties[name] for name in property_names if name in properties}


def _safe_string(value):
    return sub(r'[^a-zA-Z0-9.\-_]', '', str(value)) if not isinstance(value, str) else value


def _get_string_property(properties, property_names):
    # Some properties must be strings, however they may be defined dynamically (i.e. Fn::Join)
    return {name: _safe_string(properties[name]) for name in property_names if name in properties}


def _handle_dynamodb_table(resources):
    from moto import mock_dynamodb

    dynamodb = mock_dynamodb()

    def before():
        dynamodb.start()

        for resource_definition in resources:
            table_properties = {
                **_get_string_property(
                    resource_definition["Properties"],
                    ["TableName"]
                ),
                **_get_property(
                    resource_definition["Properties"],
                    (
                        "AttributeDefinitions",
                        "KeySchema",
                        "LocalSecondaryIndexes",
                        "GlobalSecondaryIndexes",
                        "BillingMode",
                        "ProvisionedThroughput",
                        "StreamSpecification",
                        "SSESpecification",
                        "Tags",
                    ),
                )
            }

            # boto requires StreamEnabled but Cloudformation doesn't support it so it won't be in serverless.yml
            if 'StreamSpecification' in table_properties:
                table_properties['StreamSpecification']['StreamEnabled'] = True

            boto3.resource("dynamodb").create_table(**table_properties)

    def after():
        for resource_definition in resources:
            boto3.client("dynamodb").delete_table(
                **_get_string_property(resource_definition["Properties"], ["TableName"])
            )

        dynamodb.stop()

    return before, after


def _handle_sqs_queue(resources):
    from moto import mock_sqs

    sqs = mock_sqs()

    def before():
        sqs.start()

        for resource_definition in resources:
            boto3.resource("sqs").create_queue(
                **_get_string_property(resource_definition["Properties"], ["QueueName"])
            )

    def after():
        sqs_client = boto3.client("sqs")
        for resource_definition in resources:

            sqs_client.delete_queue(
                QueueUrl=sqs_client.get_queue_url(
                    **_get_string_property(resource_definition["Properties"], ["QueueName"])
                )["QueueUrl"]
            )

        sqs.stop()

    return before, after


def _handle_s3_bucket(resources):
    from moto import mock_s3

    s3 = mock_s3()

    def before():
        s3.start()

        for resource_definition in resources:
            bucket_name = resource_definition["Properties"].get("BucketName")
            if bucket_name:
                boto3.resource("s3").create_bucket(
                    Bucket=_safe_string(bucket_name),
                    **_get_property(
                        resource_definition["Properties"],
                        (
                            "CreateBucketConfiguration",
                            "ACL",
                            "GrantFullControl",
                            "GrantRead",
                            "GrantReadACP",
                            "GrantWrite",
                            "GrantWriteACP",
                            "ObjectLockEnabledForBucket",
                        ),
                    ),
                )

    def after():
        s3_resource = boto3.resource("s3")

        for resource_definition in resources:
            bucket_name = resource_definition["Properties"].get("BucketName")
            if bucket_name:
                bucket = s3_resource.Bucket(
                    _safe_string(bucket_name)
                )
                bucket.object_versions.delete()

    return before, after


def _handle_sns_topic(resources):
    from moto import mock_sns

    sns = mock_sns()

    def before():
        sns.start()

        for resource_definition in resources:
            topic_name = resource_definition["Properties"].get("TopicName")
            if topic_name:
                boto3.resource("sns").create_topic(
                    Name=_safe_string(topic_name)
                )

    def after():
        sns_client = boto3.client("sns")

        topic_arns = {
            arn["TopicArn"].split(":")[-1]: arn["TopicArn"]
            for arn in sns_client.list_topics()["Topics"]
        }

        for resource_definition in resources:
            topic_name = resource_definition["Properties"].get("TopicName")
            if topic_name:
                sns_client.delete_topic(
                    TopicArn=topic_arns[_safe_string(topic_name)]
                )

        sns.stop()

    return before, after


def _handle_kms_key(resources):
    from moto import mock_kms

    kms = mock_kms()

    def before():
        kms.start()

        for resource_definition in resources:
            params = _get_property(
                resource_definition["Properties"], ("Description", "KeyUsage", "Tags")
            )

            if "KeyPolicy" in resource_definition["Properties"]:
                params["Policy"] = resource_definition["Properties"]["KeyPolicy"]

            if "KeySpec" in resource_definition["Properties"]:
                params["CustomerMasterKeySpec"] = resource_definition["Properties"][
                    "KeySpec"
                ]

            boto3.client("kms").create_key(**params)

    def after():
        kms.stop()

    return before, after


SUPPORTED_RESOURCES = {
    "AWS::DynamoDB::Table": _handle_dynamodb_table,
    "AWS::SQS::Queue": _handle_sqs_queue,
    "AWS::S3::Bucket": _handle_s3_bucket,
    "AWS::SNS::Topic": _handle_sns_topic,
    "AWS::KMS::Key": _handle_kms_key,
}


@pytest.fixture()
def serverless():
    global _serverless_yml_dict
    if not _serverless_yml_dict:
        _serverless_yml_dict = _load_file()

    for k, v in _serverless_yml_dict["provider"].get("environment", {}).items():
        os.environ[k] = _safe_string(v)

    actions_before = []
    actions_after = []

    resources = defaultdict(list)
    for resource_name, definition in (
        _serverless_yml_dict.get("resources", {}).get("Resources", {}).items()
    ):
        resources[definition["Type"]].append(definition)

    for resource_name, resource_function in SUPPORTED_RESOURCES.items():
        if resources.get(resource_name):
            resource = resource_function(resources[resource_name])
            actions_before.append(resource[0])
            actions_after.append(resource[1])

    for action in actions_before:
        action()

    yield

    for action in actions_after:
        action()


def _load_file():
    serverless_path = os.environ.get("SERVERLESS_FILE_PATH", "serverless.yml")
    serverless_command = os.environ.get("SERVERLESS_COMMAND", "sls")

    is_serverless = os.path.isfile(serverless_path)
    if not is_serverless:
        raise Exception("No serverless.yml file found!")

    if serverless_command not in ("sls", "serverless"):
        raise Exception("Command %s not releated to serverless" % serverless_command)

    if not which(serverless_command):
        raise Exception("No %s executable found!" % serverless_command)

    env = os.environ.copy()
    env["SLS_DEPRECATION_DISABLE"] = "*"
    env["SLS_WARNING_DISABLE"] = "*"
    result = subprocess.run([serverless_command, "print", "--config", serverless_path], stdout=subprocess.PIPE, env=env)
    serverless_content = sub(r'Serverless: [^\n]*\n', "", result.stdout.decode("utf-8"))

    try:
        return yaml.safe_load(serverless_content)
    except ScannerError as e:
        pytest.fail(
            f"serverless.yml is wrongly formatted, pytest-serverless is unable to load it: {e}"
        )
