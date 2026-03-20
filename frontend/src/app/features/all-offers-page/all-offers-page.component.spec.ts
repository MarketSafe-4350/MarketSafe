import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { RouterTestingModule } from '@angular/router/testing';
import { of, throwError } from 'rxjs';

import { AllOffersPageComponent } from './all-offers-page.component';
import { AccountsApiService } from '../../shared/services/accounts-api.service';
import { ListingsApiService } from '../../shared/services/listings-api.service';
import { Offer, OffersApiService } from '../../shared/services/offers-api.service';
import { Listing } from '../../shared/models/listing.models';

describe('AllOffersPageComponent', () => {
  let fixture: ComponentFixture<AllOffersPageComponent>;
  let component: AllOffersPageComponent;
  let accountsApiSpy: jasmine.SpyObj<AccountsApiService>;
  let listingsApiSpy: jasmine.SpyObj<ListingsApiService>;
  let offersApiSpy: jasmine.SpyObj<OffersApiService>;

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

  beforeEach(async () => {
    localStorage.clear();
    const payload = btoa(JSON.stringify({ sub: '10' }));
    localStorage.setItem('access_token', `x.${payload}.y`);

    accountsApiSpy = jasmine.createSpyObj<AccountsApiService>(
      'AccountsApiService',
      ['getMe'],
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

    listingsApiSpy = jasmine.createSpyObj<ListingsApiService>(
      'ListingsApiService',
      ['getMine', 'create', 'delete'],
    );
    listingsApiSpy.getMine.and.returnValue(of([listing]));

    offersApiSpy = jasmine.createSpyObj<OffersApiService>(
      'OffersApiService',
      ['getReceived', 'getReceivedUnseen', 'markSeen', 'resolve'],
    );
    offersApiSpy.getReceived.and.returnValue(of([pendingOffer]));
    offersApiSpy.getReceivedUnseen.and.returnValue(of([pendingOffer]));
    offersApiSpy.markSeen.and.returnValue(of({}));
    offersApiSpy.resolve.and.returnValue(of({}));

    await TestBed.configureTestingModule({
      imports: [AllOffersPageComponent, RouterTestingModule],
      providers: [
        provideNoopAnimations(),
        { provide: AccountsApiService, useValue: accountsApiSpy },
        { provide: ListingsApiService, useValue: listingsApiSpy },
        { provide: OffersApiService, useValue: offersApiSpy },
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
    expect(offersApiSpy.markSeen).toHaveBeenCalledWith(pendingOffer.id);
    expect(component.offers[0].listingTitle).toBe('Desk Lamp');
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
});
