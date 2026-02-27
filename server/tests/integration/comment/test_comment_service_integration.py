from __future__ import annotations

import os
import unittest

from src.business_logic.services.comment_service import (
    CommentService,
    CommentWithAuthor,
)
from src.business_logic.managers.comment.comment_manager import CommentManager
from src.business_logic.managers.listing.listing_manager import ListingManager
from src.business_logic.managers.account.account_manager import AccountManager

from src.db.comment.mysql.mysql_comment_db import MySQLCommentDB
from src.db.listing.mysql.mysql_listing_db import MySQLListingDB
from src.db.account.mysql.mysql_account_db import MySQLAccountDB

from src.domain_models.account import Account
from src.domain_models.comment import Comment
from src.domain_models.listing import Listing

from tests.helpers.integration_db import ensure_tables_exist, reset_all_tables
from tests.helpers.integration_db_session import acquire, get_db, release


class TestCommentServiceIntegration(unittest.TestCase):
    """
    Integration tests:
      CommentService -> CommentManager -> MySQLCommentDB -> real MySQL (docker)

    Also uses real:
      AccountManager -> MySQLAccountDB
      ListingManager -> MySQLListingDB
    """

    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("SECRET_KEY", "test-secret")

        cls._session = acquire(timeout_s=120)
        cls._db = get_db()

        ensure_tables_exist(cls._db, timeout_s=60)
        reset_all_tables(cls._db)

        cls._account_db = MySQLAccountDB(db=cls._db)
        cls._listing_db = MySQLListingDB(db=cls._db)
        cls._comment_db = MySQLCommentDB(db=cls._db)

        cls._account_manager = AccountManager(account_db=cls._account_db)
        cls._listing_manager = ListingManager(
            listing_db=cls._listing_db,
            comment_db=cls._comment_db,
        )
        cls._comment_manager = CommentManager(comment_db=cls._comment_db)

        cls._service = CommentService(
            comment_manager=cls._comment_manager,
            listing_manager=cls._listing_manager,
            account_manager=cls._account_manager,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        release(cls._session, remove_volumes=False)

    def setUp(self) -> None:
        reset_all_tables(self._db)

    # -----------------------------
    # helpers
    # -----------------------------
    def _create_account(self, email: str, verified: bool = True) -> int:
        created = self._account_db.add(
            Account(
                email=email,
                password="Password1",
                fname="Test",
                lname="User",
                verified=verified,
            )
        )
        return created.id

    def _create_listing(self, seller_id: int) -> int:
        listing: Listing = Listing(
            seller_id=seller_id,
            title="Bike",
            description="Good condition",
            price=50.0,
            location="Winnipeg",
            image_url=None,
        )
        created: Listing = self._listing_manager.create_listing(listing)
        return created.id

    # -----------------------------
    # get_all_comments_listing
    # -----------------------------
    def test_get_all_comments_listing_empty_returns_empty_list(self) -> None:
        listing_id = 9999
        result = self._service.get_all_comments_listing(listing_id=listing_id)

        self.assertIsInstance(result, list)
        self.assertEqual(result, [])

    def test_get_all_comments_listing_returns_wrapped_comments_with_authors(
        self,
    ) -> None:
        seller_id = self._create_account("seller@umanitoba.ca", verified=True)
        listing_id = self._create_listing(seller_id=seller_id)

        author1_id = self._create_account("a1@umanitoba.ca", verified=True)
        author2_id = self._create_account("a2@umanitoba.ca", verified=True)

        c1 = Comment(listing_id=listing_id, author_id=author1_id, body="hi")
        c2 = Comment(listing_id=listing_id, author_id=author2_id, body="yo")

        self._service.create_comment(
            actor_id=author1_id, listing_id=listing_id, comment=c1
        )
        self._service.create_comment(
            actor_id=author2_id, listing_id=listing_id, comment=c2
        )

        result = self._service.get_all_comments_listing(listing_id=listing_id)

        self.assertEqual(len(result), 2)
        self.assertTrue(all(isinstance(x, CommentWithAuthor) for x in result))

        # Validate each wrapper has both comment + author
        for item in result:
            self.assertIsNotNone(item.comment)
            self.assertIsNotNone(item.author)
            self.assertEqual(item.comment.author_id, item.author.id)

    # -----------------------------
    # create_comment
    # -----------------------------
    def test_create_comment_persists_and_returns_comment_with_author(self) -> None:
        seller_id = self._create_account("seller2@umanitoba.ca", verified=True)
        listing_id = self._create_listing(seller_id=seller_id)

        actor_id = self._create_account("commenter@umanitoba.ca", verified=True)

        new_comment = Comment(
            listing_id=listing_id,
            author_id=actor_id,
            body="Is this available?",
        )

        created = self._service.create_comment(
            actor_id=actor_id,
            listing_id=listing_id,
            comment=new_comment,
        )

        self.assertIsInstance(created, CommentWithAuthor)
        self.assertIsNotNone(created.comment.id)
        self.assertEqual(created.comment.listing_id, listing_id)
        self.assertEqual(created.comment.author_id, actor_id)
        self.assertEqual(created.comment.body, "Is this available?")

        # author should be the actor
        self.assertIsNotNone(created.author)
        self.assertEqual(created.author.id, actor_id)

        # And it should be visible when listing comments
        fetched = self._service.get_all_comments_listing(listing_id=listing_id)
        self.assertEqual(len(fetched), 1)
        self.assertEqual(fetched[0].comment.body, "Is this available?")
        self.assertEqual(fetched[0].author.id, actor_id)
