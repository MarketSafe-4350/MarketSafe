from datetime import datetime, timedelta
import os
from pathlib import Path
import sys
import types
import unittest

sys.modules.setdefault(
    "dotenv", types.SimpleNamespace(load_dotenv=lambda *args, **kwargs: None)
)
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
os.environ.setdefault("SECRET_KEY", "test-secret-key")

from src.domain_models import VerificationToken
from src.utils import ValidationError


class TestVerificationToken(unittest.TestCase):

    # ==============================
    # properties, repr, mark_persisted, mark_as_used
    # ==============================

    def test_properties_repr_mark_persisted_and_mark_as_used(self):
        now = datetime.now()
        token = VerificationToken(
            account_id=1,
            token_hash="hash",
            expires_at=now + timedelta(minutes=5),
            token_id=None,
            used=False,
            used_at=None,
        )

        self.assertIsNone(token.id)
        self.assertEqual(token.account_id, 1)
        self.assertEqual(token.token_hash, "hash")
        self.assertIsNotNone(token.expires_at)
        self.assertIsNotNone(token.created_at)
        self.assertFalse(token.used)
        self.assertIsNone(token.used_at)

        token.mark_persisted(12)
        self.assertEqual(token.id, 12)

        token.mark_as_used()
        self.assertTrue(token.used)
        self.assertIsNotNone(token.used_at)

        rep = repr(token)
        self.assertIn("VerificationToken(id=12", rep)

    # ==============================
    # mark_persisted
    # ==============================

    def test_mark_persisted_raises_when_none(self):
        token = VerificationToken(
            account_id=1,
            token_hash="hash",
            expires_at=datetime.now() + timedelta(minutes=5),
        )
        with self.assertRaises(ValidationError):
            token.mark_persisted(None)

    def test_mark_persisted_raises_when_already_assigned(self):
        token = VerificationToken(
            account_id=1,
            token_hash="hash",
            expires_at=datetime.now() + timedelta(minutes=5),
        )
        token.mark_persisted(1)
        with self.assertRaises(ValidationError):
            token.mark_persisted(2)

    # ==============================
    # mark_as_used
    # ==============================

    def test_mark_as_used_raises_when_already_used(self):
        token = VerificationToken(
            account_id=1,
            token_hash="hash",
            expires_at=datetime.now() + timedelta(minutes=5),
            used=True,
        )
        with self.assertRaises(ValidationError):
            token.mark_as_used()

    # ==============================
    # is_expired / is_valid
    # ==============================

    def test_is_expired_and_is_valid_when_expired(self):
        token = VerificationToken(
            account_id=1,
            token_hash="hash",
            expires_at=datetime.now() - timedelta(seconds=1),
        )
        self.assertTrue(token.is_expired())
        self.assertFalse(token.is_valid())

    def test_is_expired_and_is_valid_when_active(self):
        token = VerificationToken(
            account_id=1,
            token_hash="hash",
            expires_at=datetime.now() + timedelta(minutes=1),
            used=False,
        )
        self.assertFalse(token.is_expired())
        self.assertTrue(token.is_valid())

    def test_is_valid_false_when_used(self):
        token = VerificationToken(
            account_id=1,
            token_hash="hash",
            expires_at=datetime.now() + timedelta(minutes=1),
            used=True,
        )
        self.assertFalse(token.is_valid())
