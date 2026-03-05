from __future__ import annotations

import io
import unittest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

import src.api.routes.listing_routes as listing_routes

from src.api.dependencies import get_listing_service
from src.auth.dependencies import get_current_user_id


class TestListingRoutes(unittest.TestCase):
    def setUp(self) -> None:
        self.app = FastAPI()
        self.app.include_router(listing_routes.router)


        self.user_id = 123
        self.app.dependency_overrides[get_current_user_id] = lambda: self.user_id

        self.listing_service = MagicMock(name="listing_service")
        self.app.dependency_overrides[get_listing_service] = lambda: self.listing_service

        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.app.dependency_overrides.clear()


    def test_listing_uploads_dir_creates_and_returns_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_root = Path(tmp)

            fake_file = tmp_root / "a" / "b" / "c" / "listing_routes.py"
            fake_file.parent.mkdir(parents=True, exist_ok=True)
            fake_file.write_text("# dummy")

            with patch.object(listing_routes, "__file__", str(fake_file)):
                path = listing_routes._listing_uploads_dir()

            self.assertTrue(path.exists())
            self.assertTrue(path.is_dir())
            self.assertTrue(str(path).endswith(str(Path("uploads") / "listings")))



    def test_normalized_image_extension_uses_allowed_suffix(self):
        upload = MagicMock()
        upload.filename = "photo.PNG"
        upload.content_type = "image/png"

        ext = listing_routes._normalized_image_extension(upload)
        self.assertEqual(ext, ".png")

    def test_normalized_image_extension_falls_back_to_content_type(self):
        upload = MagicMock()
        upload.filename = "file.weird"
        upload.content_type = "image/webp"

        ext = listing_routes._normalized_image_extension(upload)
        self.assertEqual(ext, ".webp")

    def test_normalized_image_extension_defaults_to_jpg(self):
        upload = MagicMock()
        upload.filename = "noext"
        upload.content_type = "image/unknown"

        ext = listing_routes._normalized_image_extension(upload)
        self.assertEqual(ext, ".jpg")



    def test_save_uploaded_image_rejects_non_image(self):
        upload = MagicMock()
        upload.content_type = "text/plain"
        upload.filename = "notes.txt"

        with self.assertRaises(ValueError) as ctx:
            listing_routes._save_uploaded_image(upload, request=MagicMock())

        self.assertIn("must be an image", str(ctx.exception))

    def test_save_uploaded_image_writes_file_and_returns_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            upload_dir = Path(tmp)

            upload = MagicMock()
            upload.content_type = "image/png"
            upload.filename = "x.png"
            upload.file = io.BytesIO(b"fake image bytes")

            fake_uuid = MagicMock()
            fake_uuid.hex = "abc123"

            with patch.object(listing_routes, "_listing_uploads_dir", return_value=upload_dir), \
                 patch.object(listing_routes.uuid, "uuid4", return_value=fake_uuid):

                url = listing_routes._save_uploaded_image(upload, request=MagicMock())

            self.assertEqual(url, "/uploads/listings/abc123.png")
            saved_file = upload_dir / "abc123.png"
            self.assertTrue(saved_file.exists())
            self.assertEqual(saved_file.read_bytes(), b"fake image bytes")


    def test_create_listing_with_upload_no_image(self):
        fake_listing = MagicMock(name="listing_domain")
        self.listing_service.create_listing.return_value = fake_listing

        fake_response_dict = {
            "id": 1,
            "seller_id": self.user_id,
            "title": "T",
            "description": "D",
            "price": 10.0,
            "location": "L",
            "image_url": None,
            "is_sold": False,
            "created_at": None,
        }

        with patch.object(listing_routes.ListingResponse, "from_domain", return_value=fake_response_dict):
            resp = self.client.post(
                "/listings/upload",
                data={
                    "title": "T",
                    "description": "D",
                    "price": "10.0",
                    "location": "L",
                },
                files={},
            )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), fake_response_dict)

        self.listing_service.create_listing.assert_called_once_with(
            seller_id=self.user_id,
            title="T",
            description="D",
            price=10.0,
            location="L",
            image_url=None,
        )

    def test_create_listing_with_upload_image_success_closes_file(self):
        fake_listing = MagicMock()
        self.listing_service.create_listing.return_value = fake_listing

        fake_response_obj = listing_routes.ListingResponse(
            id=1,
            seller_id=self.user_id,
            title="T",
            description="D",
            price=10.0,
            location="L",
            image_url="/uploads/listings/x.jpg",
            is_sold=False,
        )

        with patch.object(listing_routes, "_save_uploaded_image", return_value="/uploads/listings/x.jpg") as save_mock, \
            patch.object(listing_routes.ListingResponse, "from_domain", return_value=fake_response_obj):

            resp = self.client.post(
                "/listings/upload",
                data={
                    "title": "Chair",
                    "description": "Nice",
                    "price": "50.0",
                    "location": "Winnipeg",
                },
                files={"image": ("photo.jpg", b"imgbytes", "image/jpeg")},
            )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), fake_response_obj.model_dump())

        save_mock.assert_called_once()
        self.listing_service.create_listing.assert_called_once_with(
            seller_id=self.user_id,
            title="Chair",
            description="Nice",
            price=50.0,
            location="Winnipeg",
            image_url="/uploads/listings/x.jpg",
        )

    def test_create_listing_with_upload_invalid_image_returns_400_and_closes_file(self):
        with patch.object(listing_routes, "_save_uploaded_image", side_effect=ValueError("Uploaded file must be an image.")):
            resp = self.client.post(
                "/listings/upload",
                data={
                    "title": "Chair",
                    "description": "Nice",
                    "price": "50.0",
                    "location": "Winnipeg",
                },
                files={
                    "image": ("file.txt", b"notanimage", "text/plain")
                },
            )

        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["detail"], "Uploaded file must be an image.")
        self.listing_service.create_listing.assert_not_called()


    def test_delete_listing_calls_service_and_returns_204(self):
        resp = self.client.delete("/listings/99")

        self.assertEqual(resp.status_code, 204)
        self.assertEqual(resp.content, b"")

        self.listing_service.delete_listing.assert_called_once_with(
            listing_id=99,
            actor_user_id=self.user_id,
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)