import os
import unittest

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.api.routes import offer_routes
from src.api.dependencies import get_offer_service, get_listing_service
from src.auth.dependencies import get_current_user_id

from src.api.errors.exception_handlers import (
    AppError,
    app_error_handler,
    request_validation_error_handler,
)
from fastapi.exceptions import RequestValidationError

from tests.helpers.integration_db import ensure_tables_exist, reset_all_tables
from tests.helpers.integration_db_session import acquire, get_db, release

from src.db.account.mysql.mysql_account_db import MySQLAccountDB
from src.db.listing.mysql.mysql_listing_db import MySQLListingDB
from src.db.offer.mysql.mysql_offer_db import MySQLOfferDB
from src.db.comment.mysql.mysql_comment_db import MySQLCommentDB

from src.business_logic.managers.account.account_manager import AccountManager
from src.business_logic.managers.listing.listing_manager import ListingManager
from src.business_logic.managers.offer.offer_manager import OfferManager

from src.business_logic.services.listing_service import ListingService
from src.business_logic.services.offer_service import OfferService

from src.domain_models import Account, Listing, Offer


class TestOfferRouteIntegration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        os.environ.setdefault("SECRET_KEY", "test-secret")

        cls._session = acquire(timeout_s=120)
        cls._db = get_db()

        ensure_tables_exist(cls._db, timeout_s=60)
        reset_all_tables(cls._db)

        # DBs
        cls._account_db = MySQLAccountDB(db=cls._db)
        cls._listing_db = MySQLListingDB(db=cls._db)
        cls._offer_db = MySQLOfferDB(db=cls._db)
        cls._comment_db = MySQLCommentDB(db=cls._db)

        # Managers
        cls._account_manager = AccountManager(
            account_db=cls._account_db,
            listing_db=cls._listing_db,
        )

        cls._listing_manager = ListingManager(
            listing_db=cls._listing_db,
            comment_db=cls._comment_db,
        )

        cls._offer_manager = OfferManager(
            offer_db=cls._offer_db,
            listing_db=cls._listing_db,
        )

        # Services
        cls._listing_service = ListingService(listing_manager=cls._listing_manager)
        
        cls._offer_service = OfferService(
            offer_manager=cls._offer_manager,
            listing_manager=cls._listing_manager,
            account_manager=cls._account_manager,
        )
        # App
        cls.app = FastAPI()
        cls.app.include_router(offer_routes.router)

        cls.app.add_exception_handler(AppError, app_error_handler)
        cls.app.add_exception_handler(
            RequestValidationError, request_validation_error_handler
        )

        cls.app.dependency_overrides[get_offer_service] = lambda: cls._offer_service
        cls.app.dependency_overrides[get_listing_service] = lambda: cls._listing_service

        cls.client = TestClient(cls.app)

    @classmethod
    def tearDownClass(cls):
        cls.app.dependency_overrides.clear()
        release(cls._session, remove_volumes=False)

    def setUp(self):
        reset_all_tables(self._db)

        # Users
        self.user_id = self._create_account("buyer@test.com")
        self.other_user_id = self._create_account("seller@test.com")
        self.third_user_id = self._create_account("third@test.com")

        # default auth = buyer
        self.app.dependency_overrides[get_current_user_id] = lambda: self.user_id

        # Listing owned by seller
        self.listing_id = self._create_listing(self.other_user_id)

    def tearDown(self):
        self.app.dependency_overrides.pop(get_current_user_id, None)

    def _create_account(self, email):
        acc = self._account_db.add(
            Account(
                email=email,
                password="Password1",
                fname="Test",
                lname="User",
                verified=True,
            )
        )
        return acc.id

    def _create_listing(self, seller_id):
        listing = self._listing_manager.create_listing(
            Listing(
                seller_id=seller_id,
                title="Item",
                description="Desc",
                price=10.0,
                location="Winnipeg",
                image_url=None,
            )
        )
        return listing.id

    def _create_offer(self, listing_id, sender_id, price=5.0):
        offer = Offer(
            listing_id=listing_id,
            sender_id=sender_id,
            offered_price=price,
            location_offered="Here",
        )
        created = self._offer_service.create_offer(offer)
        return created.id


    def test_create_offer(self):
        resp = self.client.post(
            f"/listings/{self.listing_id}/offer",
            json={"offered_price": 12.5, "location_offered": "Campus"},
        )

        self.assertEqual(resp.status_code, 200)
        data = resp.json()

        self.assertEqual(data["listing_id"], self.listing_id)
        self.assertEqual(data["sender_id"], self.user_id)

    def test_get_offer_by_id(self):
        offer_id = self._create_offer(self.listing_id, self.user_id)

        resp = self.client.get(f"/offers/{offer_id}")
        self.assertEqual(resp.status_code, 200)

        self.assertEqual(resp.json()["id"], offer_id)

    def test_get_offers_by_listing(self):
        self._create_offer(self.listing_id, self.user_id)
        self._create_offer(self.listing_id, self.third_user_id) 

        resp = self.client.get(f"/listings/{self.listing_id}/offer")
        self.assertEqual(resp.status_code, 200)

        self.assertGreaterEqual(len(resp.json()), 2)

    def test_get_sent_and_received(self):
        self._create_offer(self.listing_id, self.user_id)

  
        resp = self.client.get("/accounts/offers/sent")
        self.assertEqual(resp.status_code, 200)

       
        self.app.dependency_overrides[get_current_user_id] = lambda: self.other_user_id

        resp = self.client.get("/accounts/offers/received")
        self.assertEqual(resp.status_code, 200)

    def test_pending_and_unseen(self):
        self._create_offer(self.listing_id, self.user_id)

        self.assertEqual(
            self.client.get("/accounts/offers/received/pending").status_code, 200
        )
        self.assertEqual(
            self.client.get("/accounts/offers/received/unseen").status_code, 200
        )
        self.assertEqual(
            self.client.get("/accounts/offers/sent/pending").status_code, 200
        )

    def test_mark_seen_resolve_delete(self):
        offer_id = self._create_offer(self.listing_id, self.user_id)

   
        resp = self.client.patch(f"/offers/{offer_id}/seen")
        self.assertEqual(resp.status_code, 200)

       
        self.app.dependency_overrides[get_current_user_id] = lambda: self.other_user_id

        resp = self.client.post(f"/offers/{offer_id}/resolve?accepted=true")
        self.assertEqual(resp.status_code, 200)

        self.app.dependency_overrides[get_current_user_id] = lambda: self.user_id

        new_listing_id = self._create_listing(self.other_user_id)

        offer_id2 = self._create_offer(new_listing_id, self.user_id)

        resp = self.client.delete(f"/offers/{offer_id2}")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("deleted", resp.json())