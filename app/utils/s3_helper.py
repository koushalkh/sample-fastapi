"""
S3 utilities for handling ABEND log files using functional programming approach.
"""

from io import BytesIO
from typing import Any, Dict, Optional, Tuple

from botocore.exceptions import ClientError, NoCredentialsError
from structlog import get_logger

from app.core.config import settings

logger = get_logger(__name__)


def parse_s3_uri(s3_uri: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse S3 URI into bucket and key components.

    Args:
        s3_uri: S3 URI in format s3://bucket/key

    Returns:
        Tuple of (bucket, key) or (None, None) if invalid
    """
    if not s3_uri or not s3_uri.startswith("s3://"):
        return None, None

    try:
        # Remove s3:// prefix
        path = s3_uri[5:]

        # Split into bucket and key
        parts = path.split("/", 1)
        if len(parts) != 2:
            return None, None

        bucket, key = parts
        return bucket.strip(), key.strip()

    except Exception:
        return None, None


def get_log_content(s3_uri: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    Retrieve log content from S3.

    Args:
        s3_uri: S3 URI in format s3://bucket/key

    Returns:
        Tuple of (content, metadata) where metadata contains file info
    """
    bucket, key = parse_s3_uri(s3_uri)
    if not bucket or not key:
        logger.error("Invalid S3 URI format", s3_uri=s3_uri)
        return None, None

    try:
        logger.info("Retrieving log content from S3", bucket=bucket, key=key)

        # Get object
        response = settings.s3_client.get_object(Bucket=bucket, Key=key)

        # Read content
        content = response["Body"].read().decode("utf-8")

        # Extract metadata
        metadata = {
            "file_size": response.get("ContentLength"),
            "last_modified": response.get("LastModified"),
            "content_type": response.get("ContentType"),
            "etag": response.get("ETag", "").strip('"'),
        }

        logger.info(
            "Successfully retrieved log content",
            bucket=bucket,
            key=key,
            file_size=metadata["file_size"],
        )

        return content, metadata

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "NoSuchKey":
            logger.error("S3 object not found", s3_uri=s3_uri)
        elif error_code == "NoSuchBucket":
            logger.error("S3 bucket not found", s3_uri=s3_uri)
        elif error_code == "AccessDenied":
            logger.error("Access denied to S3 object", s3_uri=s3_uri)
        else:
            logger.error("S3 client error", error_code=error_code, s3_uri=s3_uri)
        return None, None

    except NoCredentialsError:
        logger.error("AWS credentials not found")
        return None, None

    except UnicodeDecodeError:
        logger.error("Unable to decode file content as UTF-8", s3_uri=s3_uri)
        return None, None

    except Exception as e:
        logger.error(
            "Unexpected error retrieving S3 content", error=str(e), s3_uri=s3_uri
        )
        return None, None


def check_file_exists(s3_uri: str) -> bool:
    """
    Check if a file exists in S3.

    Args:
        s3_uri: S3 URI in format s3://bucket/key

    Returns:
        True if file exists, False otherwise
    """
    bucket, key = parse_s3_uri(s3_uri)
    if not bucket or not key:
        return False

    try:
        settings.s3_client.head_object(Bucket=bucket, Key=key)
        return True

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code == "404":
            return False
        logger.error(
            "Error checking S3 file existence", error_code=error_code, s3_uri=s3_uri
        )
        return False

    except Exception as e:
        logger.error("Unexpected error checking S3 file", error=str(e), s3_uri=s3_uri)
        return False


def get_file_metadata(s3_uri: str) -> Optional[Dict[str, Any]]:
    """
    Get file metadata from S3 without downloading content.

    Args:
        s3_uri: S3 URI in format s3://bucket/key

    Returns:
        Dictionary with file metadata or None if error
    """
    bucket, key = parse_s3_uri(s3_uri)
    if not bucket or not key:
        return None

    try:
        response = settings.s3_client.head_object(Bucket=bucket, Key=key)

        return {
            "file_size": response.get("ContentLength"),
            "last_modified": response.get("LastModified"),
            "content_type": response.get("ContentType"),
            "etag": response.get("ETag", "").strip('"'),
        }

    except ClientError as e:
        logger.error("Error getting S3 file metadata", error=str(e), s3_uri=s3_uri)
        return None
    except Exception as e:
        logger.error(
            "Unexpected error getting S3 metadata", error=str(e), s3_uri=s3_uri
        )
        return None


def upload_file_content(
    content: str, s3_uri: str, content_type: str = "text/plain"
) -> bool:
    """
    Upload file content to S3.

    Args:
        content: String content to upload
        s3_uri: S3 URI in format s3://bucket/key
        content_type: MIME type of the content

    Returns:
        True if successful, False otherwise
    """
    bucket, key = parse_s3_uri(s3_uri)
    if not bucket or not key:
        logger.error("Invalid S3 URI format", s3_uri=s3_uri)
        return False

    try:
        logger.info("Uploading content to S3", bucket=bucket, key=key)

        # Convert string to bytes
        content_bytes = content.encode("utf-8")

        settings.s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=BytesIO(content_bytes),
            ContentType=content_type,
            ContentLength=len(content_bytes),
        )

        logger.info("Successfully uploaded content to S3", bucket=bucket, key=key)
        return True

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        logger.error("S3 upload error", error_code=error_code, s3_uri=s3_uri)
        return False

    except Exception as e:
        logger.error("Unexpected error uploading to S3", error=str(e), s3_uri=s3_uri)
        return False


