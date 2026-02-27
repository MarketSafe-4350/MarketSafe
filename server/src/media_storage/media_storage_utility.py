from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Optional

from minio import Minio
from minio.error import S3Error

from src.utils import Validation, StorageUnavailableError, MediaNotFoundError

from io import BytesIO

class MediaStorageUtility:
    """
    MinIO client utility (NOT singleton, NOT static).

    - Creates a MinIO connection client once.
    - Bucket is fixed to 'media'.
    - Pass this instance to other classes (repositories/services)
      that perform upload/download/presign operations.
    """

    BUCKET = "media"

    def __init__(
        self,
        *,
        endpoint: str,          # e.g. "minio:9000" (docker) or "localhost:9000" (host)
        access_key: str,
        secret_key: str,
        secure: bool = False,
        public_base_url: Optional[str] = None,  # e.g. "http://localhost:9000" for browser URLs in dev
        ensure_bucket_on_startup: bool = True,
    ) -> None:
        # ---- validate required inputs (fail fast) ----
        Validation.require_str(endpoint, "endpoint")
        Validation.require_str(access_key, "access_key")
        Validation.require_not_none(secret_key, "secret_key")
        Validation.is_boolean(secure, "secure")

        self._endpoint = endpoint
        self._access_key = access_key
        self._secret_key = secret_key
        self._secure = secure
        self._public_base_url = public_base_url

        self._client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )

        # Optional: ensure bucket exists once at startup
        if ensure_bucket_on_startup:
            self.ensure_bucket_exists()

    # -----------------------------
    # Connection / health helpers
    # -----------------------------

    def ping(self) -> None:
        """
        Fail-fast connectivity check.
        Raises StorageUnavailableError if MinIO cannot be reached or credentials are wrong.
        """
        try:
            # A lightweight call: bucket_exists triggers a request.
            self._client.bucket_exists(self.BUCKET)
        except Exception as e:
            raise StorageUnavailableError("Media storage is unavailable.") from e

    def ensure_bucket_exists(self) -> None:
        """
        Ensure the 'media' bucket exists.
        Safe to call multiple times.
        """
        try:
            if not self._client.bucket_exists(self.BUCKET):
                self._client.make_bucket(self.BUCKET)
        except Exception as e:
            raise StorageUnavailableError("Failed to initialize media bucket.") from e

    # -----------------------------
    # Properties (for other classes)
    # -----------------------------

    @property
    def client(self) -> Minio:
        """Expose the MinIO client so other classes can perform operations."""
        return self._client

    @property
    def bucket(self) -> str:
        return self.BUCKET

    @property
    def endpoint(self) -> str:
        return self._endpoint

    @property
    def secure(self) -> bool:
        return self._secure

    @property
    def public_base_url(self) -> Optional[str]:
        """
        If set, your service layer can rewrite presigned URLs for browser reachability.
        (Docker internal host 'minio' usually isn't reachable from the browser.)
        """
        return self._public_base_url



    def upload_bytes(
            self,
            key: str,
            data: bytes,
            *,
            content_type: str = "application/octet-stream",
    ) -> None:
        """
        Upload raw bytes as an object with the given key.
        """
        Validation.require_str(key, "key")
        Validation.require_not_none(data, "data")

        try:
            bio = BytesIO(data)
            self._client.put_object(
                self.BUCKET,
                key,
                bio,
                length=len(data),
                content_type=content_type,
            )
        except Exception as e:
            raise StorageUnavailableError(message="Failed to upload media.") from e

    def upload_file(
            self,
            key: str,
            file_path: str,
            *,
            content_type: str = "application/octet-stream",
    ) -> None:
        """
        Upload a local file into MinIO under the given key.
        """
        Validation.require_str(key, "key")
        Validation.require_str(file_path, "file_path")

        try:
            self._client.fput_object(
                self.BUCKET,
                key,
                file_path,
                content_type=content_type,
            )
        except Exception as e:
            raise StorageUnavailableError(message="Failed to upload media.") from e


    def presigned_get_url(self, key: str, *, expires_seconds: int = 300) -> str:
        """
        Generate a temporary GET URL for clients.
        Uses public_base_url rewrite if provided.
        """
        Validation.require_str(key, "key")

        try:
            url = self._client.presigned_get_object(
                self.BUCKET,
                key,
                expires=timedelta(seconds=expires_seconds),
            )
        except S3Error as e:

            if e.code in {"NoSuchKey", "NoSuchObject", "NotFound"}:
                raise MediaNotFoundError(message=f"Media '{key}' not found.") from e

            raise StorageUnavailableError(message="Media storage error.") from e
        except Exception as e:
            raise StorageUnavailableError(message="Media storage is unavailable.") from e

        if self._public_base_url:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            base = urlparse(self._public_base_url)
            url = parsed._replace(scheme=base.scheme, netloc=base.netloc).geturl()

        return url

    def list_keys(self, prefix: str = "") -> list[str]:
        try:
            return [obj.object_name for obj in self._client.list_objects(self.BUCKET, prefix=prefix, recursive=True)]
        except Exception as e:
            raise StorageUnavailableError(message="Failed to list media objects.") from e