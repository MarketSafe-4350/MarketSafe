from __future__ import annotations

import unittest
from uuid import uuid4

from sqlalchemy import text

from src.db.account.mysql import MySQLAccountDB
from src.db.listing.mysql.mysql_listing_db import MySQLListingDB
from src.domain_models import Account, Listing
from src.utils import (
    DatabaseQueryError,
    ListingNotFoundError,
    ValidationError,
)

from tests.helpers.integration_db import ensure_tables_exist, reset_all_tables
from tests.helpers.integration_db_session import acquire, get_db, release


class TestMySQLListingDB(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._session = acquire(timeout_s=60)
        cls._db = get_db()

        cls._account_db = MySQLAccountDB(cls._db)
        cls._listing_db = MySQLListingDB(cls._db)

        ensure_tables_exist(cls._db, timeout_s=60)
        reset_all_tables(cls._db)

    @classmethod
    def tearDownClass(cls) -> None:
        release(cls._session, remove_volumes=False)

    # -----------------------------
    # helpers
    # -----------------------------
    def _new_account(self) -> Account:
        uniq = uuid4().hex[:10]
        return Account(
            email=f"seller_{uniq}@example.com",
            password="pass",
            fname="Seller",
            lname="User",
            verified=False,
        )

    def _create_seller(self) -> Account:
        seller = self._account_db.add(self._new_account())
        self.assertIsNotNone(seller.id)
        return seller

    def _new_listing(self, seller_id: int, *, title: str | None = None, price: float = 123.45) -> Listing:
        uniq = uuid4().hex[:10]
        return Listing(
            seller_id=seller_id,
            title=title or f"Title {uniq}",
            description=f"Desc {uniq}",
            price=price,
            image_url=None,
            location="Winnipeg",
            is_sold=False,
            sold_to_id=None,
        )

    # -----------------------------
    # CREATE
    # -----------------------------
    def test_add_inserts_and_returns_id(self) -> None:
        seller = self._create_seller()
        listing = self._new_listing(seller.id)

        created = self._listing_db.add(listing)

        self.assertIsNotNone(created.id)
        self.assertEqual(created.seller_id, seller.id)
        self.assertEqual(created.title, listing.title)
        self.assertEqual(created.description, listing.description)
        self.assertEqual(float(created.price), float(listing.price))
        self.assertEqual(created.location, listing.location)
        self.assertEqual(bool(created.is_sold), False)
        self.assertIsNone(created.sold_to_id)

    def test_add_none_raises_validation(self) -> None:
        with self.assertRaises(ValidationError):
            self._listing_db.add(None)

    def test_add_fk_violation_raises_databasequeryerror(self) -> None:
        # seller_id doesn't exist -> FK violation -> IntegrityError -> DatabaseQueryError
        listing = self._new_listing(seller_id=999999999)

        with self.assertRaises(DatabaseQueryError):
            self._listing_db.add(listing)

    # -----------------------------
    # READ
    # -----------------------------
    def test_get_by_id_returns_listing_when_exists(self) -> None:
        seller = self._create_seller()
        created = self._listing_db.add(self._new_listing(seller.id))

        fetched = self._listing_db.get_by_id(created.id)
        self.assertIsNotNone(fetched)
        assert fetched is not None
        self.assertEqual(fetched.id, created.id)
        self.assertEqual(fetched.seller_id, seller.id)

    def test_get_by_id_returns_none_when_missing(self) -> None:
        self.assertIsNone(self._listing_db.get_by_id(999999999))

    def test_get_by_id_invalid_id_raises_validation(self) -> None:
        with self.assertRaises(ValidationError):
            # type: ignore[arg-type]
            self._listing_db.get_by_id("bad")

    def test_get_all_returns_list(self) -> None:
        reset_all_tables(self._db)

        self.assertEqual(self._listing_db.get_all(), [])

        seller = self._create_seller()
        a = self._listing_db.add(self._new_listing(seller.id, title="A"))
        b = self._listing_db.add(self._new_listing(seller.id, title="B"))

        rows = self._listing_db.get_all()
        self.assertGreaterEqual(len(rows), 2)

        ids = [x.id for x in rows]
        self.assertIn(a.id, ids)
        self.assertIn(b.id, ids)

    def test_get_by_seller_id(self) -> None:
        reset_all_tables(self._db)

        seller1 = self._create_seller()
        seller2 = self._create_seller()

        l1 = self._listing_db.add(self._new_listing(seller1.id))
        l2 = self._listing_db.add(self._new_listing(seller1.id))
        _ = self._listing_db.add(self._new_listing(seller2.id))

        seller1_rows = self._listing_db.get_by_seller_id(seller1.id)
        self.assertEqual({x.id for x in seller1_rows}, {l1.id, l2.id})

    def test_get_by_buyer_id(self) -> None:
        reset_all_tables(self._db)

        seller = self._create_seller()
        buyer = self._account_db.add(Account(
            email=f"buyer_{uuid4().hex[:10]}@example.com",
            password="pass",
            fname="Buyer",
            lname="User",
            verified=False,
        ))

        # Create listing then mark sold to buyer
        created = self._listing_db.add(self._new_listing(seller.id))
        self._listing_db.set_sold(created.id, True, buyer.id)

        buyer_rows = self._listing_db.get_by_buyer_id(buyer.id)
        self.assertEqual([x.id for x in buyer_rows], [created.id])

    def test_get_unsold(self) -> None:
        reset_all_tables(self._db)

        seller = self._create_seller()
        buyer = self._account_db.add(Account(
            email=f"buyer_{uuid4().hex[:10]}@example.com",
            password="pass",
            fname="Buyer",
            lname="User",
            verified=False,
        ))

        unsold = self._listing_db.add(self._new_listing(seller.id, title="unsold"))
        sold = self._listing_db.add(self._new_listing(seller.id, title="sold"))

        self._listing_db.set_sold(sold.id, True, buyer.id)

        rows = self._listing_db.get_unsold()
        ids = {x.id for x in rows}
        self.assertIn(unsold.id, ids)
        self.assertNotIn(sold.id, ids)

    # -----------------------------
    # SAFER / PARAMETERIZED READS
    # -----------------------------
    def test_get_unsold_by_location(self) -> None:
        reset_all_tables(self._db)
        seller = self._create_seller()

        wpg = self._new_listing(seller.id)
        wpg.location = "Winnipeg"
        created = self._listing_db.add(wpg)

        rows = self._listing_db.get_unsold_by_location("Winni")
        self.assertIn(created.id, {x.id for x in rows})

    def test_get_unsold_by_max_price(self) -> None:
        reset_all_tables(self._db)
        seller = self._create_seller()

        cheap = self._listing_db.add(self._new_listing(seller.id, price=10.0))
        _ = self._listing_db.add(self._new_listing(seller.id, price=999.0))

        rows = self._listing_db.get_unsold_by_max_price(50.0)
        self.assertIn(cheap.id, {x.id for x in rows})

    def test_get_unsold_by_location_and_max_price(self) -> None:
        reset_all_tables(self._db)
        seller = self._create_seller()

        good = self._new_listing(seller.id, price=25.0)
        good.location = "Brandon"
        good_created = self._listing_db.add(good)

        bad = self._new_listing(seller.id, price=250.0)
        bad.location = "Brandon"
        _ = self._listing_db.add(bad)

        rows = self._listing_db.get_unsold_by_location_and_max_price("Bran", 100.0)
        self.assertIn(good_created.id, {x.id for x in rows})

    def test_get_recent_unsold_paging(self) -> None:
        reset_all_tables(self._db)
        seller = self._create_seller()

        for _ in range(5):
            self._listing_db.add(self._new_listing(seller.id))

        page1 = self._listing_db.get_recent_unsold(limit=2, offset=0)
        page2 = self._listing_db.get_recent_unsold(limit=2, offset=2)

        self.assertEqual(len(page1), 2)
        self.assertEqual(len(page2), 2)
        self.assertNotEqual({x.id for x in page1}, {x.id for x in page2})

    def test_find_unsold_by_title_keyword(self) -> None:
        reset_all_tables(self._db)
        seller = self._create_seller()

        target = self._listing_db.add(self._new_listing(seller.id, title="Gaming Laptop"))
        _ = self._listing_db.add(self._new_listing(seller.id, title="Kitchen Table"))

        rows = self._listing_db.find_unsold_by_title_keyword("Laptop", limit=50, offset=0)
        self.assertIn(target.id, {x.id for x in rows})

    # -----------------------------
    # UPDATE
    # -----------------------------
    def test_update_updates_fields_and_rereads(self) -> None:
        seller = self._create_seller()
        created = self._listing_db.add(self._new_listing(seller.id))

        created.title = "Updated Title"
        created.description = "Updated Desc"
        created.price = 777.0
        created.location = "Thompson"

        updated = self._listing_db.update(created)
        self.assertEqual(updated.id, created.id)
        self.assertEqual(updated.title, "Updated Title")
        self.assertEqual(updated.description, "Updated Desc")
        self.assertEqual(float(updated.price), 777.0)
        self.assertEqual(updated.location, "Thompson")

    def test_update_missing_raises_listingnotfound(self) -> None:
        seller = self._create_seller()
        listing = self._new_listing(seller.id)
        listing.mark_persisted(999999999)  # fake id not in DB

        with self.assertRaises(ListingNotFoundError):
            self._listing_db.update(listing)

    def test_set_sold_missing_raises_listingnotfound(self) -> None:
        with self.assertRaises(ListingNotFoundError):
            self._listing_db.set_sold(999999999, True, 1)

    def test_set_price_missing_raises_listingnotfound(self) -> None:
        with self.assertRaises(ListingNotFoundError):
            self._listing_db.set_price(999999999, 10.0)

    # -----------------------------
    # DELETE
    # -----------------------------
    def test_remove_returns_true_when_deleted_and_false_when_missing(self) -> None:
        seller = self._create_seller()
        created = self._listing_db.add(self._new_listing(seller.id))

        deleted = self._listing_db.remove(created.id)
        self.assertTrue(deleted)

        deleted_again = self._listing_db.remove(created.id)
        self.assertFalse(deleted_again)

    # -----------------------------
    # QUERY ERROR SURFACE TEST (optional)
    # -----------------------------
    def test_query_error_is_wrapped_as_databasequeryerror(self) -> None:
        """
        Optional: verify SQLAlchemyError is mapped to DatabaseQueryError.
        We force a query failure by renaming the listing table temporarily.
        """
        with self._db.transaction() as conn:
            conn.execute(text("RENAME TABLE listing TO listing__tmp_test"))

        try:
            with self.assertRaises(DatabaseQueryError):
                self._listing_db.get_all()
        finally:
            with self._db.transaction() as conn:
                conn.execute(text("RENAME TABLE listing__tmp_test TO listing"))