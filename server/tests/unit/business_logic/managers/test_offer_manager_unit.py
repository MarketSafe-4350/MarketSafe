from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, call

from src.business_logic.managers.offer.offer_manager import OfferManager
from src.domain_models.offer import Offer
from src.utils import (
    ValidationError,
    ConflictError,
    UnapprovedBehaviorError,
    ListingNotFoundError,
    OfferNotFoundError,
)


def _make_offer(
    offer_id=1,
    listing_id=10,
    sender_id=5,
    offered_price=100.0,
    accepted=None,
    seen=False,
):
    """Return a simple namespace that mimics an Offer domain object."""
    o = SimpleNamespace(
        id=offer_id,
        listing_id=listing_id,
        sender_id=sender_id,
        offered_price=offered_price,
        accepted=accepted,
        seen=seen,
        is_pending=(accepted is None),
    )
    return o


def _make_listing(listing_id=10, seller_id=99, is_sold=False):
    """Return a simple namespace that mimics a Listing domain object."""
    return SimpleNamespace(id=listing_id, seller_id=seller_id, is_sold=is_sold)


class TestOfferManagerUnit(unittest.TestCase):

    def setUp(self) -> None:
        self.offer_db = MagicMock()
        self.listing_db = MagicMock()
        self.manager = OfferManager(self.offer_db, self.listing_db)

    # --------------------------------------------------
    # CREATE
    # --------------------------------------------------

    def test_create_offer_returns_created_offer(self) -> None:
        offer = Offer(listing_id=10, sender_id=5, offered_price=100.0)
        created = _make_offer(offer_id=1)
        listing = _make_listing(listing_id=10, seller_id=99)

        self.listing_db.get_by_id.return_value = listing
        self.offer_db.get_by_sender_and_listing.return_value = None
        self.offer_db.add.return_value = created

        out = self.manager.create_offer(offer)

        self.assertIs(created, out)
        self.offer_db.add.assert_called_once_with(offer)

    def test_create_offer_raises_validation_error_when_offer_is_none(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.create_offer(None)  # type: ignore[arg-type]

    def test_create_offer_raises_listing_not_found_when_listing_missing(self) -> None:
        offer = Offer(listing_id=10, sender_id=5, offered_price=100.0)
        self.listing_db.get_by_id.return_value = None

        with self.assertRaises(ListingNotFoundError):
            self.manager.create_offer(offer)

        self.offer_db.add.assert_not_called()

    def test_create_offer_raises_when_listing_is_sold(self) -> None:
        offer = Offer(listing_id=10, sender_id=5, offered_price=100.0)
        self.listing_db.get_by_id.return_value = _make_listing(is_sold=True)

        with self.assertRaises(UnapprovedBehaviorError):
            self.manager.create_offer(offer)

        self.offer_db.add.assert_not_called()

    def test_create_offer_raises_when_sender_is_seller(self) -> None:
        offer = Offer(listing_id=10, sender_id=99, offered_price=100.0)
        self.listing_db.get_by_id.return_value = _make_listing(seller_id=99)

        with self.assertRaises(UnapprovedBehaviorError):
            self.manager.create_offer(offer)

        self.offer_db.add.assert_not_called()

    def test_create_offer_raises_conflict_when_pending_offer_exists(self) -> None:
        offer = Offer(listing_id=10, sender_id=5, offered_price=100.0)
        self.listing_db.get_by_id.return_value = _make_listing(seller_id=99)
        self.offer_db.get_by_sender_and_listing.return_value = _make_offer(accepted=None)

        with self.assertRaises(ConflictError):
            self.manager.create_offer(offer)

        self.offer_db.add.assert_not_called()

    def test_create_offer_raises_when_accepted_offer_exists(self) -> None:
        offer = Offer(listing_id=10, sender_id=5, offered_price=100.0)
        self.listing_db.get_by_id.return_value = _make_listing(seller_id=99)
        self.offer_db.get_by_sender_and_listing.return_value = _make_offer(accepted=True)

        with self.assertRaises(UnapprovedBehaviorError):
            self.manager.create_offer(offer)

        self.offer_db.add.assert_not_called()

    def test_create_offer_allows_resubmission_after_rejection(self) -> None:
        offer = Offer(listing_id=10, sender_id=5, offered_price=120.0)
        created = _make_offer(offer_id=2)
        self.listing_db.get_by_id.return_value = _make_listing(seller_id=99)
        self.offer_db.get_by_sender_and_listing.return_value = _make_offer(accepted=False)
        self.offer_db.add.return_value = created

        out = self.manager.create_offer(offer)

        self.assertIs(created, out)
        self.offer_db.add.assert_called_once_with(offer)

    # --------------------------------------------------
    # READ (simple)
    # --------------------------------------------------

    def test_get_offer_by_id_returns_offer(self) -> None:
        offer = _make_offer(offer_id=1)
        self.offer_db.get_by_id.return_value = offer

        out = self.manager.get_offer_by_id(1)

        self.assertIs(offer, out)
        self.offer_db.get_by_id.assert_called_once_with(1)

    def test_get_offer_by_id_returns_none_when_not_found(self) -> None:
        self.offer_db.get_by_id.return_value = None

        out = self.manager.get_offer_by_id(99)

        self.assertIsNone(out)

    def test_get_offer_by_id_raises_validation_error_when_id_is_none(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.get_offer_by_id(None)  # type: ignore[arg-type]

    def test_get_all_offers_returns_all(self) -> None:
        offers = [_make_offer(1), _make_offer(2)]
        self.offer_db.get_all.return_value = offers

        out = self.manager.get_all_offers()

        self.assertEqual(offers, out)
        self.offer_db.get_all.assert_called_once_with()

    def test_get_offers_by_listing_id_delegates(self) -> None:
        offers = [_make_offer(1), _make_offer(2)]
        self.offer_db.get_by_listing_id.return_value = offers

        out = self.manager.get_offers_by_listing_id(10)

        self.assertEqual(offers, out)
        self.offer_db.get_by_listing_id.assert_called_once_with(10)

    def test_get_offers_by_listing_id_raises_validation_error_when_id_invalid(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.get_offers_by_listing_id(None)  # type: ignore[arg-type]

    def test_get_offers_by_sender_id_delegates(self) -> None:
        offers = [_make_offer(1), _make_offer(2)]
        self.offer_db.get_by_sender_id.return_value = offers

        out = self.manager.get_offers_by_sender_id(5)

        self.assertEqual(offers, out)
        self.offer_db.get_by_sender_id.assert_called_once_with(5)

    def test_get_offers_by_sender_id_raises_validation_error_when_id_invalid(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.get_offers_by_sender_id(None)  # type: ignore[arg-type]

    def test_get_accepted_offers_by_listing_id_delegates(self) -> None:
        offers = [_make_offer(accepted=True)]
        self.offer_db.get_accepted_by_listing_id.return_value = offers

        out = self.manager.get_accepted_offers_by_listing_id(10)

        self.assertEqual(offers, out)
        self.offer_db.get_accepted_by_listing_id.assert_called_once_with(10)

    def test_get_accepted_offers_by_listing_id_raises_validation_error_when_id_invalid(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.get_accepted_offers_by_listing_id(None)  # type: ignore[arg-type]

    def test_get_unseen_offers_by_listing_id_delegates(self) -> None:
        offers = [_make_offer(seen=False)]
        self.offer_db.get_unseen_by_listing_id.return_value = offers

        out = self.manager.get_unseen_offers_by_listing_id(10)

        self.assertEqual(offers, out)
        self.offer_db.get_unseen_by_listing_id.assert_called_once_with(10)

    def test_get_unseen_offers_by_listing_id_raises_validation_error_when_id_invalid(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.get_unseen_offers_by_listing_id(None)  # type: ignore[arg-type]

    def test_get_pending_offers_by_listing_id_delegates(self) -> None:
        offers = [_make_offer(accepted=None)]
        self.offer_db.get_pending_by_listing_id.return_value = offers

        out = self.manager.get_pending_offers_by_listing_id(10)

        self.assertEqual(offers, out)
        self.offer_db.get_pending_by_listing_id.assert_called_once_with(10)

    def test_get_pending_offers_by_listing_id_raises_validation_error_when_id_invalid(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.get_pending_offers_by_listing_id(None)  # type: ignore[arg-type]

    def test_get_offer_by_sender_and_listing_delegates(self) -> None:
        offer = _make_offer()
        self.offer_db.get_by_sender_and_listing.return_value = offer

        out = self.manager.get_offer_by_sender_and_listing(5, 10)

        self.assertIs(offer, out)
        self.offer_db.get_by_sender_and_listing.assert_called_once_with(5, 10)

    def test_get_offer_by_sender_and_listing_raises_when_sender_id_invalid(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.get_offer_by_sender_and_listing(None, 10)  # type: ignore[arg-type]

    def test_get_offer_by_sender_and_listing_raises_when_listing_id_invalid(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.get_offer_by_sender_and_listing(5, None)  # type: ignore[arg-type]

    # --------------------------------------------------
    # READ (aggregated)
    # --------------------------------------------------

    def test_get_offers_sellers_returns_flat_list_across_all_listings(self) -> None:
        l1 = _make_listing(listing_id=10)
        l2 = _make_listing(listing_id=11)
        o1 = _make_offer(offer_id=1, listing_id=10)
        o2 = _make_offer(offer_id=2, listing_id=11)
        o3 = _make_offer(offer_id=3, listing_id=11)

        self.listing_db.get_by_seller_id.return_value = [l1, l2]
        self.offer_db.get_by_listing_id.side_effect = [[o1], [o2, o3]]

        out = self.manager.get_offers_sellers(99)

        self.assertEqual([o1, o2, o3], out)
        self.listing_db.get_by_seller_id.assert_called_once_with(99)

    def test_get_offers_sellers_returns_empty_when_no_listings(self) -> None:
        self.listing_db.get_by_seller_id.return_value = []

        out = self.manager.get_offers_sellers(99)

        self.assertEqual([], out)
        self.offer_db.get_by_listing_id.assert_not_called()

    def test_get_offers_sellers_raises_validation_error_when_seller_id_invalid(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.get_offers_sellers(None)  # type: ignore[arg-type]

    def test_get_offer_sellers_pending_returns_only_pending_offers(self) -> None:
        l1 = _make_listing(listing_id=10)
        o1 = _make_offer(offer_id=1, accepted=None)

        self.listing_db.get_by_seller_id.return_value = [l1]
        self.offer_db.get_pending_by_listing_id.return_value = [o1]

        out = self.manager.get_offer_sellers_pending(99)

        self.assertEqual([o1], out)
        self.offer_db.get_pending_by_listing_id.assert_called_once_with(10)

    def test_get_offer_sellers_pending_raises_validation_error_when_seller_id_invalid(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.get_offer_sellers_pending(None)  # type: ignore[arg-type]

    def test_get_offer_sellers_unseen_returns_only_unseen_offers(self) -> None:
        l1 = _make_listing(listing_id=10)
        o1 = _make_offer(offer_id=1, seen=False)

        self.listing_db.get_by_seller_id.return_value = [l1]
        self.offer_db.get_unseen_by_listing_id.return_value = [o1]

        out = self.manager.get_offer_sellers_unseen(99)

        self.assertEqual([o1], out)
        self.offer_db.get_unseen_by_listing_id.assert_called_once_with(10)

    def test_get_offer_sellers_unseen_raises_validation_error_when_seller_id_invalid(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.get_offer_sellers_unseen(None)  # type: ignore[arg-type]

    def test_get_pending_offers_with_listing_by_sender_filters_pending(self) -> None:
        pending = _make_offer(offer_id=1, accepted=None)
        accepted = _make_offer(offer_id=2, accepted=True)
        rejected = _make_offer(offer_id=3, accepted=False)

        self.offer_db.get_by_sender_id.return_value = [pending, accepted, rejected]

        out = self.manager.get_pending_offers_with_listing_by_sender(5)

        self.assertEqual([pending], out)
        self.offer_db.get_by_sender_id.assert_called_once_with(5)

    def test_get_pending_offers_with_listing_by_sender_returns_empty_when_none_pending(self) -> None:
        self.offer_db.get_by_sender_id.return_value = [
            _make_offer(accepted=True),
            _make_offer(accepted=False),
        ]

        out = self.manager.get_pending_offers_with_listing_by_sender(5)

        self.assertEqual([], out)

    def test_get_pending_offers_with_listing_by_sender_raises_when_sender_id_invalid(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.get_pending_offers_with_listing_by_sender(None)  # type: ignore[arg-type]

    # --------------------------------------------------
    # UPDATE
    # --------------------------------------------------

    def test_set_offer_seen_delegates_to_db(self) -> None:
        self.manager.set_offer_seen(1)

        self.offer_db.set_seen.assert_called_once_with(1)

    def test_set_offer_seen_raises_validation_error_when_id_invalid(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.set_offer_seen(None)  # type: ignore[arg-type]

    def test_set_offer_accepted_declines_offer(self) -> None:
        offer = _make_offer(offer_id=1, listing_id=10, sender_id=5, accepted=None)
        listing = _make_listing(listing_id=10, seller_id=99)

        self.offer_db.get_by_id.return_value = offer
        self.listing_db.get_by_id.return_value = listing

        self.manager.set_offer_accepted(1, False, 99)

        self.offer_db.set_accepted.assert_called_once_with(1, False)
        self.offer_db.get_pending_by_listing_id.assert_not_called()

    def test_set_offer_accepted_accepts_offer_and_rejects_others(self) -> None:
        offer = _make_offer(offer_id=1, listing_id=10, sender_id=5, accepted=None)
        other = _make_offer(offer_id=2, listing_id=10, sender_id=6, accepted=None)
        listing = _make_listing(listing_id=10, seller_id=99)

        self.offer_db.get_by_id.return_value = offer
        self.listing_db.get_by_id.return_value = listing
        self.offer_db.get_pending_by_listing_id.return_value = [offer, other]

        self.manager.set_offer_accepted(1, True, 99)

        self.offer_db.set_accepted.assert_any_call(1, True)
        self.offer_db.set_accepted.assert_any_call(2, False)
        # Accepted offer must not be rejected
        self.assertNotIn(call(1, False), self.offer_db.set_accepted.call_args_list)

    def test_set_offer_accepted_raises_offer_not_found(self) -> None:
        self.offer_db.get_by_id.return_value = None

        with self.assertRaises(OfferNotFoundError):
            self.manager.set_offer_accepted(1, True, 99)

    def test_set_offer_accepted_raises_listing_not_found(self) -> None:
        offer = _make_offer(offer_id=1, listing_id=10)
        self.offer_db.get_by_id.return_value = offer
        self.listing_db.get_by_id.return_value = None

        with self.assertRaises(ListingNotFoundError):
            self.manager.set_offer_accepted(1, True, 99)

    def test_set_offer_accepted_raises_when_actor_is_not_seller(self) -> None:
        offer = _make_offer(offer_id=1, listing_id=10)
        listing = _make_listing(listing_id=10, seller_id=99)
        self.offer_db.get_by_id.return_value = offer
        self.listing_db.get_by_id.return_value = listing

        with self.assertRaises(UnapprovedBehaviorError):
            self.manager.set_offer_accepted(1, True, actor_id=55)

    def test_set_offer_accepted_raises_when_offer_already_resolved(self) -> None:
        offer = _make_offer(offer_id=1, listing_id=10, accepted=True)
        listing = _make_listing(listing_id=10, seller_id=99)
        self.offer_db.get_by_id.return_value = offer
        self.listing_db.get_by_id.return_value = listing

        with self.assertRaises(UnapprovedBehaviorError):
            self.manager.set_offer_accepted(1, True, 99)

    def test_set_offer_accepted_raises_validation_error_when_offer_id_invalid(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.set_offer_accepted(None, True, 99)  # type: ignore[arg-type]

    def test_set_offer_accepted_raises_validation_error_when_actor_id_invalid(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.set_offer_accepted(1, True, None)  # type: ignore[arg-type]

    def test_set_offer_accepted_raises_validation_error_when_accepted_invalid(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.set_offer_accepted(1, None, 99)  # type: ignore[arg-type]

    # --------------------------------------------------
    # DELETE
    # --------------------------------------------------

    def test_delete_offer_returns_true_when_deleted(self) -> None:
        self.offer_db.remove.return_value = True

        out = self.manager.delete_offer(1)

        self.assertTrue(out)
        self.offer_db.remove.assert_called_once_with(1)

    def test_delete_offer_returns_false_when_not_found(self) -> None:
        self.offer_db.remove.return_value = False

        out = self.manager.delete_offer(1)

        self.assertFalse(out)

    def test_delete_offer_raises_validation_error_when_id_invalid(self) -> None:
        with self.assertRaises(ValidationError):
            self.manager.delete_offer(None)  # type: ignore[arg-type]
