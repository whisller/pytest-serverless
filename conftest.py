"""
import os

pytest_plugins = ["pytester", "pytest_serverless"]

os.environ["AWS_DEFAULT_REGION"] = "eu-west-1"
os.environ["AWS_ACCESS_KEY_ID"] = "foobar_key"
os.environ["AWS_SECRET_ACCESS_KEY"] = "foobar_secret"
"""