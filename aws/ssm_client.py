import logging
logger = logging.getLogger(__name__)

# SSM Parameter Store and Secrets Manager client wrapper
class SsmClient:
    def __init__(self, session):
        # Create parameter store client
        self.ssm = session.client("ssm")
        # Create cache
        self.cache = {}
        logger.debug(f"AWSSecretClient initialized")
    
    # Get secret value
    def get(self, name):
        # Check if secret is in cache
        if name not in self.cache:
            logger.debug(f"Secret not in cache: {name}")
            val = None
            try:
                # Look up secret in parameter store
                val = self.ssm.get_parameter(Name=name, WithDecryption=True)["Parameter"]["Value"]
                logger.debug(f"Found secret in Parameter Store: {name}")
            except self.ssm.exceptions.ParameterNotFound:
                # Log and raise not found error if in parameter store
                logger.warning(f"SSM parameter not found: {name}")
                raise KeyError(f"SSM parameter not found: {name}")
            except Exception as e:
                # Raise for other errors
                logger.error(f"Unexpected error fetching secret {name}: {e}", exc_info=True)
                raise
            self.cache[name] = val
        # Return secret
        return self.cache[name]