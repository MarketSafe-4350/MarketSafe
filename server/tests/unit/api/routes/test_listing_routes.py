from __future__ import annotations

import io
import unittest
import tempfile
from fastapi import UploadFile
from io import BytesIO
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

import src.api.routes.listing_routes as listing_routes

from src.api.dependencies import (
    get_comment_service,
    get_listing_service,
    get_media_storage,
)
from src.auth.dependencies import get_current_user_id


class TestListingRoutes(unittest.TestCase):
    def setUp(self) -> None:
        self.app = FastAPI()
        self.app.include_router(listing_routes.router)

        self.user_id = 123
        self.app.dependency_overrides[get_current_user_id] = lambda: self.user_id

        self.listing_service = MagicMock(name="listing_service")
        self.app.dependency_overrides[get_listing_service] = (
            lambda: self.listing_service
        )

        self.media_storage = MagicMock(name="media_storage")
        self.app.dependency_overrides[get_media_storage] = (
            lambda: self.media_storage
        )

        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.app.dependency_overrides.clear()



    def test_search_listings_allows_single_character_query(self):
        self.listing_service.search_listings.return_value = []

        response = self.client.get("/listings/search?q=a")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])
        self.listing_service.search_listings.assert_called_once_with(query="a")

    def test_normalized_image_extension_returns_lowercase_file_suffix_when_allowed(self):
        upload = UploadFile(
            filename="photo.PNG",
            file=BytesIO(b"fake-image-bytes"),
            headers={"content-type": "image/png"},
        )

        result = listing_routes._normalized_image_extension(upload)

        self.assertEqual(result, ".png")

    def test_normalized_image_extension_uses_content_type_when_suffix_missing(self):
        upload = UploadFile(
            filename="photo",
            file=BytesIO(b"fake-image-bytes"),
            headers={"content-type": "image/webp"},
        )

        result = listing_routes._normalized_image_extension(upload)

        self.assertEqual(result, ".webp")

    def test_normalized_image_extension_uses_content_type_when_suffix_not_allowed(self):
        upload = UploadFile(
            filename="photo.bmp",
            file=BytesIO(b"fake-image-bytes"),
            headers={"content-type": "image/png"},
        )

        result = listing_routes._normalized_image_extension(upload)

        self.assertEqual(result, ".png")

    def test_normalized_image_extension_defaults_to_jpg_when_unknown(self):
        upload = UploadFile(
            filename="photo.bmp",
            file=BytesIO(b"fake-image-bytes"),
            headers={"content-type": "application/octet-stream"},
        )

        result = listing_routes._normalized_image_extension(upload)

        self.assertEqual(result, ".jpg")
    
    def test_search_listings_rejects_empty_query(self):
        response = self.client.get("/search?q=")

        self.assertEqual(response.status_code, 404)
        self.listing_service.search_listings.assert_not_called()

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

    def test_upload_listing_image_rejects_non_image(self):
        upload = MagicMock()
        upload.content_type = "text/plain"
        upload.filename = "notes.txt"

        with self.assertRaises(ValueError) as ctx:
            import asyncio
            asyncio.run(
                listing_routes._upload_listing_image(upload, self.media_storage)
            )

        self.assertIn("must be an image", str(ctx.exception))
        self.media_storage.upload_bytes.assert_not_called()

    def test_upload_listing_image_uploads_bytes_and_returns_key(self):
        upload = MagicMock()
        upload.content_type = "image/png"
        upload.filename = "x.png"
        upload.read = AsyncMock(return_value=b"fake image bytes")

        fake_uuid = MagicMock()
        fake_uuid.hex = "abc123"

        self.media_storage.upload_bytes.return_value = "/uploads/listings/abc123.png"

        with patch.object(listing_routes.uuid, "uuid4", return_value=fake_uuid):
            import asyncio
            url = asyncio.run(
                listing_routes._upload_listing_image(upload, self.media_storage)
            )

        self.assertEqual(url, "/uploads/listings/abc123.png")
        upload.read.assert_awaited_once()
        self.media_storage.upload_bytes.assert_called_once_with(
            key="listings/abc123.png",
            data=b"fake image bytes",
            content_type="image/png",
        )

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

        with patch.object(
            listing_routes.ListingResponse,
            "from_domain",
            return_value=fake_response_dict,
        ) as from_domain_mock:
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
        from_domain_mock.assert_called_once_with(fake_listing, self.media_storage)
   
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

        with patch.object(
            listing_routes,
            "_upload_listing_image",
            new=AsyncMock(return_value="/uploads/listings/x.jpg"),
        ) as upload_mock, patch.object(
            listing_routes.ListingResponse,
            "from_domain",
            return_value=fake_response_obj,
        ):
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

        upload_mock.assert_awaited_once()
        self.listing_service.create_listing.assert_called_once_with(
            seller_id=self.user_id,
            title="Chair",
            description="Nice",
            price=50.0,
            location="Winnipeg",
            image_url="/uploads/listings/x.jpg",
        )

    def test_create_listing_with_upload_invalid_image_returns_400(self):
        with patch.object(
            listing_routes,
            "_upload_listing_image",
            new=AsyncMock(side_effect=ValueError("Uploaded file must be an image.")),
        ):
            resp = self.client.post(
                "/listings/upload",
                data={
                    "title": "Chair",
                    "description": "Nice",
                    "price": "50.0",
                    "location": "Winnipeg",
                },
                files={"image": ("file.txt", b"notanimage", "text/plain")},
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

    def test_get_all_listing_returns_list_of_listing_responses(self):
        l1 = MagicMock(name="listing1")
        l2 = MagicMock(name="listing2")
        self.listing_service.get_all_listing.return_value = [l1, l2]

        with patch.object(
            listing_routes.ListingResponse,
            "from_domain",
            side_effect=[
                {
                    "id": 1,
                    "seller_id": 123,
                    "title": "A",
                    "description": "D",
                    "price": 1.0,
                    "image_url": None,
                    "location": None,
                    "created_at": None,
                    "is_sold": False,
                },
                {
                    "id": 2,
                    "seller_id": 123,
                    "title": "B",
                    "description": "D",
                    "price": 2.0,
                    "image_url": None,
                    "location": None,
                    "created_at": None,
                    "is_sold": False,
                },
            ],
        ) as from_domain_mock:
            resp = self.client.get("/listings")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 2)
        self.listing_service.get_all_listing.assert_called_once()
        self.assertEqual(from_domain_mock.call_count, 2)

    def test_get_my_listing_returns_list(self):
        l1 = MagicMock()
        self.listing_service.get_listing_by_user_id.return_value = [l1]

        with patch.object(
            listing_routes.ListingResponse,
            "from_domain",
            return_value={
                "id": 1,
                "seller_id": self.user_id,
                "title": "T",
                "description": "D",
                "price": 10.0,
                "image_url": None,
                "location": "L",
                "created_at": None,
                "is_sold": False,
            },
        ) as from_domain_mock:
            resp = self.client.get("/listings/me")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()[0]["seller_id"], self.user_id)
        self.listing_service.get_listing_by_user_id.assert_called_once_with(
            user_id=self.user_id
        )
        from_domain_mock.assert_called_once_with(l1, self.media_storage)

    def test_search_listings_calls_service_and_returns_list(self):
        l1 = MagicMock()
        self.listing_service.search_listings.return_value = [l1]

        with patch.object(
            listing_routes.ListingResponse,
            "from_domain",
            return_value={
                "id": 1,
                "seller_id": 5,
                "title": "Chair",
                "description": "Nice",
                "price": 50.0,
                "image_url": None,
                "location": "Winnipeg",
                "created_at": None,
                "is_sold": False,
            },
        ) as from_domain_mock:
            resp = self.client.get("/listings/search?q=chair")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 1)
        self.listing_service.search_listings.assert_called_once_with(query="chair")
        from_domain_mock.assert_called_once_with(l1, self.media_storage)

    def test_create_listing_json_calls_service_and_returns_listing_response(self):
        fake_listing = MagicMock()
        self.listing_service.create_listing.return_value = fake_listing

        fake_response = {
            "id": 1,
            "seller_id": self.user_id,
            "title": "T",
            "description": "D",
            "price": 10.0,
            "image_url": None,
            "location": "L",
            "created_at": None,
            "is_sold": False,
        }

        with patch.object(
            listing_routes.ListingResponse,
            "from_domain",
            return_value=fake_response,
        ) as from_domain_mock:
            resp = self.client.post(
                "/listings",
                json={
                    "title": "T",
                    "description": "D",
                    "price": 10.0,
                    "location": "L",
                    "image_url": None,
                },
            )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), fake_response)

        self.listing_service.create_listing.assert_called_once_with(
            seller_id=self.user_id,
            title="T",
            description="D",
            price=10.0,
            location="L",
            image_url=None,
        )
        from_domain_mock.assert_called_once_with(fake_listing, self.media_storage)

    def test_get_listings_by_seller_returns_list(self):
        l1 = MagicMock()
        self.listing_service.get_listing_by_user_id.return_value = [l1]

        fake_response = {
            "id": 5,
            "seller_id": 42,
            "title": "Desk",
            "description": "Nice desk",
            "price": 80.0,
            "image_url": None,
            "location": "Winnipeg",
            "created_at": None,
            "is_sold": False,
        }

        with patch.object(
            listing_routes.ListingResponse,
            "from_domain",
            return_value=fake_response,
        ) as from_domain_mock:
            resp = self.client.get("/listings/seller/42")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 1)
        self.assertEqual(resp.json()[0]["seller_id"], 42)
        self.listing_service.get_listing_by_user_id.assert_called_once_with(
            user_id=42
        )
        from_domain_mock.assert_called_once_with(l1, self.media_storage)

    def test_rate_listing_calls_service_and_returns_rating_response(self):
        fake_rating = MagicMock(name="rating_domain")
        self.listing_service.rate_listing.return_value = fake_rating

        fake_response = {
            "id": 1,
            "listing_id": 99,
            "rater_id": self.user_id,
            "transaction_rating": 4,
        }

        with patch.object(
            listing_routes.RatingResponse,
            "from_domain",
            return_value=fake_response,
        ) as from_domain_mock:
            resp = self.client.post(
                "/listings/99/ratings",
                json={"transaction_rating": 4},
            )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), fake_response)
        self.listing_service.rate_listing.assert_called_once_with(
            listing_id=99,
            rater_id=self.user_id,
            transaction_rating=4,
        )
        from_domain_mock.assert_called_once_with(fake_rating)

    def test_get_listing_comment_returns_list(self):
        self.comment_service = MagicMock(name="comment_service")
        self.app.dependency_overrides[get_comment_service] = (
            lambda: self.comment_service
        )

        c1 = MagicMock(name="comment_with_author1")
        c2 = MagicMock(name="comment_with_author2")
        c1.comment, c1.author = MagicMock(), MagicMock()
        c2.comment, c2.author = MagicMock(), MagicMock()

        self.comment_service.get_all_comments_listing.return_value = [c1, c2]

        with patch.object(
            listing_routes.CommentResponse,
            "from_domain",
            side_effect=[
                {
                    "id": 1,
                    "listing_id": 99,
                    "author_id": 123,
                    "author_name": "A B",
                    "body": "x",
                    "created_date": None,
                },
                {
                    "id": 2,
                    "listing_id": 99,
                    "author_id": 555,
                    "author_name": "C D",
                    "body": "y",
                    "created_date": None,
                },
            ],
        ):
            resp = self.client.get("/listings/99/comments")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 2)
        self.comment_service.get_all_comments_listing.assert_called_once_with(
            listing_id=99
        )

    def test_create_listing_comment_calls_service_and_returns_comment_response(self):
        self.comment_service = MagicMock(name="comment_service")
        self.app.dependency_overrides[get_comment_service] = (
            lambda: self.comment_service
        )

        fake_comment_domain = MagicMock(name="comment_domain")
        with patch.object(
            listing_routes.CommentCreate,
            "to_domain",
            return_value=fake_comment_domain,
        ) as to_domain_mock:
            item = MagicMock(name="comment_with_author")
            item.comment = MagicMock()
            item.author = MagicMock()
            self.comment_service.create_comment.return_value = item

            with patch.object(
                listing_routes.CommentResponse,
                "from_domain",
                return_value={
                    "id": 1,
                    "listing_id": 99,
                    "author_id": self.user_id,
                    "author_name": "Test User",
                    "body": "hello",
                    "created_date": None,
                },
            ):
                resp = self.client.post(
                    "/listings/99/comments",
                    json={"body": "hello"},
                )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()["listing_id"], 99)

        to_domain_mock.assert_called_once_with(
            listing_id=99,
            author_id=self.user_id,
        )
        self.comment_service.create_comment.assert_called_once_with(
            actor_id=self.user_id,
            listing_id=99,
            comment=fake_comment_domain,
        )

    def test_normalized_image_extension_uses_filename_suffix_when_valid(self):
        upload = UploadFile(
            filename="photo.png",
            file=BytesIO(b"data"),
            headers={"content-type": "image/jpeg"},
        )
        result = listing_routes._normalized_image_extension(upload)
        self.assertEqual(result, ".png")

    def test_search_listings_rejects_empty_query(self):
        response = self.client.get("/listings/search?q=")
        self.assertEqual(response.status_code, 422)

if __name__ == "__main__":
    unittest.main(verbosity=2)