pytest-serverless
---
Automatically mocks resources defined in serverless.yml file using [moto](https://github.com/spulec/moto) and uses them in [pytest](https://github.com/pytest-dev/pytest).

This way you can focus on writing tests rather than defining enormous list of fixtures.

| master | PyPI | Python | pytest | Licence |
| --- | --- | --- | --- | --- |
| ![Master](https://github.com/whisller/pytest-serverless/workflows/Master/badge.svg) | [![PyPI](https://img.shields.io/pypi/v/pytest-serverless.svg)](https://pypi.org/project/pytest-serverless/) | ![](https://img.shields.io/pypi/pyversions/pytest-serverless.svg) | `6.2` | ![](https://img.shields.io/pypi/l/pytest-serverless.svg) |

## Pre installation requirements
- `serverless` installed
- `pytest` installed

## Installation
```sh
pip install pytest-serverless
```

## Usage
Assuming your `serverless.yml` file looks like:
```yaml
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
         WriteCapacityUnits: 30
```

Just mark your test with `@pytest.mark.usefixtures("serverless")` and `pytest-serverless` will automatically create `my-microservice.my-table` dynamodb table.
```python
import boto3
import pytest


@pytest.mark.usefixtures("serverless")
def test():
    table = boto3.resource("dynamodb").Table("my-microservice.my-table")
    count_of_items = len(table.scan()["Items"])
    assert count_of_items == 0
```

## Supported resources
### AWS::DynamoDB::Table
### AWS::SQS::Queue
### AWS::SNS::Topic
### AWS::S3::Bucket
### AWS::KMS::Key
