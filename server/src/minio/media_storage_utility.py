from __future__ import annotations

from io import BytesIO
from typing import Optional
import json

from minio import Minio
from minio.error import S3Error

from src.utils import Validation, StorageUnavailableError, MediaNotFoundError


class MediaStorageUtility:
    """
    MinIO client utility.

    Public-media version:
    - uploads media
    - ensures bucket exists
    - can make bucket public
    - returns stable public URLs for stored objects
    """

    BUCKET = "media"

    def __init__(
        self,
        *,
        endpoint: str,
        access_key: str,
        secret_key: str,
        secure: bool = False,
        public_base_url: Optional[str] = None,
        ensure_bucket_on_startup: bool = True,
        make_bucket_public_on_startup: bool = False,
    ) -> None:
        Validation.require_str(endpoint, "endpoint")
        Validation.require_str(access_key, "access_key")
        Validation.require_not_none(secret_key, "secret_key")
        Validation.is_boolean(secure, "secure")

        self._endpoint = endpoint
        self._access_key = access_key
        self._secret_key = secret_key
        self._secure = secure
        self._public_base_url = public_base_url.rstrip("/") if public_base_url else None

        self._client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
        )

        if ensure_bucket_on_startup:
            self.ensure_bucket_exists()

        if make_bucket_public_on_startup:
            self.make_bucket_public()

    def ping(self) -> None:
        try:
            self._client.bucket_exists(self.BUCKET)
        except Exception as e:
            raise StorageUnavailableError("Media storage is unavailable.") from e

    def ensure_bucket_exists(self) -> None:
        try:
            if not self._client.bucket_exists(self.BUCKET):
                self._client.make_bucket(self.BUCKET)
        except Exception as e:
            raise StorageUnavailableError("Failed to initialize media bucket.") from e

    def make_bucket_public(self) -> None:
        policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"AWS": ["*"]},
                    "Action": ["s3:GetObject"],
                    "Resource": [f"arn:aws:s3:::{self.BUCKET}/*"],
                }
            ],
        }

        try:
            self._client.set_bucket_policy(self.BUCKET, json.dumps(policy))
        except Exception as e:
            raise StorageUnavailableError("Failed to set public bucket policy.") from e

    @property
    def client(self) -> Minio:
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
        return self._public_base_url

    def upload_bytes(
        self,
        key: str,
        data: bytes,
        *,
        content_type: str = "application/octet-stream",
    ) -> str:
        """
        Upload raw bytes and return the stable public URL.
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
            raise StorageUnavailableError("Failed to upload media.") from e

        return key

    def upload_file(
        self,
        key: str,
        file_path: str,
        *,
        content_type: str = "application/octet-stream",
    ) -> str:
        """
        Upload a local file and return the stable public URL.
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
            raise StorageUnavailableError("Failed to upload media.") from e

        return key

    def object_exists(self, key: str) -> bool:
        Validation.require_str(key, "key")

        try:
            self._client.stat_object(self.BUCKET, key)
            return True
        except S3Error as e:
            if e.code in {"NoSuchKey", "NoSuchObject", "NotFound"}:
                return False
            raise StorageUnavailableError("Media storage error.") from e
        except Exception as e:
            raise StorageUnavailableError("Media storage is unavailable.") from e

    def list_keys(self, prefix: str = "") -> list[str]:
        try:
            return [
                obj.object_name
                for obj in self._client.list_objects(
                    self.BUCKET,
                    prefix=prefix,
                    recursive=True,
                )
            ]
        except Exception as e:
            raise StorageUnavailableError("Failed to list media objects.") from e

    def public_url(self, key: str) -> str:
        Validation.require_str(key, "key")

        if not self._public_base_url:
            raise StorageUnavailableError(
                "Public base URL is not configured for media storage."
            )

        return f"{self._public_base_url}/{self.BUCKET}/{key}"