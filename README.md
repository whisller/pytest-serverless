pytest-serverless
---
Mock local resources for serverless framework.

| master | PyPI | Python | pytest | Licence |
| --- | --- | --- | --- | --- |
| [![Build Status](https://travis-ci.org/whisller/pytest-serverless.svg?branch=master)](https://travis-ci.org/whisller/pytest-serverless) | [![PyPI](https://img.shields.io/pypi/v/pytest-serverless.svg)](https://pypi.org/project/pytest-serverless/) | ![](https://img.shields.io/pypi/pyversions/pytest-serverless.svg) | `3.10.1`, `4.6.6`, `5.2.4` | ![](https://img.shields.io/pypi/l/pytest-serverless.svg) |


## Installation
```sh
pip install pytest-serverless
```

Your project has to have `pytest` installed.

## What problem it tries to solve?
When building your project with [serverless](https://serverless.com/) most likely you will create
[resources](https://serverless.com/framework/docs/providers/aws/guide/resources/) like dynamodb tables, sqs queues, sns topics.

During writing tests you will have to mock those in [moto](https://github.com/spulec/moto). 

This pytest plugin tries to automate this process by reading `serverless.yml` file and create
moto mocks of resources for you.

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

To start using `my-microservice.my-table` table in your tests just mark your test with `@pytest.mark.usefixtures("serverless")`, and rest will be done by plugin.
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

## Issues?
Plugin is in early stage of development, so you might find some bugs or missing functionality.

If possible create pull request (with tests) that fixes particular problem.
