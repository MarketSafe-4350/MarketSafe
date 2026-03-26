import { TestBed } from '@angular/core/testing';

import { BuyerOfferNotificationsService } from './buyer-offer-notifications.service';
import { Offer } from './offers-api.service';

describe('BuyerOfferNotificationsService', () => {
  let service: BuyerOfferNotificationsService;

  const acceptedOffer: Offer = {
    id: 10,
    listingId: 5,
    senderId: 100,
    offeredPrice: 75,
    locationOffered: 'Campus',
    seen: true,
    accepted: true,
    createdDate: '2026-03-24T12:00:00Z',
  };

  beforeEach(() => {
    localStorage.clear();
    TestBed.configureTestingModule({
      providers: [BuyerOfferNotificationsService],
    });

    service = TestBed.inject(BuyerOfferNotificationsService);
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('syncResolvedOffers_ShouldShowExistingResolvedOffersAsUnreadOnFirstLoad', () => {
    const unreadIds = service.syncResolvedOffers([acceptedOffer], 7);

    expect([...unreadIds]).toEqual([acceptedOffer.id]);
  });

  it('syncResolvedOffers_ShouldMarkStatusChangesUnreadForThatUserOnly', () => {
    service.syncResolvedOffers([{ ...acceptedOffer, accepted: null }], 7);
    const unreadIds = service.syncResolvedOffers([acceptedOffer], 7);

    expect([...unreadIds]).toEqual([acceptedOffer.id]);
    expect(
      [...service.syncResolvedOffers([acceptedOffer], 8)],
    ).toEqual([acceptedOffer.id]);
  });

  it('markResolvedOffersSeen_ShouldClearUnreadIdsForScopedUser', () => {
    service.syncResolvedOffers([{ ...acceptedOffer, accepted: null }], 7);
    service.syncResolvedOffers([acceptedOffer], 7);

    service.markResolvedOffersSeen([acceptedOffer.id], 7);

    expect([...service.getUnseenResolvedOfferIds([acceptedOffer], 7)]).toEqual([]);
  });
});
