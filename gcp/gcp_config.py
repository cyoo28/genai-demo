import os
import logging

from gcp_cred import GCPCredHelper
from vertex_client import VertexClient
from gcs_client import GCSClient
from sm_client import SmClient
from brevo_client import BrevoClient
from sql_client import SqlClient
from user import UserManager

logger = logging.getLogger(__name__)

class GCPConfig:
    def __init__(self):
        self.configStore = {}
        self.session = {}
        self.secretClient = None

    def reset(self):
        self.configStore = {}

    def create(self):
        if self.configStore:
            return self.configStore
        # Set up GCP session
        logger.debug("Setting up GCP session")
        self.session["credentials"], self.session["project"] = GCPCredHelper().get_session()
        self.session["project"] = self.session["project"] or os.environ.get("GCPPROJECT")
        # Set up secret manager client
        logger.debug("Setting up secret manager client")
        self.secretClient = SmClient(self.session)
        # Set up brevo email client
        logger.debug("Setting up brevo client")
        brevoApi = self.secretClient.get("genai_brevo")
        self.configStore["sender"] = self.secretClient.get("genai_sender")
        self.configStore["emailClient"] = BrevoClient(brevoApi, self.configStore["sender"])
        # Get SQL host, username, password, and database name
        logger.debug(f"Getting database info from GCP")
        dbHost = os.environ.get("DBHOST") or self.secretClient.get("genai_dbHost")
        dbName = "genai"
        dbUsername = self.secretClient.get("genai_dbUsername")
        dbPassword = self.secretClient.get("genai_dbPassword")
        # Set up SQL client
        logger.debug(f"Setting up SQL client")
        sqlClient = SqlClient(dbHost, dbName, dbUsername, dbPassword)
        self.configStore["userMan"] = UserManager(sqlClient)
        # Get GCS bucket
        logger.debug(f"Setting up GCS client")
        bucket = self.secretClient.get("genai_bucket")
        # Set up GCS client
        self.configStore["storageClient"] = GCSClient(self.session, bucket)
        # Set up vertex client
        logger.debug(f"Setting up vertex client")
        region = os.environ.get("GCPREGION") 
        self.configStore["genaiClient"] = VertexClient(region, self.session, self.configStore["storageClient"])
        return self.configStore