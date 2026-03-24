import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { RouterTestingModule } from '@angular/router/testing';
import { of, throwError } from 'rxjs';

import { AllOffersPageComponent } from './all-offers-page.component';
import { AccountsApiService } from '../../shared/services/accounts-api.service';
import { ListingsApiService } from '../../shared/services/listings-api.service';
import { Offer, OffersApiService } from '../../shared/services/offers-api.service';
import { Listing } from '../../shared/models/listing.models';
import { RatingsApiService } from '../../shared/services/ratings-api.service';
import { BuyerOfferNotificationsService } from '../../shared/services/buyer-offer-notifications.service';

describe('AllOffersPageComponent', () => {
  let fixture: ComponentFixture<AllOffersPageComponent>;
  let component: AllOffersPageComponent;
  let accountsApiSpy: jasmine.SpyObj<AccountsApiService>;
  let listingsApiSpy: jasmine.SpyObj<ListingsApiService>;
  let offersApiSpy: jasmine.SpyObj<OffersApiService>;
  let ratingsApiSpy: jasmine.SpyObj<RatingsApiService>;
  let buyerOfferNotificationsSpy: jasmine.SpyObj<BuyerOfferNotificationsService>;

  const listing: Listing = {
    id: 5,
    sellerId: 10,
    title: 'Desk Lamp',
    description: 'Warm light',
    imageUrl: '',
    price: 20,
    location: 'Winnipeg',
    createdAt: new Date('2026-03-01').toISOString(),
    isSold: false,
  };

  const pendingOffer: Offer = {
    id: 11,
    listingId: 5,
    senderId: 88,
    offeredPrice: 18,
    locationOffered: 'Campus',
    seen: false,
    accepted: null,
    createdDate: new Date('2026-03-02').toISOString(),
  };

  const acceptedSentOffer: Offer = {
    id: 21,
    listingId: 5,
    senderId: 10,
    offeredPrice: 20,
    locationOffered: 'Campus',
    seen: true,
    accepted: true,
    createdDate: new Date('2026-03-03').toISOString(),
  };

  beforeEach(async () => {
    localStorage.clear();
    const payload = btoa(JSON.stringify({ sub: '10' }));
    localStorage.setItem('access_token', `x.${payload}.y`);

    accountsApiSpy = jasmine.createSpyObj<AccountsApiService>(
      'AccountsApiService',
      ['getMe', 'getById'],
    );
    accountsApiSpy.getMe.and.returnValue(
      of({
        id: 10,
        email: 'seller@example.com',
        fname: 'Seller',
        lname: 'User',
        verified: true,
      }),
    );
    accountsApiSpy.getById.and.returnValue(
      of({
        id: 88,
        email: 'buyer@example.com',
        fname: 'Jamie',
        lname: 'Buyer',
        verified: true,
      }),
    );

    listingsApiSpy = jasmine.createSpyObj<ListingsApiService>(
      'ListingsApiService',
      ['getMine', 'getAll', 'create', 'delete'],
    );
    listingsApiSpy.getMine.and.returnValue(of([listing]));
    listingsApiSpy.getAll.and.returnValue(of([listing]));

    offersApiSpy = jasmine.createSpyObj<OffersApiService>(
      'OffersApiService',
      ['getReceived', 'getReceivedUnseen', 'getSent', 'markSeen', 'resolve'],
    );
    ratingsApiSpy = jasmine.createSpyObj<RatingsApiService>(
      'RatingsApiService',
      ['create', 'getByListingId'],
    );
    buyerOfferNotificationsSpy = jasmine.createSpyObj<BuyerOfferNotificationsService>(
      'BuyerOfferNotificationsService',
      ['syncResolvedOffers', 'markResolvedOffersSeen'],
    );
    offersApiSpy.getReceived.and.returnValue(of([pendingOffer]));
    offersApiSpy.getReceivedUnseen.and.returnValue(of([pendingOffer]));
    offersApiSpy.getSent.and.returnValue(of([]));
    offersApiSpy.markSeen.and.returnValue(of({}));
    offersApiSpy.resolve.and.returnValue(of({}));
    ratingsApiSpy.create.and.returnValue(
      of({
        id: 1,
        listingId: acceptedSentOffer.listingId,
        raterId: 10,
        transactionRating: 5,
      }),
    );
    ratingsApiSpy.getByListingId.and.returnValue(of(null));
    buyerOfferNotificationsSpy.syncResolvedOffers.and.returnValue(new Set<number>());

    await TestBed.configureTestingModule({
      imports: [AllOffersPageComponent, RouterTestingModule],
      providers: [
        provideNoopAnimations(),
        { provide: AccountsApiService, useValue: accountsApiSpy },
        { provide: ListingsApiService, useValue: listingsApiSpy },
        { provide: OffersApiService, useValue: offersApiSpy },
        { provide: RatingsApiService, useValue: ratingsApiSpy },
        { provide: BuyerOfferNotificationsService, useValue: buyerOfferNotificationsSpy },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(AllOffersPageComponent);
    component = fixture.componentInstance;
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('ngOnInit_ShouldLoadOffersAndMarkUnseenAsSeen', () => {
    fixture.detectChanges();

    expect(listingsApiSpy.getMine).toHaveBeenCalled();
    expect(offersApiSpy.getReceived).toHaveBeenCalled();
    expect(offersApiSpy.getReceivedUnseen).toHaveBeenCalled();
    expect(accountsApiSpy.getById).toHaveBeenCalledWith(pendingOffer.senderId);
    expect(offersApiSpy.markSeen).toHaveBeenCalledWith(pendingOffer.id);
    expect(component.offers[0].listingTitle).toBe('Desk Lamp');
    expect(component.offers[0].buyerName).toBe('Jamie Buyer');
    expect(component.offers[0].seen).toBeTrue();
  });

  it('resolveOffer_Accepted_ShouldUpdateOfferStatus', () => {
    fixture.detectChanges();

    component.resolveOffer(pendingOffer.id, true);

    expect(offersApiSpy.resolve).toHaveBeenCalledWith(pendingOffer.id, true);
    expect(component.offers[0].accepted).toBeTrue();
    expect(component.canResolveOffer(component.offers[0])).toBeFalse();
  });

  it('resolveOffer_Error_ShouldSetErrorMessage', () => {
    offersApiSpy.resolve.and.returnValue(
      throwError(() => new Error('resolve failed')),
    );
    fixture.detectChanges();

    component.resolveOffer(pendingOffer.id, false);

    expect(component.errorMessage).toBe('Failed to update offer status.');
  });

  it('ngOnInit_AcceptedSentOffer_ShouldLoadSellerNameForRatingFlow', () => {
    offersApiSpy.getReceived.and.returnValue(of([]));
    offersApiSpy.getReceivedUnseen.and.returnValue(of([]));
    offersApiSpy.getSent.and.returnValue(of([acceptedSentOffer]));
    accountsApiSpy.getById.and.returnValue(
      of({
        id: 10,
        email: 'seller@example.com',
        fname: 'Seller',
        lname: 'User',
        verified: true,
      }),
    );

    fixture = TestBed.createComponent(AllOffersPageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();

    expect(component.sentOffers.length).toBe(1);
    expect(component.sentOffers[0].sellerName).toBe('Seller User');
    expect(ratingsApiSpy.getByListingId).toHaveBeenCalledWith(acceptedSentOffer.listingId);
  });

  it('submitSellerRating_ShouldPersistRatingAndUpdateOfferState', () => {
    offersApiSpy.getReceived.and.returnValue(of([]));
    offersApiSpy.getReceivedUnseen.and.returnValue(of([]));
    offersApiSpy.getSent.and.returnValue(of([acceptedSentOffer]));
    accountsApiSpy.getById.and.returnValue(
      of({
        id: 10,
        email: 'seller@example.com',
        fname: 'Seller',
        lname: 'User',
        verified: true,
      }),
    );

    fixture = TestBed.createComponent(AllOffersPageComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();

    component.setPendingRating(acceptedSentOffer.id, 5);
    component.submitSellerRating(component.sentOffers[0]);

    expect(ratingsApiSpy.create).toHaveBeenCalledWith(acceptedSentOffer.listingId, 5);
    expect(component.sentOffers[0].hasRatedSeller).toBeTrue();
    expect(component.sentOffers[0].ratingMessage).toContain('You rated');
  });
});
