import boto3
import pytest
import yaml

from pytest_serverless import find_self_variables_to_replace, replace_variables


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
        (
            "apiName: ${self:custom.api_name}",
            [("${self:custom.api_name}", "custom.api_name")],
        ),
        (
            "apiName: ${self:custom.api-name}",
            [("${self:custom.api-name}", "custom.api-name")],
        ),
    ],
)
def test_find_self_variables_to_replace(test_input, expected):
    assert find_self_variables_to_replace(test_input) == expected


class TestReplaceVariables:
    @pytest.mark.parametrize(
        "test_input,expected",
        [
            # Single level of variables to replace
            (
                """service: my-microservice
resources:
 Resources:
   EventQueue:
     Type: "AWS::SQS::Queue"
     Properties:
       QueueName: ${self:service}.queue""",
                """service: my-microservice
resources:
 Resources:
   EventQueue:
     Type: "AWS::SQS::Queue"
     Properties:
       QueueName: my-microservice.queue""",
            ),
            # Double level of variables to replace
            (
                """service: my-microservice
custom:
  sqs_name: "${self:service}-some-queue"
resources:
  Resources:
    EventQueue:
      Type: "AWS::SQS::Queue"
      Properties:
        QueueName: ${self:custom.sqs_name}""",
                """service: my-microservice
custom:
  sqs_name: "my-microservice-some-queue"
resources:
  Resources:
    EventQueue:
      Type: "AWS::SQS::Queue"
      Properties:
        QueueName: my-microservice-some-queue""",
            ),
        ],
    )
    def test_it_replaces_variables(self, test_input, expected):
        assert replace_variables(test_input) == yaml.safe_load(expected)

    @pytest.mark.parametrize(
        "test_input,expected",
        [
            (
                """provider:
deploymentBucket:
  name: ${self:custom.variables.deploymentDomain}
custom:
  variables: ${file(./variables.yml):${opt:stage, 'dev'}}
  other: ${self.custom.does_not_exist}""",
                """provider:
deploymentBucket:
  name: ${self:custom.variables.deploymentDomain}
custom:
  variables: ${file(./variables.yml):${opt:stage, 'dev'}}
  other: ${self.custom.does_not_exist}""",
            )
        ],
    )
    def test_it_handles_unsupported_variables(self, test_input, expected):
        assert replace_variables(test_input) == yaml.safe_load(expected)
