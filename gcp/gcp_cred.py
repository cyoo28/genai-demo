import logging
import google.auth
from google.auth.exceptions import DefaultCredentialsError, GoogleAuthError

logger = logging.getLogger(__name__)

# GCP client wrapper for authentication
class GCPCredHelper:
    def __init__(self):
        self.credentials = None
        self.projectId = None
    
    # Get session authentication
    def get_session(self):
        try:
            # Load logged-in profile or service account credentials
            logger.debug("Loading Local Credentials")
            self.credentials, self.projectId = google.auth.default()
            return self.credentials, self.projectId
        # Log and raise Google-specific authentication errors
        except (GoogleAuthError, DefaultCredentialsError) as e:
            logger.error(f"GCP authentication error: {e}")
            raise
        # Log and raise other unexpected errors
        except Exception as e:
            logger.error(f"Unexpected error getting GCP credentials: {e}", exc_info=True)
            raise