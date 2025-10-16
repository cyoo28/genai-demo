import logging
import json
logger = logging.getLogger(__name__)

# S3 client wrapper for CRUD operations
class S3Client:
    def __init__(self, session, bucket):
        # Save the bucket name and S3 Client
        self.bucket = bucket
        self.s3 = session.client("s3")
        logger.debug(f"S3Client initialized for bucket: {bucket}")

    # Helper function to call S3
    def _s3_call(self, func, *args, **kwargs):
        try:
            # Try to execute the call
            return func(*args, **kwargs)
        except self.s3.exceptions.ClientError as e:
            # Log missing object error
            code = e.response["Error"]["Code"]
            if code == "404":
                logger.debug(f"Object not found: {kwargs.get('Key')}")
                return None
            # Log and raise other S3 client error
            logger.error(f"S3 ClientError: {e}", exc_info=True)
            raise
        except Exception as e:
            # Log and raise other error
            logger.error(f"S3 operation failed: {e}", exc_info=True)
            raise

    # Read object from S3
    def obj_read(self, key):
        logger.debug(f"Attempting to read S3 object: {key}")
        # Execute S3 call
        response = self._s3_call(self.s3.get_object, Bucket=self.bucket, Key=key)
        # Get data from object
        data = json.loads(response["Body"].read())
        # Get metadata for object
        meta = response.get("Metadata", {})
        logger.debug(f"Successfully read S3 object: {key}")
        # Return the decoded object
        return data, meta

    # Write object to S3
    def obj_write(self, key, obj, contentType="application/json", metadata=None):
        logger.debug(f"Attempting to write S3 object: {key}")
        # Format response for S3
        body = json.dumps(obj, indent=2).encode("utf-8")
        # Set up S3 object
        params = {
            "Bucket": self.bucket,
            "Key": key,
            "Body": body,
            "ContentType": contentType
        }
        # Add metadata if included
        if metadata:
            params["Metadata"] = metadata
        # Execute S3 call
        self._s3_call(self.s3.put_object, **params)
        logger.debug(f"Successfully wrote S3 object: {key}")
    
    # Delete object from S3
    def obj_delete(self, key):
        logger.debug(f"Attempting to delete S3 object: {key}")
        # Execute S3 call
        self._s3_call(self.s3.delete_object, Bucket=self.bucket, Key=key)
        logger.debug(f"Successfully deleted S3 object: {key}")
    
    # Check that object with key exists in S3
    def obj_check(self, key):
        logger.debug(f"Attempting to find S3 object: {key}")
        # Execute S3 call
        exists = bool(self._s3_call(self.s3.head_object, Bucket=self.bucket, Key=key))
        logger.debug(f"{'Successfully found' if exists else 'Failed to find'} S3 object: {key}")
        # Return status
        return exists
    
    # List objects under prefix in S3
    def obj_list(self, prefix):
        logger.debug(f"Listing objects in bucket {self.bucket} under prefix: {prefix}")
        paginator = self.s3.get_paginator("list_objects_v2")
        # Execute S3 call
        pageIterator = self._s3_call(paginator.paginate, Bucket=self.bucket, Prefix=prefix)
        # List S3 keys under prefix
        keys = [obj["Key"] for page in pageIterator for obj in page.get("Contents", []) if obj["Key"] != prefix]
        logger.debug(f"Found {len(keys)} objects under prefix: {prefix}")
        return keys