from __future__ import annotations

import unittest
from uuid import uuid4

from sqlalchemy import text

from src.db.account.mysql import MySQLAccountDB
from src.db.listing.mysql.mysql_listing_db import MySQLListingDB
from src.db.comment.mysql.mysql_comment_db import MySQLCommentDB

from src.domain_models import Account, Listing, Comment

from src.utils import (
    DatabaseQueryError,
    ValidationError,
    CommentNotFoundError, 
)

from tests.helpers.integration_db import ensure_tables_exist, reset_all_tables
from tests.helpers.integration_db_session import acquire, get_db, release


class TestMySQLCommentDB(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._session = acquire(timeout_s=60)
        cls._db = get_db()

        ensure_tables_exist(cls._db, timeout_s=60)
        reset_all_tables(cls._db)

        cls._account_db = MySQLAccountDB(cls._db)
        cls._listing_db = MySQLListingDB(cls._db)
        cls._comment_db = MySQLCommentDB(cls._db)

    @classmethod
    def tearDownClass(cls) -> None:
        release(cls._session, remove_volumes=False)

    # -----------------------------
    # helpers
    # -----------------------------
    def _new_account(self, *, prefix: str = "user") -> Account:
        uniq = uuid4().hex[:10]
        return Account(
            email=f"{prefix}_{uniq}@example.com",
            password="pass",
            fname="F",
            lname="L",
            verified=False,
        )

    def _create_account(self, *, prefix: str = "user") -> Account:
        account = self._account_db.add(self._new_account(prefix=prefix))
        self.assertIsNotNone(account.id)
        return account

    def _new_listing(self, seller_id: int, *, title: str | None = None) -> Listing:
        uniq = uuid4().hex[:10]
        return Listing(
            seller_id=seller_id,
            title=title or f"Title {uniq}",
            description=f"Desc {uniq}",
            price=10.0,
            image_url=None,
            location="Winnipeg",
            is_sold=False,
            sold_to_id=None,
        )

    def _create_listing(self, seller_id: int) -> Listing:
        created = self._listing_db.add(self._new_listing(seller_id))
        self.assertIsNotNone(created.id)
        return created

    def _new_comment(self, listing_id: int, author_id: int, *, body: str | None = "hello") -> Comment:
        return Comment(
            listing_id=listing_id,
            author_id=author_id,
            body=body,
            comment_id=None,
        )

    # -----------------------------
    # CREATE
    # -----------------------------
    def test_add_inserts_and_returns_id(self) -> None:
        reset_all_tables(self._db)

        seller = self._create_account(prefix="seller")
        listing = self._create_listing(seller.id)

        author = self._create_account(prefix="author")
        comment = self._new_comment(listing.id, author.id, body="first!")

        created = self._comment_db.add(comment)

        self.assertIsNotNone(created.id)
        self.assertEqual(created.listing_id, listing.id)
        self.assertEqual(created.author_id, author.id)
        self.assertEqual(created.body, "first!")

    def test_add_none_raises_validation(self) -> None:
        with self.assertRaises(ValidationError):
            self._comment_db.add(None)

    def test_add_fk_violation_listing_raises_databasequeryerror(self) -> None:
        reset_all_tables(self._db)

        author = self._create_account(prefix="author")
        # listing_id doesn't exist -> FK violation -> IntegrityError -> DatabaseQueryError
        comment = self._new_comment(listing_id=999999999, author_id=author.id, body="x")

        with self.assertRaises(DatabaseQueryError):
            self._comment_db.add(comment)

    def test_add_fk_violation_author_raises_databasequeryerror(self) -> None:
        reset_all_tables(self._db)

        seller = self._create_account(prefix="seller")
        listing = self._create_listing(seller.id)

        # author_id doesn't exist -> FK violation -> IntegrityError -> DatabaseQueryError
        comment = self._new_comment(listing_id=listing.id, author_id=999999999, body="x")

        with self.assertRaises(DatabaseQueryError):
            self._comment_db.add(comment)

    def test_add_generic_sqlalchemy_error_is_wrapped(self) -> None:
        """
        Force a generic SQLAlchemyError
        """
        seller = self._create_account(prefix="seller")
        listing = self._create_listing(seller.id)

        author = self._create_account(prefix="author")
        comment = self._new_comment(listing.id, author.id, body="first!")

        with self._db.transaction() as conn:
            conn.execute(text("RENAME TABLE comment TO comment__tmp_test"))

        try:
            with self.assertRaises(DatabaseQueryError):
                self._comment_db.add(comment)

        finally:
            with self._db.transaction() as conn:
                conn.execute(text("RENAME TABLE comment__tmp_test TO comment"))
                
    # -----------------------------
    # READ
    # -----------------------------
    def test_get_by_id_returns_comment_when_exists(self) -> None:
        reset_all_tables(self._db)

        seller = self._create_account(prefix="seller")
        listing = self._create_listing(seller.id)
        author = self._create_account(prefix="author")

        created = self._comment_db.add(self._new_comment(listing.id, author.id, body="hi"))

        fetched = self._comment_db.get_by_id(created.id)
        self.assertIsNotNone(fetched)
        assert fetched is not None

        self.assertEqual(fetched.id, created.id)
        self.assertEqual(fetched.listing_id, listing.id)
        self.assertEqual(fetched.author_id, author.id)
        self.assertEqual(fetched.body, "hi")

        # created_date should be populated when reading from DB
        self.assertIsNotNone(fetched.created_date)

    def test_get_by_id_returns_none_when_missing(self) -> None:
        self.assertIsNone(self._comment_db.get_by_id(999999999))

    def test_get_by_id_invalid_id_raises_validation(self) -> None:
        with self.assertRaises(ValidationError):
            self._comment_db.get_by_id("bad")

    def test_get_by_listing_id_returns_comments(self) -> None:
        reset_all_tables(self._db)

        seller = self._create_account(prefix="seller")
        listing1 = self._create_listing(seller.id)
        listing2 = self._create_listing(seller.id)

        author = self._create_account(prefix="author")

        c1 = self._comment_db.add(self._new_comment(listing1.id, author.id, body="a"))
        c2 = self._comment_db.add(self._new_comment(listing1.id, author.id, body="b"))
        _ = self._comment_db.add(self._new_comment(listing2.id, author.id, body="other"))

        rows = self._comment_db.get_by_listing_id(listing1.id)
        ids = {x.id for x in rows}
        self.assertEqual(ids, {c1.id, c2.id})

    def test_get_by_author_id_returns_comments(self) -> None:
        reset_all_tables(self._db)

        seller = self._create_account(prefix="seller")
        listing = self._create_listing(seller.id)

        author1 = self._create_account(prefix="author1")
        author2 = self._create_account(prefix="author2")

        a = self._comment_db.add(self._new_comment(listing.id, author1.id, body="a"))
        b = self._comment_db.add(self._new_comment(listing.id, author1.id, body="b"))
        _ = self._comment_db.add(self._new_comment(listing.id, author2.id, body="c"))

        rows = self._comment_db.get_by_author_id(author1.id)
        self.assertEqual({x.id for x in rows}, {a.id, b.id})

    # -----------------------------
    # UPDATE
    # -----------------------------
    def test_update_body_updates_field(self) -> None:
        reset_all_tables(self._db)

        seller = self._create_account(prefix="seller")
        listing = self._create_listing(seller.id)
        author = self._create_account(prefix="author")

        created = self._comment_db.add(self._new_comment(listing.id, author.id, body="old"))

        self._comment_db.update_body(created.id, "new")

        fetched = self._comment_db.get_by_id(created.id)
        self.assertIsNotNone(fetched)
        assert fetched is not None
        self.assertEqual(fetched.body, "new")

    def test_update_body_allows_null_body(self) -> None:
        reset_all_tables(self._db)

        seller = self._create_account(prefix="seller")
        listing = self._create_listing(seller.id)
        author = self._create_account(prefix="author")

        created = self._comment_db.add(self._new_comment(listing.id, author.id, body="old"))

        self._comment_db.update_body(created.id, None)

        fetched = self._comment_db.get_by_id(created.id)
        self.assertIsNotNone(fetched)
        assert fetched is not None
        self.assertIsNone(fetched.body)

    def test_update_body_missing_raises_notfound(self) -> None:
        with self.assertRaises(CommentNotFoundError):
            self._comment_db.update_body(999999999, "x")

    # -----------------------------
    # DELETE
    # -----------------------------
    def test_remove_returns_true_when_deleted_and_false_when_missing(self) -> None:
        reset_all_tables(self._db)

        seller = self._create_account(prefix="seller")
        listing = self._create_listing(seller.id)
        author = self._create_account(prefix="author")

        created = self._comment_db.add(self._new_comment(listing.id, author.id, body="bye"))

        deleted = self._comment_db.remove(created.id)
        self.assertTrue(deleted)

        deleted_again = self._comment_db.remove(created.id)
        self.assertFalse(deleted_again)
                
    def test_query_error_is_wrapped_as_databasequeryerror_for_all_methods(self) -> None:
        with self._db.transaction() as conn:
            conn.execute(text("RENAME TABLE comment TO comment__tmp_test"))

        try:
            with self.assertRaises(DatabaseQueryError):
                self._comment_db.get_by_id(1)

            with self.assertRaises(DatabaseQueryError):
                self._comment_db.get_by_listing_id(1)

            with self.assertRaises(DatabaseQueryError):
                self._comment_db.get_by_author_id(1)

            with self.assertRaises(DatabaseQueryError):
                self._comment_db.update_body(1, "x")

            with self.assertRaises(DatabaseQueryError):
                self._comment_db.remove(1)

        finally:
            with self._db.transaction() as conn:
                conn.execute(text("RENAME TABLE comment__tmp_test TO comment"))