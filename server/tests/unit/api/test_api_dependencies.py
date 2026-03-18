from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

import src.api.dependencies as deps


class TestAPIDependencies(unittest.TestCase):

    def setUp(self) -> None:
        self.db = MagicMock(name="db")
        self.account_db = MagicMock(name="account_db")
        self.listing_db = MagicMock(name="listing_db")
        self.comment_db = MagicMock(name="comment_db")
        self.offer_db = MagicMock(name="offer_db") 
        self.token_db = MagicMock(name="token_db")

        self.account_manager = MagicMock(name="account_manager")
        self.comment_manager = MagicMock(name="comment_manager")
        self.listing_manager = MagicMock(name="listing_manager")
        self.offer_manager = MagicMock(name="offer_manager")  

    def test_get_db(self):
        with patch.object(deps.DBUtility, "instance", return_value=self.db) as mock_instance:
            result = deps.get_db()

        mock_instance.assert_called_once()
        self.assertIs(result, self.db)

    def test_get_account_db(self):
        with patch.object(deps, "MySQLAccountDB", return_value=self.account_db) as ctor:
            result = deps.get_account_db(db=self.db)

        ctor.assert_called_once_with(db=self.db)
        self.assertIs(result, self.account_db)

    def test_get_listing_db(self):
        with patch.object(deps, "MySQLListingDB", return_value=self.listing_db) as ctor:
            result = deps.get_listing_db(db=self.db)

        ctor.assert_called_once_with(db=self.db)
        self.assertIs(result, self.listing_db)

    def test_get_comment_db(self):
        with patch.object(deps, "MySQLCommentDB", return_value=self.comment_db) as ctor:
            result = deps.get_comment_db(db=self.db)

        ctor.assert_called_once_with(db=self.db)
        self.assertIs(result, self.comment_db)

    def test_get_email_token_db(self):
        with patch.object(deps, "MySQLEmailVerificationTokenDB", return_value=self.token_db) as ctor:
            result = deps.get_email_token_db(db=self.db)

        ctor.assert_called_once_with(db=self.db)
        self.assertIs(result, self.token_db)

    def test_get_offer_db(self):
        with patch.object(deps, "MySQLOfferDB", return_value=self.offer_db) as ctor:
            result = deps.get_offer_db(db=self.db)

        ctor.assert_called_once_with(db=self.db)
        self.assertIs(result, self.offer_db)

    def test_get_account_manager(self):
        with patch.object(deps, "AccountManager", return_value=self.account_manager) as ctor:
            result = deps.get_account_manager(account_db=self.account_db)

        ctor.assert_called_once_with(account_db=self.account_db)
        self.assertIs(result, self.account_manager)

    def test_get_comment_manager(self):
        with patch.object(deps, "CommentManager", return_value=self.comment_manager) as ctor:
            result = deps.get_comment_manager(comment_db=self.comment_db)

        ctor.assert_called_once_with(comment_db=self.comment_db)
        self.assertIs(result, self.comment_manager)

    def test_get_listing_manager(self):
        with patch.object(deps, "ListingManager", return_value=self.listing_manager) as ctor:
            result = deps.get_listing_manager(
                listing_db=self.listing_db,
                comment_db=self.comment_db
            )

        ctor.assert_called_once_with(
            listing_db=self.listing_db,
            comment_db=self.comment_db
        )
        self.assertIs(result, self.listing_manager)

    def test_get_offer_manager(self):
        with patch.object(deps, "OfferManager", return_value=self.offer_manager) as ctor:
            result = deps.get_offer_manager(
                offer_db=self.offer_db,
                listing_db=self.listing_db,
            )

        ctor.assert_called_once_with(
            offer_db=self.offer_db,
            listing_db=self.listing_db,
        )
        self.assertIs(result, self.offer_manager)

    def test_get_account_service(self):
        service = MagicMock()

        with patch.object(deps, "AccountService", return_value=service) as ctor:
            result = deps.get_account_service(
                account_manager=self.account_manager,
                token_db=self.token_db
            )

        ctor.assert_called_once_with(
            account_manager=self.account_manager,
            token_db=self.token_db
        )
        self.assertIs(result, service)

    def test_get_comment_service(self):
        service = MagicMock()

        with patch.object(deps, "CommentService", return_value=service) as ctor:
            result = deps.get_comment_service(
                comment_manager=self.comment_manager,
                listing_manager=self.listing_manager,
                account_manager=self.account_manager,
            )

        ctor.assert_called_once_with(
            comment_manager=self.comment_manager,
            listing_manager=self.listing_manager,
            account_manager=self.account_manager,
        )
        self.assertIs(result, service)

    def test_get_listing_service(self):
        service = MagicMock()

        with patch.object(deps, "ListingService", return_value=service) as ctor:
            result = deps.get_listing_service(listing_manager=self.listing_manager)

        ctor.assert_called_once_with(listing_manager=self.listing_manager)
        self.assertIs(result, service)

    def test_get_offer_service(self):
        service = MagicMock()

        with patch.object(deps, "OfferService", return_value=service) as ctor:
            result = deps.get_offer_service(
                offer_manager=self.offer_manager,
                listing_manager=self.listing_manager,
                account_manager=self.account_manager,
            )

        ctor.assert_called_once_with(
            offer_manager=self.offer_manager,
            listing_manager=self.listing_manager,
            account_manager=self.account_manager,
        )
        self.assertIs(result, service)


if __name__ == "__main__":
    unittest.main()