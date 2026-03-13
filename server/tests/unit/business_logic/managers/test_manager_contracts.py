import unittest

from src.business_logic.managers.account import IAccountManager
from src.business_logic.managers.comment import ICommentManager
from src.business_logic.managers.listing import IListingManager


# -------------------------
# Dummy DB deps (minimal)
# -------------------------
class DummyAccountDB:
    pass


class DummyListingDB:
    pass


class DummyCommentDB:
    pass


# -------------------------
# Contract stubs
# -------------------------
class AccountManagerContractStub(IAccountManager):
    """Minimal implementation used to validate the IAccountManager contract."""

    def create_account(self, account):
        return super().create_account(account)

    def get_account_by_id(self, account_id):
        return super().get_account_by_id(account_id)

    def get_account_by_email(self, email):
        return super().get_account_by_email(email)

    def list_accounts(self):
        return super().list_accounts()

    def set_verified(self, account_id, verified):
        return super().set_verified(account_id, verified)

    def delete_account(self, account_id):
        return super().delete_account(account_id)

    def set_verified_by_email(self, email, verified):
        return super().set_verified_by_email(email, verified)

    def get_account_with_listings(self, account_id):
        return super().get_account_with_listings(account_id)

    def get_account_with_listings_by_email(self, email):
        return super().get_account_with_listings_by_email(email)

    def get_account_with_listings_for(self, account):
        return super().get_account_with_listings_for(account)

    def fill_account_rating_values(self, account):
        return super().fill_account_rating_values(account)

    def get_account_with_rating_values_by_id(self, account_id):
        return super().get_account_with_rating_values_by_id(account_id)

    def get_account_with_rating_values_by_email(self, email):
        return super().get_account_with_rating_values_by_email(email)


class CommentManagerContractStub(ICommentManager):
    """Minimal implementation used to validate the ICommentManager contract."""

    def create_comment(self, actor, listing, comment):
        return super().create_comment(actor, listing, comment)

    def get_comment_by_id(self, comment_id):
        return super().get_comment_by_id(comment_id)

    def list_comments_for_listing(self, listing_id):
        return super().list_comments_for_listing(listing_id)

    def list_comments_for_author(self, author_id):
        return super().list_comments_for_author(author_id)

    def update_comment_body(self, actor, comment):
        return super().update_comment_body(actor, comment)

    def delete_comment(self, actor, comment_id):
        return super().delete_comment(actor, comment_id)


class ListingManagerContractStub(IListingManager):
    """Minimal implementation used to validate the IListingManager contract."""

    def create_listing(self, listing):
        return super().create_listing(listing)

    def get_listing_by_id(self, listing_id):
        return super().get_listing_by_id(listing_id)

    def list_listings(self):
        return super().list_listings()

    def list_unsold_listings(self):
        return super().list_unsold_listings()

    def list_recent_unsold(self, limit=50, offset=0):
        return super().list_recent_unsold(limit, offset)

    def list_unsold_by_location(self, location):
        return super().list_unsold_by_location(location)

    def list_unsold_by_max_price(self, max_price):
        return super().list_unsold_by_max_price(max_price)

    def list_unsold_by_location_and_max_price(self, location, max_price):
        return super().list_unsold_by_location_and_max_price(location, max_price)

    def find_unsold_by_title_keyword(self, keyword, limit=50, offset=0):
        return super().find_unsold_by_title_keyword(keyword, limit, offset)

    def list_listings_by_seller(self, seller_id):
        return super().list_listings_by_seller(seller_id)

    def list_listings_by_buyer(self, buyer_id):
        return super().list_listings_by_buyer(buyer_id)

    def get_listing_with_comments(self, listing_id):
        return super().get_listing_with_comments(listing_id)

    def fill_listing_rating_value(self, listing):
        return super().fill_listing_rating_value(listing)

    def get_listing_with_rating_by_id(self, listing_id):
        return super().get_listing_with_rating_by_id(listing_id)

    def get_listing_with_comments_and_rating(self, listing_id):
        return super().get_listing_with_comments_and_rating(listing_id)

    def update_listing(self, listing):
        return super().update_listing(listing)

    def mark_listing_sold(self, actor, listing, buyer):
        return super().mark_listing_sold(actor, listing, buyer)

    def update_listing_price(self, listing_id, price):
        return super().update_listing_price(listing_id, price)

    def delete_listing(self, listing_id):
        return super().delete_listing(listing_id)


