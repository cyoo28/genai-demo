import os
import logging

from aws_cred import AWSCredHelper
from bedrock_client import BedrockClient
from s3_client import S3Client
from ssm_client import SsmClient
from ses_client import SesClient
from sql_client import SqlClient
from user import UserManager

logger = logging.getLogger(__name__)

class AWSConfig:
    def __init__(self):
        self.configStore = {}
        self.session = None
        self.secretClient = None

    def reset(self):
        self.configStore = {}

    def create(self):
        if self.configStore:
            return self.configStore
        # Set up AWS session
        logger.debug("Setting up AWS session")
        awsProfile = os.environ.get("AWSPROFILE", None)
        awsRegion = os.environ.get("AWSREGION")
        self.session = AWSCredHelper().get_session(awsProfile, awsRegion)
        # Set up secrets manager/parameter store client
        logger.debug("Setting up secrets manager/parameter store client")
        self.secretClient = SsmClient(self.session)
        # Set up SES client
        logger.debug("Setting up SES client")
        self.configStore["sender"] = self.secretClient.get("/genai/sender")
        self.configStore["emailClient"] = SesClient(self.session, self.configStore["sender"])
        # Get SQL host, username, password, and database name
        logger.debug(f"Getting database info from AWS")
        dbHost = os.environ.get("DBHOST") or self.secretClient.get("/genai/dbHost")
        dbName = "genai"
        dbUsername = self.secretClient.get("/genai/dbUsername")
        dbPassword = self.secretClient.get("/genai/dbPassword")
        # Set up SQL client
        logger.debug(f"Setting up SQL client")
        sqlClient = SqlClient(dbHost, dbName, dbUsername, dbPassword)
        self.configStore["userMan"] = UserManager(sqlClient)
        # Get S3 bucket
        logger.debug(f"Setting up s3 client")
        bucket = self.secretClient.get("/genai/bucket")
        # Set up S3 client
        self.configStore["storageClient"] = S3Client(self.session, bucket)
        # Set up bedrock client
        logger.debug(f"Setting up bedrock client")
        self.configStore["genaiClient"] = BedrockClient(self.session, self.configStore["storageClient"])
        return self.configStore