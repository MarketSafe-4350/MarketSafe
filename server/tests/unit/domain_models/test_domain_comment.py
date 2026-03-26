from datetime import datetime
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

from src.domain_models import Comment
from src.utils import ValidationError, UnapprovedBehaviorError


class TestComment(unittest.TestCase):

    # ==============================
    # properties, mutators, repr
    # ==============================

    def test_properties_mutators_and_repr(self):
        created = datetime(2026, 1, 1, 12, 0, 0)
        comment = Comment(
            listing_id=5, author_id=7, body=" hello ", created_date=created
        )

        self.assertIsNone(comment.id)
        self.assertEqual(comment.listing_id, 5)
        self.assertEqual(comment.author_id, 7)
        self.assertEqual(comment.body, "hello")
        self.assertEqual(comment.created_date, created)

        comment.listing_id = 6
        comment.author_id = 8
        comment.body = None
        self.assertEqual(comment.listing_id, 6)
        self.assertEqual(comment.author_id, 8)
        self.assertIsNone(comment.body)

        comment.mark_persisted(33)
        self.assertEqual(comment.id, 33)

        rep = repr(comment)
        self.assertIn("Comment(id=33", rep)

    # ==============================
    # mark_persisted
    # ==============================

    def test_mark_persisted_raises_when_none(self):
        comment = Comment(listing_id=1, author_id=2)
        with self.assertRaises(ValidationError):
            comment.mark_persisted(None)

    def test_mark_persisted_raises_when_already_assigned(self):
        comment = Comment(listing_id=1, author_id=2)
        comment.mark_persisted(9)
        with self.assertRaises(UnapprovedBehaviorError):
            comment.mark_persisted(10)
