class TestGeneral:
    def test_it_replaces_local_variable_with_its_value(self, testdir):
        with open(testdir.tmpdir + "/serverless.yml", "w") as f:
            f.write(
                """
    service: my-microservice
    resources:
      Resources:
        TokenTable:
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
        TokenTable:
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
