from __future__ import annotations

import json
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from minio.error import S3Error

from src.minio.media_storage_utility import MediaStorageUtility
from src.utils import StorageUnavailableError


class TestMediaStorageUtility(unittest.TestCase):
    def make_s3_error(self, code: str) -> S3Error:
        return S3Error(
            code=code,
            message="msg",
            resource="/media/test",
            request_id="req-1",
            host_id="host-1",
            response=MagicMock(),
        )

    @patch("src.minio.media_storage_utility.Minio")
    def test_init_sets_fields_and_does_not_initialize_bucket_when_disabled(self, mock_minio):
        client = MagicMock()
        mock_minio.return_value = client

        storage = MediaStorageUtility(
            endpoint="localhost:9000",
            access_key="minioadmin",
            secret_key="secret",
            secure=False,
            public_base_url="http://localhost:9000/",
            ensure_bucket_on_startup=False,
            make_bucket_public_on_startup=False,
        )

        mock_minio.assert_called_once_with(
            endpoint="localhost:9000",
            access_key="minioadmin",
            secret_key="secret",
            secure=False,
        )
        self.assertEqual(storage.endpoint, "localhost:9000")
        self.assertFalse(storage.secure)
        self.assertEqual(storage.public_base_url, "http://localhost:9000")
        self.assertEqual(storage.bucket, "media")
        self.assertIs(storage.client, client)

    @patch("src.minio.media_storage_utility.Minio")
    def test_init_calls_bucket_setup_methods_when_enabled(self, mock_minio):
        mock_minio.return_value = MagicMock()

        with (
            patch.object(MediaStorageUtility, "ensure_bucket_exists") as ensure_mock,
            patch.object(MediaStorageUtility, "make_bucket_public") as public_mock,
        ):
            MediaStorageUtility(
                endpoint="localhost:9000",
                access_key="minioadmin",
                secret_key="secret",
                ensure_bucket_on_startup=True,
                make_bucket_public_on_startup=True,
            )

        ensure_mock.assert_called_once()
        public_mock.assert_called_once()

    @patch("src.minio.media_storage_utility.Minio")
    def test_ping_success(self, mock_minio):
        client = MagicMock()
        mock_minio.return_value = client
        storage = MediaStorageUtility(
            endpoint="localhost:9000",
            access_key="a",
            secret_key="b",
            ensure_bucket_on_startup=False,
        )

        storage.ping()

        client.bucket_exists.assert_called_once_with("media")

    @patch("src.minio.media_storage_utility.Minio")
    def test_ping_raises_storage_unavailable_error_on_failure(self, mock_minio):
        client = MagicMock()
        client.bucket_exists.side_effect = Exception("down")
        mock_minio.return_value = client

        storage = MediaStorageUtility(
            endpoint="localhost:9000",
            access_key="a",
            secret_key="b",
            ensure_bucket_on_startup=False,
        )

        with self.assertRaises(StorageUnavailableError):
            storage.ping()

    @patch("src.minio.media_storage_utility.Minio")
    def test_ensure_bucket_exists_creates_bucket_when_missing(self, mock_minio):
        client = MagicMock()
        client.bucket_exists.return_value = False
        mock_minio.return_value = client

        storage = MediaStorageUtility(
            endpoint="localhost:9000",
            access_key="a",
            secret_key="b",
            ensure_bucket_on_startup=False,
        )

        storage.ensure_bucket_exists()

        client.bucket_exists.assert_called_once_with("media")
        client.make_bucket.assert_called_once_with("media")

    @patch("src.minio.media_storage_utility.Minio")
    def test_ensure_bucket_exists_does_not_create_when_bucket_exists(self, mock_minio):
        client = MagicMock()
        client.bucket_exists.return_value = True
        mock_minio.return_value = client

        storage = MediaStorageUtility(
            endpoint="localhost:9000",
            access_key="a",
            secret_key="b",
            ensure_bucket_on_startup=False,
        )

        storage.ensure_bucket_exists()

        client.bucket_exists.assert_called_once_with("media")
        client.make_bucket.assert_not_called()

    @patch("src.minio.media_storage_utility.Minio")
    def test_ensure_bucket_exists_raises_storage_unavailable_error(self, mock_minio):
        client = MagicMock()
        client.bucket_exists.side_effect = Exception("boom")
        mock_minio.return_value = client

        storage = MediaStorageUtility(
            endpoint="localhost:9000",
            access_key="a",
            secret_key="b",
            ensure_bucket_on_startup=False,
        )

        with self.assertRaises(StorageUnavailableError):
            storage.ensure_bucket_exists()

    @patch("src.minio.media_storage_utility.Minio")
    def test_make_bucket_public_sets_expected_policy(self, mock_minio):
        client = MagicMock()
        mock_minio.return_value = client

        storage = MediaStorageUtility(
            endpoint="localhost:9000",
            access_key="a",
            secret_key="b",
            ensure_bucket_on_startup=False,
        )

        storage.make_bucket_public()

        client.set_bucket_policy.assert_called_once()
        bucket_arg, policy_arg = client.set_bucket_policy.call_args.args
        self.assertEqual(bucket_arg, "media")

        policy = json.loads(policy_arg)
        self.assertEqual(policy["Version"], "2012-10-17")
        self.assertEqual(policy["Statement"][0]["Effect"], "Allow")
        self.assertEqual(policy["Statement"][0]["Action"], ["s3:GetObject"])
        self.assertEqual(
            policy["Statement"][0]["Resource"],
            ["arn:aws:s3:::media/*"],
        )

    @patch("src.minio.media_storage_utility.Minio")
    def test_make_bucket_public_raises_storage_unavailable_error(self, mock_minio):
        client = MagicMock()
        client.set_bucket_policy.side_effect = Exception("boom")
        mock_minio.return_value = client

        storage = MediaStorageUtility(
            endpoint="localhost:9000",
            access_key="a",
            secret_key="b",
            ensure_bucket_on_startup=False,
        )

        with self.assertRaises(StorageUnavailableError):
            storage.make_bucket_public()

    @patch("src.minio.media_storage_utility.Minio")
    def test_upload_bytes_success_returns_key(self, mock_minio):
        client = MagicMock()
        mock_minio.return_value = client

        storage = MediaStorageUtility(
            endpoint="localhost:9000",
            access_key="a",
            secret_key="b",
            ensure_bucket_on_startup=False,
        )

        result = storage.upload_bytes(
            "images/a.png",
            b"abc",
            content_type="image/png",
        )

        self.assertEqual(result, "images/a.png")
        client.put_object.assert_called_once()

        args = client.put_object.call_args.args
        kwargs = client.put_object.call_args.kwargs

        self.assertEqual(args[0], "media")
        self.assertEqual(args[1], "images/a.png")
        self.assertEqual(kwargs["length"], 3)
        self.assertEqual(kwargs["content_type"], "image/png")

    @patch("src.minio.media_storage_utility.Minio")
    def test_upload_bytes_raises_storage_unavailable_error(self, mock_minio):
        client = MagicMock()
        client.put_object.side_effect = Exception("boom")
        mock_minio.return_value = client

        storage = MediaStorageUtility(
            endpoint="localhost:9000",
            access_key="a",
            secret_key="b",
            ensure_bucket_on_startup=False,
        )

        with self.assertRaises(StorageUnavailableError):
            storage.upload_bytes("images/a.png", b"abc")

    @patch("src.minio.media_storage_utility.Minio")
    def test_upload_file_success_returns_key(self, mock_minio):
        client = MagicMock()
        mock_minio.return_value = client

        storage = MediaStorageUtility(
            endpoint="localhost:9000",
            access_key="a",
            secret_key="b",
            ensure_bucket_on_startup=False,
        )

        result = storage.upload_file(
            "images/a.png",
            "/tmp/a.png",
            content_type="image/png",
        )

        self.assertEqual(result, "images/a.png")
        client.fput_object.assert_called_once_with(
            "media",
            "images/a.png",
            "/tmp/a.png",
            content_type="image/png",
        )

    @patch("src.minio.media_storage_utility.Minio")
    def test_upload_file_raises_storage_unavailable_error(self, mock_minio):
        client = MagicMock()
        client.fput_object.side_effect = Exception("boom")
        mock_minio.return_value = client

        storage = MediaStorageUtility(
            endpoint="localhost:9000",
            access_key="a",
            secret_key="b",
            ensure_bucket_on_startup=False,
        )

        with self.assertRaises(StorageUnavailableError):
            storage.upload_file("images/a.png", "/tmp/a.png")

    @patch("src.minio.media_storage_utility.Minio")
    def test_object_exists_returns_true_when_object_found(self, mock_minio):
        client = MagicMock()
        mock_minio.return_value = client

        storage = MediaStorageUtility(
            endpoint="localhost:9000",
            access_key="a",
            secret_key="b",
            ensure_bucket_on_startup=False,
        )

        self.assertTrue(storage.object_exists("images/a.png"))
        client.stat_object.assert_called_once_with("media", "images/a.png")

    @patch("src.minio.media_storage_utility.Minio")
    def test_object_exists_returns_false_for_missing_object_codes(self, mock_minio):
        for code in ("NoSuchKey", "NoSuchObject", "NotFound"):
            client = MagicMock()
            client.stat_object.side_effect = self.make_s3_error(code)
            mock_minio.return_value = client

            storage = MediaStorageUtility(
                endpoint="localhost:9000",
                access_key="a",
                secret_key="b",
                ensure_bucket_on_startup=False,
            )

            self.assertFalse(storage.object_exists("images/a.png"))

    @patch("src.minio.media_storage_utility.Minio")
    def test_object_exists_raises_storage_unavailable_error_for_other_s3_errors(self, mock_minio):
        client = MagicMock()
        client.stat_object.side_effect = self.make_s3_error("AccessDenied")
        mock_minio.return_value = client

        storage = MediaStorageUtility(
            endpoint="localhost:9000",
            access_key="a",
            secret_key="b",
            ensure_bucket_on_startup=False,
        )

        with self.assertRaises(StorageUnavailableError):
            storage.object_exists("images/a.png")

    @patch("src.minio.media_storage_utility.Minio")
    def test_object_exists_raises_storage_unavailable_error_for_general_exception(self, mock_minio):
        client = MagicMock()
        client.stat_object.side_effect = Exception("boom")
        mock_minio.return_value = client

        storage = MediaStorageUtility(
            endpoint="localhost:9000",
            access_key="a",
            secret_key="b",
            ensure_bucket_on_startup=False,
        )

        with self.assertRaises(StorageUnavailableError):
            storage.object_exists("images/a.png")

    @patch("src.minio.media_storage_utility.Minio")
    def test_list_keys_returns_object_names(self, mock_minio):
        client = MagicMock()
        client.list_objects.return_value = [
            SimpleNamespace(object_name="a.png"),
            SimpleNamespace(object_name="folder/b.png"),
        ]
        mock_minio.return_value = client

        storage = MediaStorageUtility(
            endpoint="localhost:9000",
            access_key="a",
            secret_key="b",
            ensure_bucket_on_startup=False,
        )

        result = storage.list_keys(prefix="folder/")

        self.assertEqual(result, ["a.png", "folder/b.png"])
        client.list_objects.assert_called_once_with(
            "media",
            prefix="folder/",
            recursive=True,
        )

    @patch("src.minio.media_storage_utility.Minio")
    def test_list_keys_raises_storage_unavailable_error(self, mock_minio):
        client = MagicMock()
        client.list_objects.side_effect = Exception("boom")
        mock_minio.return_value = client

        storage = MediaStorageUtility(
            endpoint="localhost:9000",
            access_key="a",
            secret_key="b",
            ensure_bucket_on_startup=False,
        )

        with self.assertRaises(StorageUnavailableError):
            storage.list_keys()

    @patch("src.minio.media_storage_utility.Minio")
    def test_public_url_returns_expected_url(self, mock_minio):
        mock_minio.return_value = MagicMock()

        storage = MediaStorageUtility(
            endpoint="localhost:9000",
            access_key="a",
            secret_key="b",
            public_base_url="http://localhost:9000/",
            ensure_bucket_on_startup=False,
        )

        result = storage.public_url("images/a.png")

        self.assertEqual(result, "http://localhost:9000/media/images/a.png")

    @patch("src.minio.media_storage_utility.Minio")
    def test_public_url_raises_when_public_base_url_not_configured(self, mock_minio):
        mock_minio.return_value = MagicMock()

        storage = MediaStorageUtility(
            endpoint="localhost:9000",
            access_key="a",
            secret_key="b",
            public_base_url=None,
            ensure_bucket_on_startup=False,
        )

        with self.assertRaises(StorageUnavailableError):
            storage.public_url("images/a.png")


if __name__ == "__main__":
    unittest.main()