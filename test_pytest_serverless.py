import pytest

from pytest_serverless import find_self_variables_to_replace


class TestGeneral:
    def test_it_replaces_local_variable_with_its_value(self, testdir):
        with open(testdir.tmpdir + "/serverless.yml", "w") as f:
            f.write(
                """
    service: my-microservice
    resources:
      Resources:
        TableA:
          Type: 'AWS::DynamoDB::Table'
          DeletionPolicy: Delete
          Properties:
            TableName: ${self:service}.my-table
            AttributeDefinitions:
              - AttributeName: id
                AttributeType: S
              - AttributeName: company_id
                AttributeType: S
            KeySchema:
              - AttributeName: id
                KeyType: HASH
            GlobalSecondaryIndexes:
              - IndexName: company_id
                KeySchema:
                  - AttributeName: company_id
                    KeyType: HASH
                Projection:
                  ProjectionType: ALL
                ProvisionedThroughput:
                  ReadCapacityUnits: 10
                  WriteCapacityUnits: 30
            ProvisionedThroughput:
              ReadCapacityUnits: 10
              WriteCapacityUnits: 30"""
            )

        testdir.makeconftest('pytest_plugins = ["pytest_serverless"]')
        testdir.makepyfile(
            """
            import boto3

            def test():
                table = boto3.resource("dynamodb").Table("my-microservice.my-table")
                count_of_items = len(table.scan()["Items"])
                assert count_of_items == 0

                table.put_item(Item={"id": "my-id"})
                count_of_items = len(table.scan()["Items"])
                assert count_of_items == 1
            """
        )

        result = testdir.runpytest()
        result.assert_outcomes(passed=1)


class TestDynamoDb:
    def test_it_creates_database_table(self, testdir):
        with open(testdir.tmpdir + "/serverless.yml", "w") as f:
            f.write(
                """resources:
      Resources:
        TableA:
          Type: 'AWS::DynamoDB::Table'
          DeletionPolicy: Delete
          Properties:
            TableName: my-microservice.my-table
            AttributeDefinitions:
              - AttributeName: id
                AttributeType: S
              - AttributeName: company_id
                AttributeType: S
            KeySchema:
              - AttributeName: id
                KeyType: HASH
            GlobalSecondaryIndexes:
              - IndexName: company_id
                KeySchema:
                  - AttributeName: company_id
                    KeyType: HASH
                Projection:
                  ProjectionType: ALL
                ProvisionedThroughput:
                  ReadCapacityUnits: 10
                  WriteCapacityUnits: 30
            ProvisionedThroughput:
              ReadCapacityUnits: 10
              WriteCapacityUnits: 30"""
            )

        testdir.makeconftest('pytest_plugins = ["pytest_serverless"]')
        testdir.makepyfile(
            """
            import boto3

            def test():
                table = boto3.resource("dynamodb").Table("my-microservice.my-table")
                count_of_items = len(table.scan()["Items"])
                assert count_of_items == 0

                table.put_item(Item={"id": "my-id"})
                count_of_items = len(table.scan()["Items"])
                assert count_of_items == 1
            """
        )

        result = testdir.runpytest()
        result.assert_outcomes(passed=1)

    def test_it_creates_multiple_tables(self, testdir):
        with open(testdir.tmpdir + "/serverless.yml", "w") as f:
            f.write(
                """resources:
      Resources:
        TableA:
          Type: 'AWS::DynamoDB::Table'
          DeletionPolicy: Delete
          Properties:
            TableName: my-microservice.my-table
            AttributeDefinitions:
              - AttributeName: id
                AttributeType: S
              - AttributeName: company_id
                AttributeType: S
            KeySchema:
              - AttributeName: id
                KeyType: HASH
            GlobalSecondaryIndexes:
              - IndexName: company_id
                KeySchema:
                  - AttributeName: company_id
                    KeyType: HASH
                Projection:
                  ProjectionType: ALL
                ProvisionedThroughput:
                  ReadCapacityUnits: 10
                  WriteCapacityUnits: 30
            ProvisionedThroughput:
              ReadCapacityUnits: 10
              WriteCapacityUnits: 30
        TableB:
          Type: 'AWS::DynamoDB::Table'
          DeletionPolicy: Delete
          Properties:
            TableName: my-microservice-second.my-table
            AttributeDefinitions:
              - AttributeName: id
                AttributeType: S
              - AttributeName: company_id
                AttributeType: S
            KeySchema:
              - AttributeName: id
                KeyType: HASH
            GlobalSecondaryIndexes:
              - IndexName: company_id
                KeySchema:
                  - AttributeName: company_id
                    KeyType: HASH
                Projection:
                  ProjectionType: ALL
                ProvisionedThroughput:
                  ReadCapacityUnits: 10
                  WriteCapacityUnits: 30
            ProvisionedThroughput:
              ReadCapacityUnits: 10
              WriteCapacityUnits: 30
              """
            )

        testdir.makeconftest('pytest_plugins = ["pytest_serverless"]')
        testdir.makepyfile(
            """
            import boto3

            def test():
                table = boto3.resource("dynamodb").Table("my-microservice.my-table")
                count_of_items = len(table.scan()["Items"])
                assert count_of_items == 0

                table.put_item(Item={"id": "my-id"})
                count_of_items = len(table.scan()["Items"])
                assert count_of_items == 1
                
                table = boto3.resource("dynamodb").Table("my-microservice-second.my-table")
                count_of_items = len(table.scan()["Items"])
                assert count_of_items == 0

                table.put_item(Item={"id": "my-id"})
                count_of_items = len(table.scan()["Items"])
                assert count_of_items == 1
            """
        )

        result = testdir.runpytest()
        result.assert_outcomes(passed=1)


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
