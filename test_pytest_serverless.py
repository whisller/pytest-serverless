import os

import boto3
import pytest


class TestGeneral:
    @pytest.mark.usefixtures("serverless")
    def test_it_replaces_local_variable_with_its_value(self):
        """
        This test checks if `${self:service}` from `serverless.yml` will be replaced with `my-microservice` value
        """
        table = boto3.resource("dynamodb").Table("my-microservice.my-table")
        count_of_items = len(table.scan()["Items"])
        assert count_of_items == 0

        table.put_item(Item={"id": "my-id"})
        count_of_items = len(table.scan()["Items"])
        assert count_of_items == 1

    @pytest.mark.usefixtures("serverless")
    def test_it_sets_environment_variables_defined_in_serverless_yml_file(self):
        assert os.environ.get("SERVICE") == "my-microservice"

    @pytest.mark.usefixtures("serverless")
    def test_it_sets_dynamic_environment_variables_defined_in_serverless_yml_file(self):
        assert os.environ.get("MY_DYNAMIC_TABLE_NAME") == "FnJoin-my-microservicetable"

class TestDynamoDb:
    @pytest.mark.usefixtures("serverless")
    def test_it_creates_database_tables(self):
        table = boto3.resource("dynamodb").Table("my-microservice.my-table")
        count_of_items = len(table.scan()["Items"])
        assert count_of_items == 0

        table.put_item(Item={"id": "my-id"})
        count_of_items = len(table.scan()["Items"])
        assert count_of_items == 1

    @pytest.mark.usefixtures("serverless")
    def test_it_creates_dynamically_named_database_tables(self):
        table_name = os.environ.get('MY_DYNAMIC_TABLE_NAME')
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

    @pytest.mark.usefixtures("serverless")
    def test_it_creates_dynamically_named_sqs_queue(self):
        sqs_client = boto3.client("sqs")
        queue_name = os.environ.get('MY_DYNAMIC_QUEUE_NAME')
        response = sqs_client.get_queue_url(QueueName=queue_name)
        assert response["QueueUrl"] == f"https://queue.amazonaws.com/123456789012/{queue_name}"


class TestS3:
    @pytest.mark.usefixtures("serverless")
    def test_it_creates_s3_bucket(self):
        s3_client = boto3.client("s3")
        response = s3_client.get_bucket_versioning(Bucket="org-example.my-bucket")

        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200

    @pytest.mark.usefixtures("serverless")
    def test_it_creates_dynamically_named_s3_bucket(self):
        s3_client = boto3.client("s3")
        bucket_name = os.environ.get('MY_DYNAMIC_BUCKET_NAME')
        response = s3_client.get_bucket_versioning(Bucket=bucket_name)

        assert response["ResponseMetadata"]["HTTPStatusCode"] == 200

    @pytest.mark.usefixtures("serverless")
    def test_it_removes_s3_bucket_even_if_it_contains_objects(self):
        """
        This test will fail with if we correctly not clean up bucket:
        botocore.exceptions.ClientError: An error occurred (BucketNotEmpty) when calling the DeleteBucket operation: The bucket you tried to delete is not empty
        """
        s3_client = boto3.client("s3")
        s3_client.put_object(
            Body="HappyFace.jpg",
            Bucket="org-example.my-bucket",
            Key="HappyFace.jpg",
            ServerSideEncryption="AES256",
            StorageClass="STANDARD_IA",
        )


class TestSns:
    @pytest.mark.usefixtures("serverless")
    def test_it_creates_sns_topic(self):
        sns_client = boto3.client("sns")
        topic_arns = [arn["TopicArn"] for arn in sns_client.list_topics()["Topics"]]

        assert (
            "arn:aws:sns:us-east-1:123456789012:org-example-my-sns-topic" in topic_arns
        )

    @pytest.mark.usefixtures("serverless")
    def test_it_creates_dynamically_named_sns_topic(self):
        sns_client = boto3.client("sns")
        topic_name = os.environ.get('MY_DYNAMIC_TOPIC_NAME')
        topic_arns = [arn["TopicArn"] for arn in sns_client.list_topics()["Topics"]]

        assert (
            f"arn:aws:sns:us-east-1:123456789012:{topic_name}" in topic_arns
        )


class TestKms:
    @pytest.mark.usefixtures("serverless")
    def test_it_creates_kms_key(self):
        kms_client = boto3.client("kms")
        kms_client.list_keys()
