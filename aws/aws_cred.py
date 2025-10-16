import boto3
import logging
logger = logging.getLogger(__name__)

# AWS client wrapper for authentication
class AWSCredHelper:
    def __init__(self):
        self.session = None
    
    # Get session authentication
    def get_session(self, awsProfile=None, awsRegion=None):
        try:
            if awsProfile:
                # If a profile name is provided, use it to create boto3 session
                logger.debug(f"Using AWS profile: {awsProfile} in region: {awsRegion}")
                self.session = boto3.Session(profile_name=awsProfile, region_name=awsRegion)
            else:
                # Otherwise, use default credentials
                logger.debug(f"Using default credentials in region: {awsRegion}")
                self.session = boto3.Session(region_name=awsRegion)
            return self.session
        except Exception as e:
            # Log and raise error
            logger.error(f"Error creating AWS session: {e}", exc_info=True)
            raise