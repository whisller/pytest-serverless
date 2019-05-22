import os
import re

import boto3
from box import Box
from moto import mock_dynamodb2
import pytest
import yaml


@pytest.fixture(autouse=True)
def setup_mocks():
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
        resources = resources.replace(
            variable[0], eval(f"my_box.{variable[1]}")
        )
    serverless_yml_dict["resources"] = yaml.safe_load(resources)

    for resource_name, resource_definition in (
        serverless_yml_dict.get("resources", {}).get("Resources", {}).items()
    ):
        if resource_definition.get("Type") == "AWS::DynamoDB::Table":
            dynamodb = mock_dynamodb2()

            dynamodb.start()
            boto3.resource("dynamodb").create_table(**resource_definition["Properties"])
            yield
            dynamodb.stop()


def find_self_variables_to_replace(content):
    return re.findall(r"(\${self:([a-zA-Z.]+)})", content)
