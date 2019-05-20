import os

import boto3
from moto import mock_dynamodb2
import pytest
import yaml

is_serverless = os.path.isfile("serverless.yml")


@pytest.fixture(autouse=True)
def setup_mocks():
    if not is_serverless:
        return

    with open(os.path.join(os.getcwd(), "serverless.yml")) as f:
        serverless_yml = yaml.safe_load(f)

    if not serverless_yml.get("resources", {}).get("Resources"):
        return

    for resource_name, resource_definition in serverless_yml["resources"]["Resources"].items():
        if resource_definition.get("Type") == "AWS::DynamoDB::Table":
            mock_dynamodb2().start()

            boto3.resource("dynamodb").create_table(**resource_definition["Properties"])
