from __future__ import annotations

import unittest
import datetime

from src.db import CommentMapper
from src.domain_models import Comment


class TestCommentMapper(unittest.TestCase):
    def test_from_mapping_maps_all_fields_when_present(self) -> None:
        created = datetime.datetime(2026, 3, 4, 12, 0, 0)

        row = {
            "id": 10,
            "created_date": created,
            "body": "hello",
            "listing_id": 5,
            "author_id": 7,
        }

        out = CommentMapper.from_mapping(row)

        self.assertIsInstance(out, Comment)
        self.assertEqual(out.id, 10)
        self.assertEqual(out.listing_id, 5)
        self.assertEqual(out.author_id, 7)
        self.assertEqual(out.body, "hello")
        self.assertEqual(out.created_date, created)

    def test_from_mapping_sets_body_none_when_null(self) -> None:
        row = {
            "id": 1,
            "created_date": None,
            "body": None,
            "listing_id": 2,
            "author_id": 3,
        }

        out = CommentMapper.from_mapping(row)

        self.assertEqual(out.id, 1)
        self.assertEqual(out.body, None)

    def test_from_mapping_sets_id_none_when_missing_id_value(self) -> None:
        row = {
            "id": None,
            "created_date": None,
            "body": "x",
            "listing_id": 2,
            "author_id": 3,
        }

        out = CommentMapper.from_mapping(row)

        self.assertIsNone(out.id)
        self.assertEqual(out.body, "x")

    def test_from_mapping_casts_types_to_int_and_str(self) -> None:
        row = {
            "id": "9",
            "created_date": None,
            "body": 12345,
            "listing_id": "100",
            "author_id": "200",
        }

        out = CommentMapper.from_mapping(row)

        self.assertEqual(out.id, 9)
        self.assertEqual(out.listing_id, 100)
        self.assertEqual(out.author_id, 200)
        self.assertEqual(out.body, "12345")


if __name__ == "__main__":
    unittest.main(verbosity=2)
