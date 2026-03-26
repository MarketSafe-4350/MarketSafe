from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from src.business_logic.services.offer_service import OfferService
from src.utils import OfferNotFoundError, ListingNotFoundError, UnapprovedBehaviorError


def _make_offer(offer_id=1, listing_id=10, sender_id=5, accepted=None):
    return SimpleNamespace(
        id=offer_id,
        listing_id=listing_id,
        sender_id=sender_id,
        accepted=accepted,
        is_pending=(accepted is None),
    )


def _make_listing(listing_id=10, seller_id=99, is_sold=False):
    return SimpleNamespace(id=listing_id, seller_id=seller_id, is_sold=is_sold)


def _make_account(account_id=99):
    return SimpleNamespace(id=account_id)


class TestOfferServiceUnit(unittest.TestCase):

    def setUp(self) -> None:
        self.offer_manager = MagicMock()
        self.listing_manager = MagicMock()
        self.account_manager = MagicMock()

        self.service = OfferService(
            offer_manager=self.offer_manager,
            listing_manager=self.listing_manager,
            account_manager=self.account_manager,
        )

    # --------------------------------------------------
    # Delegation — simple pass-throughs
    # --------------------------------------------------

    def test_create_offer_delegates_to_manager(self) -> None:
        offer = _make_offer()
        self.offer_manager.create_offer.return_value = offer

        out = self.service.create_offer(offer)

        self.assertIs(offer, out)
        self.offer_manager.create_offer.assert_called_once_with(offer)

    def test_get_offer_by_id_delegates_to_manager(self) -> None:
        offer = _make_offer()
        self.offer_manager.get_offer_by_id.return_value = offer

        out = self.service.get_offer_by_id(1)

        self.assertIs(offer, out)
        self.offer_manager.get_offer_by_id.assert_called_once_with(1)

    def test_get_offers_by_listing_id_delegates_to_manager(self) -> None:
        offers = [_make_offer(1), _make_offer(2)]
        self.offer_manager.get_offers_by_listing_id.return_value = offers

        out = self.service.get_offers_by_listing_id(10)

        self.assertEqual(offers, out)
        self.offer_manager.get_offers_by_listing_id.assert_called_once_with(10)

    def test_get_offers_by_sender_id_delegates_to_manager(self) -> None:
        offers = [_make_offer(1)]
        self.offer_manager.get_offers_by_sender_id.return_value = offers

        out = self.service.get_offers_by_sender_id(5)

        self.assertEqual(offers, out)
        self.offer_manager.get_offers_by_sender_id.assert_called_once_with(5)

    def test_get_offers_sellers_delegates_to_manager(self) -> None:
        offers = [_make_offer(1), _make_offer(2)]
        self.offer_manager.get_offers_sellers.return_value = offers

        out = self.service.get_offers_sellers(99)

        self.assertEqual(offers, out)
        self.offer_manager.get_offers_sellers.assert_called_once_with(99)

    def test_get_offer_sellers_pending_delegates_to_manager(self) -> None:
        offers = [_make_offer(1)]
        self.offer_manager.get_offer_sellers_pending.return_value = offers

        out = self.service.get_offer_sellers_pending(99)

        self.assertEqual(offers, out)
        self.offer_manager.get_offer_sellers_pending.assert_called_once_with(99)

    def test_get_offer_sellers_unseen_delegates_to_manager(self) -> None:
        offers = [_make_offer(1)]
        self.offer_manager.get_offer_sellers_unseen.return_value = offers

        out = self.service.get_offer_sellers_unseen(99)

        self.assertEqual(offers, out)
        self.offer_manager.get_offer_sellers_unseen.assert_called_once_with(99)

    def test_get_pending_offers_with_listing_by_sender_delegates(self) -> None:
        offers = [_make_offer(1)]
        self.offer_manager.get_pending_offers_with_listing_by_sender.return_value = offers

        out = self.service.get_pending_offers_with_listing_by_sender(5)

        self.assertEqual(offers, out)
        self.offer_manager.get_pending_offers_with_listing_by_sender.assert_called_once_with(5)

    def test_set_offer_seen_delegates_to_manager(self) -> None:
        self.service.set_offer_seen(1)

        self.offer_manager.set_offer_seen.assert_called_once_with(1)

    def test_delete_offer_delegates_to_manager(self) -> None:
        self.offer_manager.delete_offer.return_value = True

        out = self.service.delete_offer(1)

        self.assertTrue(out)
        self.offer_manager.delete_offer.assert_called_once_with(1)

    # --------------------------------------------------
    # resolve_offer — decline
    # --------------------------------------------------

    def test_resolve_offer_decline_calls_manager_and_skips_mark_sold(self) -> None:
        offer = _make_offer(offer_id=1, listing_id=10, sender_id=5)
        self.offer_manager.get_offer_by_id.return_value = offer

        self.service.resolve_offer(offer_id=1, accepted=False, actor_id=99)

        self.offer_manager.set_offer_accepted.assert_called_once_with(1, False, 99)
        self.listing_manager.mark_listing_sold.assert_not_called()
        self.account_manager.get_account_by_id.assert_not_called()

    # --------------------------------------------------
    # resolve_offer — accept (happy path)
    # --------------------------------------------------

    def test_resolve_offer_accept_calls_mark_listing_sold(self) -> None:
        offer = _make_offer(offer_id=1, listing_id=10, sender_id=5)
        actor = _make_account(account_id=99)
        buyer = _make_account(account_id=5)
        listing = _make_listing(listing_id=10, seller_id=99)

        self.offer_manager.get_offer_by_id.return_value = offer
        self.listing_manager.get_listing_by_id.return_value = listing
        self.account_manager.get_account_by_id.side_effect = lambda account_id: (
            actor if account_id == 99 else buyer
        )

        self.service.resolve_offer(offer_id=1, accepted=True, actor_id=99)

        self.offer_manager.set_offer_accepted.assert_called_once_with(1, True, 99)
        self.listing_manager.mark_listing_sold.assert_called_once_with(actor, listing, buyer)

    def test_resolve_offer_accept_fetches_correct_actor_and_buyer(self) -> None:
        offer = _make_offer(offer_id=1, listing_id=10, sender_id=5)
        actor = _make_account(account_id=99)
        buyer = _make_account(account_id=5)
        listing = _make_listing(listing_id=10, seller_id=99)

        self.offer_manager.get_offer_by_id.return_value = offer
        self.listing_manager.get_listing_by_id.return_value = listing
        self.account_manager.get_account_by_id.side_effect = lambda account_id: (
            actor if account_id == 99 else buyer
        )

        self.service.resolve_offer(offer_id=1, accepted=True, actor_id=99)

        # Actor fetched with seller id, buyer fetched with offer sender id
        calls = [c.kwargs["account_id"] if c.kwargs else c.args[0]
                 for c in self.account_manager.get_account_by_id.call_args_list]
        self.assertIn(99, calls)
        self.assertIn(5, calls)

    # --------------------------------------------------
    # resolve_offer — error paths
    # --------------------------------------------------

    def test_resolve_offer_raises_offer_not_found_when_offer_missing(self) -> None:
        self.offer_manager.get_offer_by_id.return_value = None

        with self.assertRaises(OfferNotFoundError):
            self.service.resolve_offer(offer_id=99, accepted=True, actor_id=1)

        self.offer_manager.set_offer_accepted.assert_not_called()
        self.listing_manager.mark_listing_sold.assert_not_called()

    def test_resolve_offer_raises_listing_not_found_when_listing_missing(self) -> None:
        offer = _make_offer(offer_id=1, listing_id=10, sender_id=5)
        self.offer_manager.get_offer_by_id.return_value = offer
        self.listing_manager.get_listing_by_id.return_value = None

        with self.assertRaises(ListingNotFoundError):
            self.service.resolve_offer(offer_id=1, accepted=True, actor_id=99)

        self.listing_manager.mark_listing_sold.assert_not_called()

    def test_resolve_offer_raises_when_buyer_account_not_found(self) -> None:
        offer = _make_offer(offer_id=1, listing_id=10, sender_id=5)
        actor = _make_account(account_id=99)
        listing = _make_listing(listing_id=10, seller_id=99)

        self.offer_manager.get_offer_by_id.return_value = offer
        self.listing_manager.get_listing_by_id.return_value = listing
        self.account_manager.get_account_by_id.side_effect = lambda account_id: (
            actor if account_id == 99 else None
        )

        with self.assertRaises(UnapprovedBehaviorError):
            self.service.resolve_offer(offer_id=1, accepted=True, actor_id=99)

        self.listing_manager.mark_listing_sold.assert_not_called()

    def test_resolve_offer_propagates_error_from_set_offer_accepted(self) -> None:
        offer = _make_offer(offer_id=1)
        self.offer_manager.get_offer_by_id.return_value = offer
        self.offer_manager.set_offer_accepted.side_effect = UnapprovedBehaviorError(
            message="Not the seller."
        )

        with self.assertRaises(UnapprovedBehaviorError):
            self.service.resolve_offer(offer_id=1, accepted=True, actor_id=55)

        self.listing_manager.mark_listing_sold.assert_not_called()
