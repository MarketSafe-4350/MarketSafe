# src/api/uploaders/listing_image_uploader.py
from __future__ import annotations

import uuid
from dataclasses import dataclass
from pathlib import Path

from fastapi import UploadFile

from src.media_storage import MediaStorageUtility
from src.utils import ValidationError


@dataclass(frozen=True)
class ListingImageUploader:
    """
    Uploads listing images to object storage (MinIO).

    Design:
    - Stores images in MinIO bucket "media"
    - Returns a stable object key (NOT a URL)
    - Caller should persist the returned key in the Listing record (e.g., Listing.image_url)

    Why:
    - Signed URLs expire, so we never store them in DB.
    - Stateless servers can scale horizontally (all instances share the same storage backend).
    """

    media: MediaStorageUtility
    key_prefix: str = "uploads/listings"

    def save(self, upload: UploadFile) -> str:
        """
        Validate + upload an image to MinIO.

        Args:
            upload: FastAPI UploadFile from multipart/form-data.

        Returns:
            object_key: e.g. "uploads/listings/<uuid>.png"

        Raises:
            ValidationError: if file is not an image or is empty.
            StorageUnavailableError: if MinIO fails (raised from MediaStorageUtility).
        """
        content_type = (upload.content_type or "").strip().lower()
        if not content_type.startswith("image/"):
            raise ValidationError(message="Uploaded file must be an image.")

        ext = self._normalized_image_extension(upload)
        filename = f"{uuid.uuid4().hex}{ext}"
        object_key = f"{self.key_prefix}/{filename}"

        data = upload.file.read()
        if not data:
            raise ValidationError(message="Uploaded file is empty.")

        # Upload to MinIO bucket "media"
        self.media.upload_bytes(key=object_key, data=data, content_type=content_type)

        return object_key

    @staticmethod
    def _normalized_image_extension(upload: UploadFile) -> str:
        """
        Resolve a safe image extension based on filename suffix or content-type.

        Defaults to ".jpg" if unknown.
        """
        allowed = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
        suffix = Path(upload.filename or "").suffix.lower()
        if suffix in allowed:
            return suffix

        by_content_type = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/gif": ".gif",
            "image/webp": ".webp",
        }
        return by_content_type.get((upload.content_type or "").lower(), ".jpg")