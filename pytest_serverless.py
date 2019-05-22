import os
import re

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

    serverless_yml_dict = yaml.safe_load(serverless_yml_content)
    resources = yaml.safe_dump(serverless_yml_dict.get("resources"))

    my_box = Box.from_yaml(serverless_yml_content)
    variables_to_replace = find_self_variables_to_replace(resources)

    for variable in variables_to_replace:
        resources = resources.replace(variable[0], eval(f"my_box.{variable[1]}"))
    serverless_yml_dict["resources"] = yaml.safe_load(resources)

    dynamodb_tables = []
    for resource_name, resource_definition in (
        serverless_yml_dict.get("resources", {}).get("Resources", {}).items()
    ):
        if resource_definition.get("Type") == "AWS::DynamoDB::Table":
            dynamodb_tables.append(resource_definition["Properties"])

    if dynamodb_tables:
        from moto import mock_dynamodb2

        dynamodb = mock_dynamodb2()
        dynamodb.start()

        for table_definition in dynamodb_tables:
            boto3.resource("dynamodb").create_table(**table_definition)

        yield

        dynamodb.stop()


def find_self_variables_to_replace(content):
    return re.findall(r"(\${self:([a-zA-Z.]+)})", content)
