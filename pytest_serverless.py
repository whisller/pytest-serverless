import os
import re
from collections import defaultdict

import boto3
from box import Box
import pytest
import yaml


@pytest.fixture()
def serverless():
    is_serverless = os.path.isfile("serverless.yml")
    if not is_serverless:
        raise Exception("No serverless.yml file found!")

    with open(os.path.join(os.getcwd(), "serverless.yml")) as f:
        serverless_yml_content = f.read()

    serverless_yml_content = remove_env_variables(serverless_yml_content)
    serverless_yml_dict = replace_self_variables(serverless_yml_content)

    actions_before = []
    actions_after = []

    resources = defaultdict(list)
    for resource_name, definition in (
        serverless_yml_dict.get("resources", {}).get("Resources", {}).items()
    ):
        resources[definition["Type"]].append(definition)

    if resources.get("AWS::DynamoDB::Table"):
        dynamodb = handle_dynamodb_table(resources["AWS::DynamoDB::Table"])

        actions_before.append(dynamodb[0])
        actions_after.append(dynamodb[1])

    if resources.get("AWS::SQS::Queue"):
        sqs = handle_sqs_queue(resources["AWS::SQS::Queue"])

        actions_before.append(sqs[0])
        actions_after.append(sqs[1])

    for action in actions_before:
        action()

    yield

    for action in actions_after:
        action()


def handle_dynamodb_table(resources):
    from moto import mock_dynamodb2

    dynamodb = mock_dynamodb2()

    def before():
        dynamodb.start()

        for resource_definition in resources:
            boto3.resource("dynamodb").create_table(**resource_definition["Properties"])

    def after():
        for resource_definition in resources:
            boto3.client("dynamodb").delete_table(
                TableName=resource_definition["Properties"]["TableName"]
            )

        dynamodb.stop()

    return before, after


def handle_sqs_queue(resources):
    from moto import mock_sqs

    sqs = mock_sqs()

    def before():
        sqs.start()

        for resource_definition in resources:
            boto3.resource("sqs").create_queue(**resource_definition["Properties"])

    def after():
        sqs_client = boto3.client("sqs")
        for resource_definition in resources:
            sqs_client.delete_queue(
                QueueUrl=sqs_client.get_queue_url(
                    QueueName=resource_definition["Properties"]["QueueName"]
                )["QueueUrl"]
            )

        sqs.stop()

    return before, after


def find_self_variables_to_replace(content):
    return re.findall(r"(\${self:([a-zA-Z._\-]+)})", content)


def replace_self_variables(serverless_yml_content):
    variables_to_replace = find_self_variables_to_replace(serverless_yml_content)
    for variable in variables_to_replace:
        my_box = Box.from_yaml(serverless_yml_content)
        try:
            value = eval(f"my_box.{variable[1]}")
            serverless_yml_content = serverless_yml_content.replace(variable[0], value)
        except AttributeError:
            pass

    return yaml.safe_load(serverless_yml_content)


def find_env_variables_to_replace(content):
    return re.findall(r"(\${env:([a-zA-Z._\-]+),?(.*)})", content)


def remove_env_variables(serverless_yml_content):
    variables_to_replace = find_env_variables_to_replace(serverless_yml_content)
    for variable in variables_to_replace:
        serverless_yml_content = serverless_yml_content.replace(variable[0], "")

    return serverless_yml_content
