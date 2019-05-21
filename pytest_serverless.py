import os
import re

import boto3
from box import Box
from moto import mock_dynamodb2
import pytest
import yaml

is_serverless = os.path.isfile("serverless.yml")


@pytest.fixture(autouse=True)
def setup_mocks():
    if not is_serverless:
        raise Exception("No serverless.yml file found!")

    with open(os.path.join(os.getcwd(), "serverless.yml")) as f:
        serverless_yml_content = f.read()

    my_box = Box.from_yaml(serverless_yml_content)
    results = re.findall(r"(\${self:(.*)})", serverless_yml_content)

    for result in results:
        serverless_yml_content = serverless_yml_content.replace(
            result[0], eval(f"my_box.{result[1]}")
        )

    serverless_yml_dict = yaml.safe_load(serverless_yml_content)
    for resource_name, resource_definition in (
        serverless_yml_dict.get("resources", {}).get("Resources", {}).items()
    ):
        if resource_definition.get("Type") == "AWS::DynamoDB::Table":
            dynamodb = mock_dynamodb2()

            dynamodb.start()
            boto3.resource("dynamodb").create_table(**resource_definition["Properties"])
            yield
            dynamodb.stop()
