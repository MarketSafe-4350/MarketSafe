from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

import src.api.routes.offer_routes as offer_routes

from src.api.dependencies import get_offer_service
from src.auth.dependencies import get_current_user_id


class TestOfferRoutes(unittest.TestCase):
    def setUp(self) -> None:
        self.app = FastAPI()
        self.app.include_router(offer_routes.router)

        self.user_id = 555
        self.app.dependency_overrides[get_current_user_id] = lambda: self.user_id

        self.offer_service = MagicMock(name="offer_service")
        self.app.dependency_overrides[get_offer_service] = lambda: self.offer_service

        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self.app.dependency_overrides.clear()

    def _full_offer_response(self, **overrides):
        base = {
            "id": 1,
            "listing_id": 42,
            "sender_id": self.user_id,
            "offered_price": 99.99,
            "location_offered": "Here",
            "seen": False,
            "accepted": None,
            "created_date": None,
        }
        base.update(overrides)
        return base

    def test_create_offer_calls_service_and_returns_offer_response(self):
        created_offer = MagicMock()
        self.offer_service.create_offer.return_value = created_offer

        fake_response = self._full_offer_response()

        with patch.object(
            offer_routes.OfferResponse, "from_domain", return_value=fake_response
        ):
            resp = self.client.post(
                "/listings/42/offer",
                json={"offered_price": 99.99, "location_offered": "Here"},
            )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), fake_response)

        self.offer_service.create_offer.assert_called_once()
        created_arg = self.offer_service.create_offer.call_args[0][0]
        self.assertEqual(created_arg.listing_id, 42)
        self.assertEqual(created_arg.sender_id, self.user_id)

    def test_get_offer_by_id_calls_service_and_returns(self):
        self.offer_service.get_offer_by_id.return_value = MagicMock()

        fake_response = self._full_offer_response(id=7)

        with patch.object(
            offer_routes.OfferResponse, "from_domain", return_value=fake_response
        ):
            resp = self.client.get("/offers/7")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), fake_response)
        self.offer_service.get_offer_by_id.assert_called_once_with(7)

    def test_get_offers_by_listing_returns_list(self):
        self.offer_service.get_offers_by_listing_id.return_value = [MagicMock()]

        with patch.object(
            offer_routes.OfferResponse,
            "from_domain",
            return_value=self._full_offer_response(),
        ):
            resp = self.client.get("/listings/100/offer")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 1)
        self.offer_service.get_offers_by_listing_id.assert_called_once_with(100)

    def test_get_offers_sent_calls_service_and_returns_list(self):
        self.offer_service.get_offers_by_sender_id.return_value = [MagicMock()]

        with patch.object(
            offer_routes.OfferResponse,
            "from_domain",
            return_value=self._full_offer_response(),
        ):
            resp = self.client.get("/accounts/offers/sent")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 1)
        self.offer_service.get_offers_by_sender_id.assert_called_once_with(self.user_id)

    def test_get_offers_received_calls_service_and_returns_list(self):
        self.offer_service.get_offers_sellers.return_value = [MagicMock()]

        with patch.object(
            offer_routes.OfferResponse,
            "from_domain",
            return_value=self._full_offer_response(),
        ):
            resp = self.client.get("/accounts/offers/received")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 1)
        self.offer_service.get_offers_sellers.assert_called_once_with(self.user_id)

    def test_get_pending_received_offers_calls_service_and_returns_list(self):
        self.offer_service.get_offer_sellers_pending.return_value = [MagicMock()]

        with patch.object(
            offer_routes.OfferResponse,
            "from_domain",
            return_value=self._full_offer_response(),
        ):
            resp = self.client.get("/accounts/offers/received/pending")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 1)
        self.offer_service.get_offer_sellers_pending.assert_called_once_with(self.user_id)

    def test_get_unseen_received_offers_calls_service_and_returns_list(self):
        self.offer_service.get_offer_sellers_unseen.return_value = [MagicMock()]

        with patch.object(
            offer_routes.OfferResponse,
            "from_domain",
            return_value=self._full_offer_response(seen=False),
        ):
            resp = self.client.get("/accounts/offers/received/unseen")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 1)
        self.offer_service.get_offer_sellers_unseen.assert_called_once_with(self.user_id)

    def test_get_pending_sent_offers_calls_service_and_returns_list(self):
        self.offer_service.get_pending_offers_with_listing_by_sender.return_value = [
            MagicMock()
        ]

        with patch.object(
            offer_routes.OfferResponse,
            "from_domain",
            return_value=self._full_offer_response(),
        ):
            resp = self.client.get("/accounts/offers/sent/pending")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.json()), 1)
        self.offer_service.get_pending_offers_with_listing_by_sender.assert_called_once_with(
            self.user_id
        )

    def test_mark_offer_seen_calls_service_and_returns_message(self):
        resp = self.client.patch("/offers/55/seen")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"message": "Offer marked as seen"})
        self.offer_service.set_offer_seen.assert_called_once_with(55)

    def test_resolve_offer_calls_service_and_returns_message(self):
        resp = self.client.post("/offers/66/resolve?accepted=true")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"message": "Offer resolved"})
        self.offer_service.resolve_offer.assert_called_once_with(66, True, self.user_id)

    def test_delete_offer_calls_service_and_returns_deleted_flag(self):
        self.offer_service.delete_offer.return_value = True

        resp = self.client.delete("/offers/77")

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json(), {"deleted": True})
        self.offer_service.delete_offer.assert_called_once_with(77)


if __name__ == "__main__":
    unittest.main(verbosity=2)