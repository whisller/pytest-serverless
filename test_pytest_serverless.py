import boto3
import pytest

from pytest_serverless import find_self_variables_to_replace


class TestGeneral:
    @pytest.mark.usefixtures("serverless")
    def test_it_replaces_local_variable_with_its_value(self):
        table = boto3.resource("dynamodb").Table("my-microservice.my-table")
        count_of_items = len(table.scan()["Items"])
        assert count_of_items == 0

        table.put_item(Item={"id": "my-id"})
        count_of_items = len(table.scan()["Items"])
        assert count_of_items == 1


class TestDynamoDb:
    @pytest.mark.parametrize(
        "table_name", ["my-microservice.my-table", "my-microservice-second.my-table"]
    )
    @pytest.mark.usefixtures("serverless")
    def test_it_creates_database_tables(self, table_name):
        table = boto3.resource("dynamodb").Table(table_name)
        count_of_items = len(table.scan()["Items"])
        assert count_of_items == 0

        table.put_item(Item={"id": "my-id"})
        count_of_items = len(table.scan()["Items"])
        assert count_of_items == 1


class TestSqs:
    @pytest.mark.usefixtures("serverless")
    def test_it_creates_sqs_queue(self):
        sqs_client = boto3.client("sqs")
        response = sqs_client.get_queue_url(QueueName="my-super-queue")
        assert "my-super-queue" in response["QueueUrl"]


@pytest.mark.parametrize(
    "test_input,expected",
    [
        ("apiName: ${self:service}", [("${self:service}", "service")]),
        (
            "stackName: ${self:service}-${self:provider.stage}",
            [
                ("${self:service}", "service"),
                ("${self:provider.stage}", "provider.stage"),
            ],
        ),
        (
            'name: ${self:custom.variables.deploymentDomain}"',
            [
                (
                    "${self:custom.variables.deploymentDomain}",
                    "custom.variables.deploymentDomain",
                )
            ],
        ),
    ],
)
def test_find_self_variables_to_replace(test_input, expected):
    assert find_self_variables_to_replace(test_input) == expected
