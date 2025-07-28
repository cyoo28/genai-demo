import logging
import json
from google.cloud import storage

logger = logging.getLogger(__name__)

# define an GCS class
class MyGCSClient:
    def __init__(self, bucketName, credentials, project):
        # save the bucket name
        self.bucketName = bucketName
        # create a GCS client
        self.GCS = storage.Client(credentials=credentials, project=project)
        self.bucket = self.GCS.bucket(bucketName)
        logger.debug(f"MyGCPClient initialized for bucket: {bucketName}")
    def obj_read(self, key):
        logger.debug(f"Attempting to read GCS object with key: {key}")
        # try to retrieve the object
        try:
            blob = self.bucket.blob(key)
            blobStr = blob.download_as_text()
            data = json.loads(blobStr)
            metaData = blob.metadata
            logger.debug(f"Successfully read GCS object with key: {key}")
            # return the decoded object
            return data, metaData
        except Exception as e:
            logger.error(f"Error reading GCS object with key {key}: {e}", exc_info=True)
            raise
    def obj_write(self, key, obj, contentType="application/json", metadata=None):
        logger.debug(f"Attempting to write GCS object with key: {key}")
        # try to upload the object
        try:
            blob = self.bucket.blob(key)
            objStr = json.dumps(obj, indent=2)
            if metadata:
                blob.metadata = metadata
            blob.upload_from_string(objStr, content_type=contentType)
            logger.debug(f"Successfully wrote GCS object with key: {key}")
        except Exception as e:
            logger.error(f"Error writing GCS object with key {key}: {e}", exc_info=True)
            raise
    def obj_delete(self, key):
        logger.debug(f"Attempting to delete GCS object with key: {key}")
        # try to delete the object
        try:
            blob = self.bucket.blob(key)
            blob.delete()
            logger.debug(f"Successfully deleted GCS object with key: {key}")
        except Exception as e:
            logger.error(f"Error deleting GCS object with key {key}: {e}", exc_info=True)
            raise
    def obj_lookup(self, key):
        logger.debug(f"Attempting to lookup GCS object with key: {key}")
        # try to retrive head of key
        try:
            blob = self.bucket.blob(key)
            if blob.exists():
                # if it does exist return True
                logger.debug(f"Object found for key: {key}")
                return True
            else:
                # if it doesn't exist return False
                logger.debug(f"Object not found for key: {key}")
                return False
        except Exception as e:
            logger.error(f"Unexpected error looking up object with key {key}: {e}", exc_info=True)
            return None
    def obj_list(self, prefix):
        logger.debug(f"Listing objects in bucket: {self.bucketName} under {prefix}")
        # try to list objects in the bucket
        try:
            blobs = self.GCS.list_blobs(self.bucketName, prefix=prefix)
            keys = [blob.name for blob in blobs if blob.name != prefix]
            logger.debug(f"Found {len(keys)} objects in bucket under {prefix}")
            return keys
        except Exception as e:
            logger.error(f"Error listing objects in bucket under {prefix}: {e}", exc_info=True)
            raise