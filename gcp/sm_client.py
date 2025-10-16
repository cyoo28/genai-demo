import logging
from google.cloud.secretmanager import SecretManagerServiceClient as secretsClient
from google.api_core.exceptions import NotFound

logger = logging.getLogger(__name__)

# Secret Manager client wrapper
class SmClient():
    def __init__(self, session):
        # Create secret manager client
        self.client = secretsClient(credentials=session["credentials"])
        self.project_id = session["project"]
        logger.debug(f"GCPSecretStore initialized")

    # Get secret value
    def get(self, name, version="latest"):
        # Set up secret prefix
        secret = f"projects/{self.project_id}/secrets/{name}/versions/{version}"
        try:
            # Look up secret in GCP secret manager
            resp = self.client.access_secret_version(name=secret)
            val = resp.payload.data.decode("UTF-8")
            logger.debug(f"Found secret in Secret Manager: {name}")
        except NotFound:
            # Log and raise not found error
            logger.warning(f"Secret Manager secret not found: {name}")
            raise KeyError(f"Secret Manager secret not found: {name}")
        except Exception as e:
            # Raise for other errors
            logger.error(f"Unexpected error fetching secret {name}: {e}", exc_info=True)
            raise
        # Return secret
        return val