# -------------------------
# Contract tests (all three)
# -------------------------
class TestBusinessManagerContracts(unittest.TestCase):
    """Contract-level tests for abstract business-layer manager interfaces."""

    # -------------------------
    # IAccountManager
    # -------------------------
    def test_account_manager_requires_account_db(self):
        with self.assertRaises(Exception):
            AccountManagerContractStub(account_db=None)

    def test_account_manager_init_accepts_optional_listing_db(self):
        mgr = AccountManagerContractStub(
            account_db=DummyAccountDB(),
            listing_db=DummyListingDB(),
        )
        self.assertIsNotNone(mgr)

    def test_account_manager_default_methods_raise_not_implemented(self):
        mgr = AccountManagerContractStub(account_db=DummyAccountDB())

        with self.assertRaises(NotImplementedError):
            mgr.create_account(account=None)
        with self.assertRaises(NotImplementedError):
            mgr.get_account_by_id(1)
        with self.assertRaises(NotImplementedError):
            mgr.get_account_by_email("a@b.com")
        with self.assertRaises(NotImplementedError):
            mgr.list_accounts()
        with self.assertRaises(NotImplementedError):
            mgr.set_verified(1, True)
        with self.assertRaises(NotImplementedError):
            mgr.delete_account(1)
        with self.assertRaises(NotImplementedError):
            mgr.set_verified_by_email("a@b.com", True)
        with self.assertRaises(NotImplementedError):
            mgr.get_account_with_listings(1)

        with self.assertRaises(NotImplementedError):
            mgr.get_account_with_listings_by_email("a@b.com")
        with self.assertRaises(NotImplementedError):
            mgr.get_account_with_listings_for(account=None)
        with self.assertRaises(NotImplementedError):
            mgr.fill_account_rating_values(account=None)
        with self.assertRaises(NotImplementedError):
            mgr.get_account_with_rating_values_by_id(1)
        with self.assertRaises(NotImplementedError):
            mgr.get_account_with_rating_values_by_email("a@b.com")

    # -------------------------
    # ICommentManager
    # -------------------------
    def test_comment_manager_requires_comment_db(self):
        with self.assertRaises(Exception):
            CommentManagerContractStub(comment_db=None)

    def test_comment_manager_default_methods_raise_not_implemented(self):
        mgr = CommentManagerContractStub(comment_db=DummyCommentDB())

        with self.assertRaises(NotImplementedError):
            mgr.create_comment(actor=None, listing=None, comment=None)
        with self.assertRaises(NotImplementedError):
            mgr.get_comment_by_id(1)
        with self.assertRaises(NotImplementedError):
            mgr.list_comments_for_listing(1)
        with self.assertRaises(NotImplementedError):
            mgr.list_comments_for_author(1)
        with self.assertRaises(NotImplementedError):
            mgr.update_comment_body(actor=None, comment=None)
        with self.assertRaises(NotImplementedError):
            mgr.delete_comment(actor=None, comment_id=1)

    # -------------------------
    # IListingManager
    # -------------------------
    def test_listing_manager_requires_listing_db_and_comment_db(self):
        with self.assertRaises(Exception):
            ListingManagerContractStub(listing_db=None, comment_db=DummyCommentDB())
        with self.assertRaises(Exception):
            ListingManagerContractStub(listing_db=DummyListingDB(), comment_db=None)

    def test_listing_manager_default_methods_raise_not_implemented(self):
        mgr = ListingManagerContractStub(
            listing_db=DummyListingDB(),
            comment_db=DummyCommentDB(),
        )

        with self.assertRaises(NotImplementedError):
            mgr.create_listing(listing=None)
        with self.assertRaises(NotImplementedError):
            mgr.get_listing_by_id(1)
        with self.assertRaises(NotImplementedError):
            mgr.list_listings()
        with self.assertRaises(NotImplementedError):
            mgr.list_unsold_listings()
        with self.assertRaises(NotImplementedError):
            mgr.list_recent_unsold(limit=10, offset=0)
        with self.assertRaises(NotImplementedError):
            mgr.list_unsold_by_location("Winnipeg")
        with self.assertRaises(NotImplementedError):
            mgr.list_unsold_by_max_price(100.0)
        with self.assertRaises(NotImplementedError):
            mgr.list_unsold_by_location_and_max_price("Winnipeg", 100.0)
        with self.assertRaises(NotImplementedError):
            mgr.find_unsold_by_title_keyword("bike", limit=10, offset=0)
        with self.assertRaises(NotImplementedError):
            mgr.list_listings_by_seller(1)
        with self.assertRaises(NotImplementedError):
            mgr.list_listings_by_buyer(1)
        with self.assertRaises(NotImplementedError):
            mgr.get_listing_with_comments(1)
        with self.assertRaises(NotImplementedError):
            mgr.update_listing(listing=None)
        with self.assertRaises(NotImplementedError):
            mgr.mark_listing_sold(actor=None, listing=None, buyer=None)
        with self.assertRaises(NotImplementedError):
            mgr.update_listing_price(listing_id=1, price=99.99)
        with self.assertRaises(NotImplementedError):
            mgr.delete_listing(1)

        with self.assertRaises(NotImplementedError):
            mgr.fill_listing_rating_value(listing=None)
        with self.assertRaises(NotImplementedError):
            mgr.get_listing_with_rating_by_id(1)
        with self.assertRaises(NotImplementedError):
            mgr.get_listing_with_comments_and_rating(1)

    def test_account_manager_rating_and_listing_extension_methods_raise_not_implemented(self):
        mgr = AccountManagerContractStub(account_db=DummyAccountDB())

        with self.assertRaises(NotImplementedError):
            mgr.get_account_with_listings_by_email("a@b.com")
        with self.assertRaises(NotImplementedError):
            mgr.get_account_with_listings_for(account=None)
        with self.assertRaises(NotImplementedError):
            mgr.fill_account_rating_values(account=None)
        with self.assertRaises(NotImplementedError):
            mgr.get_account_with_rating_values_by_id(1)
        with self.assertRaises(NotImplementedError):
            mgr.get_account_with_rating_values_by_email("a@b.com")

    def test_listing_manager_rating_extension_methods_raise_not_implemented(self):
        mgr = ListingManagerContractStub(
            listing_db=DummyListingDB(),
            comment_db=DummyCommentDB(),
        )

        with self.assertRaises(NotImplementedError):
            mgr.fill_listing_rating_value(listing=None)
        with self.assertRaises(NotImplementedError):
            mgr.get_listing_with_rating_by_id(1)
        with self.assertRaises(NotImplementedError):
            mgr.get_listing_with_comments_and_rating(1)