def upload_file_from_path(
    file_path: str, s3_uri: str, content_type: Optional[str] = None
) -> bool:
    """
    Upload a file from local path to S3.

    Args:
        file_path: Local file path
        s3_uri: S3 URI in format s3://bucket/key
        content_type: MIME type of the content (auto-detect if None)

    Returns:
        True if successful, False otherwise
    """
    bucket, key = parse_s3_uri(s3_uri)
    if not bucket or not key:
        logger.error("Invalid S3 URI format", s3_uri=s3_uri)
        return False

    try:
        logger.info("Uploading file to S3", file_path=file_path, bucket=bucket, key=key)

        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type

        settings.s3_client.upload_file(file_path, bucket, key, ExtraArgs=extra_args)

        logger.info(
            "Successfully uploaded file to S3",
            file_path=file_path,
            bucket=bucket,
            key=key,
        )
        return True

    except FileNotFoundError:
        logger.error("Local file not found", file_path=file_path)
        return False

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        logger.error(
            "S3 upload error", error_code=error_code, file_path=file_path, s3_uri=s3_uri
        )
        return False

    except Exception as e:
        logger.error(
            "Unexpected error uploading file to S3",
            error=str(e),
            file_path=file_path,
            s3_uri=s3_uri,
        )
        return False


def move_file(source_s3_uri: str, destination_s3_uri: str) -> bool:
    """
    Move a file from one S3 location to another (copy + delete).

    Args:
        source_s3_uri: Source S3 URI in format s3://bucket/key
        destination_s3_uri: Destination S3 URI in format s3://bucket/key

    Returns:
        True if successful, False otherwise
    """
    source_bucket, source_key = parse_s3_uri(source_s3_uri)
    dest_bucket, dest_key = parse_s3_uri(destination_s3_uri)

    if not all([source_bucket, source_key, dest_bucket, dest_key]):
        logger.error(
            "Invalid S3 URI format",
            source=source_s3_uri,
            destination=destination_s3_uri,
        )
        return False

    try:
        logger.info(
            "Moving file in S3", source=source_s3_uri, destination=destination_s3_uri
        )

        # Copy the object
        copy_source = {"Bucket": source_bucket, "Key": source_key}
        settings.s3_client.copy_object(
            CopySource=copy_source, Bucket=dest_bucket, Key=dest_key
        )

        # Delete the original
        settings.s3_client.delete_object(Bucket=source_bucket, Key=source_key)

        logger.info(
            "Successfully moved file in S3",
            source=source_s3_uri,
            destination=destination_s3_uri,
        )
        return True

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        logger.error(
            "S3 move error",
            error_code=error_code,
            source=source_s3_uri,
            destination=destination_s3_uri,
        )
        return False

    except Exception as e:
        logger.error(
            "Unexpected error moving file in S3",
            error=str(e),
            source=source_s3_uri,
            destination=destination_s3_uri,
        )
        return False


def copy_file(source_s3_uri: str, destination_s3_uri: str) -> bool:
    """
    Copy a file from one S3 location to another.

    Args:
        source_s3_uri: Source S3 URI in format s3://bucket/key
        destination_s3_uri: Destination S3 URI in format s3://bucket/key

    Returns:
        True if successful, False otherwise
    """
    source_bucket, source_key = parse_s3_uri(source_s3_uri)
    dest_bucket, dest_key = parse_s3_uri(destination_s3_uri)

    if not all([source_bucket, source_key, dest_bucket, dest_key]):
        logger.error(
            "Invalid S3 URI format",
            source=source_s3_uri,
            destination=destination_s3_uri,
        )
        return False

    try:
        logger.info(
            "Copying file in S3", source=source_s3_uri, destination=destination_s3_uri
        )

        copy_source = {"Bucket": source_bucket, "Key": source_key}
        settings.s3_client.copy_object(
            CopySource=copy_source, Bucket=dest_bucket, Key=dest_key
        )

        logger.info(
            "Successfully copied file in S3",
            source=source_s3_uri,
            destination=destination_s3_uri,
        )
        return True

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        logger.error(
            "S3 copy error",
            error_code=error_code,
            source=source_s3_uri,
            destination=destination_s3_uri,
        )
        return False

    except Exception as e:
        logger.error(
            "Unexpected error copying file in S3",
            error=str(e),
            source=source_s3_uri,
            destination=destination_s3_uri,
        )
        return False


def delete_file(s3_uri: str) -> bool:
    """
    Delete a file from S3.

    Args:
        s3_uri: S3 URI in format s3://bucket/key

    Returns:
        True if successful, False otherwise
    """
    bucket, key = parse_s3_uri(s3_uri)
    if not bucket or not key:
        logger.error("Invalid S3 URI format", s3_uri=s3_uri)
        return False

    try:
        logger.info("Deleting file from S3", bucket=bucket, key=key)

        settings.s3_client.delete_object(Bucket=bucket, Key=key)

        logger.info("Successfully deleted file from S3", bucket=bucket, key=key)
        return True

    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        logger.error("S3 delete error", error_code=error_code, s3_uri=s3_uri)
        return False

    except Exception as e:
        logger.error(
            "Unexpected error deleting file from S3", error=str(e), s3_uri=s3_uri
        )
        return False
