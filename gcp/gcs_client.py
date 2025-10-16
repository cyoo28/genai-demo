import logging
import json
from google.cloud import storage

logger = logging.getLogger(__name__)

# GCS client wrapper for CRUD operations
class GCSClient:
    def __init__(self, session, bucketName):
        # Save the bucket name and GCS client
        self.bucketName = bucketName
        self.GCS = storage.Client(credentials=session["credentials"], project=session["project"])
        self.bucket = self.GCS.bucket(bucketName)
        logger.debug(f"MyGCPClient initialized for bucket: {bucketName}")

    # Helper function to call GCS
    def _gcs_call(self, func, *args, **kwargs):
        try:
            # Try to execute the call
            return func(*args, **kwargs)
        except Exception as e:
            # Log and raise GCP error
            logger.error(f"GCS operation failed: {e}", exc_info=True)
            raise

    # Read object from GCS
    def obj_read(self, key):
        logger.debug(f"Attempting to read GCS object: {key}")
        # Create blob object
        blob = self.bucket.blob(key)
        # Execute GCS call
        blobStr = self._gcs_call(blob.download_as_text)
        # Get data from object
        data = json.loads(blobStr)
        # Get metadata for object
        meta = blob.metadata
        logger.debug(f"Successfully read GCS object: {key}")
        # Return the decoded object
        return data, meta

    # Write object to GCS
    def obj_write(self, key, obj, contentType="application/json", metadata=None):
        logger.debug(f"Attempting to write GCS object: {key}")
        # Create blob object
        blob = self.bucket.blob(key)
        # Format response for GCS
        objStr = json.dumps(obj, indent=2)
        # Add metadata if included
        if metadata:
            blob.metadata = metadata
        # Execute GCS call
        self._gcs_call(blob.upload_from_string, objStr, content_type=contentType)
        logger.debug(f"Successfully wrote GCS object: {key}")

    # Delete object from GCS
    def obj_delete(self, key):
        logger.debug(f"Attempting to delete GCS object: {key}")
        # Create blob object
        blob = self.bucket.blob(key)
        # Execute GCS call
        self._gcs_call(blob.delete)
        logger.debug(f"Successfully deleted GCS object: {key}")
    
    # Check that object with key exists in GCS
    def obj_check(self, key):
        logger.debug(f"Attempting to lookup GCS object with key: {key}")
        # Create blob object
        blob = self.bucket.blob(key)
        # Execute GCS call
        exists = bool(self._gcs_call(blob.exists))
        logger.debug(f"{'Successfully found' if exists else 'Failed to find'} GCS object: {key}")
        # Return status
        return exists
    
    # List objects under prefix in GCS
    def obj_list(self, prefix):
        logger.debug(f"Listing objects in bucket: {self.bucketName} under {prefix}")
        # Execute GCS call
        blobs = self._gcs_call(self.GCS.list_blobs, self.bucketName, prefix=prefix)
        # List GCS keys under prefix
        keys = [blob.name for blob in blobs if blob.name != prefix]
        logger.debug(f"Found {len(keys)} objects in bucket under {prefix}")
        return keys